from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import whisper
import json
import sqlite3
import os
import base64
import time
import re
import logging
from datetime import datetime
from huggingface_hub import InferenceClient
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from contextlib import contextmanager

# Import the Enterprise AI search module v2
from ai_search import create_search_engine, Connection as SearchConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-this-in-production-1234567890'
CORS(app)

# ─── Configuration ──────────────────────────────────────────────────────────────
class Config:
    HF_TOKEN = "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"
    MODEL = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH = r"database/database_two.db"
    MAX_RESPONSE_TOKENS = 1000
    TEMPERATURE = 0.1
    EXTRACTION_TEMPERATURE = 0.05

client = InferenceClient(api_key=Config.HF_TOKEN)
whisper_model = None

# ─── Initialize Search Engine ───────────────────────────────────────────────────
search_engine = create_search_engine(
    api_key=Config.HF_TOKEN,
    MODEL=Config.MODEL
)

# ─── Data Models ────────────────────────────────────────────────────────────────
@dataclass
class Connection:
    id: Optional[int]
    user_id: Optional[int]
    full_name: str
    contact_info: Optional[str]
    job_title: Optional[str]
    company: Optional[str]
    industry: Optional[str]
    sector: Optional[str]
    skills_experience: Optional[str]
    ai_summary: Optional[str]
    ai_rating: int
    rating_momentum: Optional[str]
    key_accomplishments: Optional[str]
    relationship_status: Optional[str]
    days_since_contact: int
    mutual_connections: Optional[str]
    personal_notes: Optional[str]

    @classmethod
    def from_dict(cls, data: Dict) -> 'Connection':
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            full_name=data.get('full_name', ''),
            contact_info=data.get('contact_info'),
            job_title=data.get('job_title'),
            company=data.get('company'),
            industry=data.get('industry'),
            sector=data.get('sector'),
            skills_experience=data.get('skills_experience'),
            ai_summary=data.get('ai_summary'),
            ai_rating=data.get('ai_rating', 5),
            rating_momentum=data.get('rating_momentum'),
            key_accomplishments=data.get('key_accomplishments'),
            relationship_status=data.get('relationship_status'),
            days_since_contact=data.get('days_since_contact', 0),
            mutual_connections=data.get('mutual_connections'),
            personal_notes=data.get('personal_notes')
        )

# ─── Database Helpers ───────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        company TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT,
        contact_info TEXT,
        job_title TEXT,
        company TEXT,
        industry TEXT,
        sector TEXT,
        skills_experience TEXT,
        key_accomplishments TEXT,
        relationship_status TEXT DEFAULT 'Professional',
        days_since_contact INTEGER DEFAULT 0,
        mutual_connections TEXT,
        personal_notes TEXT,
        ai_summary TEXT,
        ai_rating INTEGER DEFAULT 5,
        rating_momentum TEXT DEFAULT 'Stagnant',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

# ─── Auth Helpers ───────────────────────────────────────────────────────────────
def get_current_user_id():
    return session.get('user_id')

def is_logged_in():
    return 'user_id' in session

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ─── Helper: Convert Connection to SearchConnection ────────────────────────────
def connection_to_search_connection(conn: Connection) -> SearchConnection:
    """Convert app Connection to ai_search.Connection"""
    return SearchConnection.from_dict({
        'id': conn.id,
        'user_id': conn.user_id,
        'full_name': conn.full_name,
        'contact_info': conn.contact_info,
        'job_title': conn.job_title,
        'company': conn.company,
        'industry': conn.industry,
        'sector': conn.sector,
        'skills_experience': conn.skills_experience,
        'key_accomplishments': conn.key_accomplishments,
        'relationship_status': conn.relationship_status,
        'days_since_contact': conn.days_since_contact,
        'mutual_connections': conn.mutual_connections,
        'personal_notes': conn.personal_notes,
        'ai_summary': conn.ai_summary,
        'ai_rating': conn.ai_rating,
        'rating_momentum': conn.rating_momentum
    })

# ─── Whisper & AI Helpers ───────────────────────────────────────────────────────
def load_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper base model...")
        whisper_model = whisper.load_model("base")
    return whisper_model

def validate_and_clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    schema = {
        'full_name': (str, ""),
        'contact_info': (str, ""),
        'job_title': (str, ""),
        'company': (str, ""),
        'industry': (str, ""),
        'sector': (str, ""),
        'skills_experience': (str, ""),
        'key_accomplishments': (str, ""),
        'relationship_status': (str, "Professional"),
        'days_since_contact': (int, 0),
        'mutual_connections': (str, ""),
        'personal_notes': (str, "")
    }

    cleaned = {}
    for key, (typ, default) in schema.items():
        val = data.get(key)
        if val in (None, "null", ""):
            cleaned[key] = default
            continue
        if isinstance(val, list):
            cleaned[key] = ", ".join(str(v) for v in val if v)
            continue
        try:
            cleaned[key] = int(val) if typ == int else str(val).strip()
        except:
            cleaned[key] = default
    return cleaned

def extract_structured_data(raw_text: str) -> Dict | None:
    print(f"Extracting from: {raw_text[:80]}...")

    prompt = f"""You are a professional data extraction assistant.
Extract networking / contact information from the following spoken text.
Return **only** valid JSON. Use null for missing fields. Do not add explanations.

TRANSCRIBED TEXT:
"{raw_text}"

Fields to extract (exact keys):
{{
  "full_name": str,
  "contact_info": str,
  "job_title": str,
  "company": str,
  "industry": str,
  "sector": str,
  "skills_experience": str,
  "key_accomplishments": str,
  "relationship_status": str,
  "days_since_contact": int,
  "mutual_connections": str,
  "personal_notes": str
}}

Rules:
- Only extract what is explicitly said
- Do not guess or infer
- relationship_status: one of "New Contact", "Professional", "Close Colleague", "Strategic Partner", etc.
- Return pure JSON only
"""

    try:
        resp = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=Config.MAX_RESPONSE_TOKENS,
            temperature=Config.EXTRACTION_TEMPERATURE
        )
        content = resp.choices[0].message.content.strip()

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        data = json.loads(content)
        return validate_and_clean_data(data)

    except Exception as e:
        print(f"Extraction failed: {e}")
        return None

def generate_ai_analysis(data: Dict) -> Dict:
    prompt = f"""You are a strategic business network analyst.
Rate this contact on a 1-10 scale based only on the provided data.
Be honest — use the full range.

Data:
- Name: {data.get('full_name', 'N/A')}
- Title: {data.get('job_title', 'N/A')} @ {data.get('company', 'N/A')}
- Industry: {data.get('industry', 'N/A')} / {data.get('sector', 'N/A')}
- Skills: {data.get('skills_experience', 'N/A')}
- Accomplishments: {data.get('key_accomplishments', 'N/A')}
- Notes: {data.get('personal_notes', 'N/A')}

Return only JSON:
{{
  "ai_summary": "Two sentence summary of value",
  "ai_rating": int,
  "rating_momentum": "Stagnant"
}}
"""

    try:
        resp = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        content = resp.choices[0].message.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        analysis = json.loads(content)

        rating = analysis.get('ai_rating', 5)
        if not isinstance(rating, int) or rating < 1 or rating > 10:
            analysis['ai_rating'] = 5

        analysis['rating_momentum'] = "Stagnant"
        return analysis

    except Exception as e:
        print(f"Analysis failed: {e}")
        return {
            "ai_summary": "Could not generate summary.",
            "ai_rating": 5,
            "rating_momentum": "Stagnant"
        }

def save_connection(user_id: int, data: Dict):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO connections (
            user_id, full_name, contact_info, job_title, company, industry, sector,
            skills_experience, key_accomplishments, relationship_status,
            days_since_contact, mutual_connections, personal_notes,
            ai_summary, ai_rating, rating_momentum
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data.get('full_name'),
            data.get('contact_info'),
            data.get('job_title'),
            data.get('company'),
            data.get('industry'),
            data.get('sector'),
            data.get('skills_experience'),
            data.get('key_accomplishments'),
            data.get('relationship_status'),
            data.get('days_since_contact'),
            data.get('mutual_connections'),
            data.get('personal_notes'),
            data.get('ai_summary'),
            data.get('ai_rating'),
            data.get('rating_momentum')
        ))
        conn.commit()
    finally:
        conn.close()

def get_user_connections(user_id: int) -> List[Connection]:
    """Get user connections as app Connection objects"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE user_id = ? ORDER BY ai_rating DESC, days_since_contact ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [Connection.from_dict(dict(row)) for row in rows]

# ─── Routes ─────────────────────────────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    members = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('index.html', members=members)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['email'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        company = request.form.get('company', '')

        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT INTO users (email, password, first_name, last_name, company)
            VALUES (?, ?, ?, ?, ?)
            ''', (email, password, first_name, last_name, company))
            user_id = cursor.lastrowid
            conn.commit()
            session['user_id'] = user_id
            session['email'] = email
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Email already exists")
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile/<person_id>')
@login_required
def profile_view(person_id):
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE id = ? AND user_id = ?", (person_id, user_id))
    person = cursor.fetchone()
    conn.close()
    
    if not person:
        return "Connection not found", 404
    
    return render_template('profile.html', person=dict(person))

@app.route('/update/<person_id>', methods=['POST'])
@login_required
def update_person(person_id):
    user_id = get_current_user_id()
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM connections WHERE id = ? AND user_id = ?", (person_id, user_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"status": "error", "message": "Not found"}), 404
        
        update_fields = []
        update_values = []
        
        for key, value in data.items():
            if key in ['full_name', 'contact_info', 'job_title', 'company', 'industry', 
                       'sector', 'skills_experience', 'key_accomplishments', 'relationship_status',
                       'mutual_connections', 'personal_notes', 'ai_summary', 'rating_momentum']:
                update_fields.append(f"{key} = ?")
                update_values.append(value)
            elif key in ['ai_rating', 'days_since_contact']:
                update_fields.append(f"{key} = ?")
                try:
                    clean_val = int(str(value).replace('/10', ''))
                    update_values.append(clean_val)
                except:
                    update_values.append(value)
        
        if update_fields:
            update_values.append(person_id)
            update_values.append(user_id)
            query = f"UPDATE connections SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?"
            cursor.execute(query, update_values)
            conn.commit()
        
        conn.close()
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Update error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/regenerate-summary/<person_id>', methods=['POST'])
@login_required
def regenerate_summary(person_id):
    user_id = get_current_user_id()
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM connections WHERE id = ? AND user_id = ?", (person_id, user_id))
        person = cursor.fetchone()
        
        if not person:
            conn.close()
            return jsonify({"status": "error"}), 404
        
        person_dict = dict(person)
        analysis = generate_ai_analysis(person_dict)
        new_summary = analysis.get('ai_summary', 'Could not generate summary.')
        
        cursor.execute("UPDATE connections SET ai_summary = ? WHERE id = ? AND user_id = ?", 
                      (new_summary, person_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "ai_summary": new_summary}), 200
        
    except Exception as e:
        print(f"Regenerate error: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/add', methods=['POST'])
@login_required
def add_connection():
    user_id = get_current_user_id()
    try:
        data = {
            'full_name': request.form.get('full_name', ''),
            'contact_info': request.form.get('contact_info', ''),
            'job_title': request.form.get('job_title', ''),
            'company': request.form.get('company', ''),
            'industry': request.form.get('industry', ''),
            'sector': request.form.get('sector', ''),
            'skills_experience': request.form.get('skills_experience', ''),
            'key_accomplishments': request.form.get('key_accomplishments', ''),
            'relationship_status': request.form.get('relationship_status', 'Professional'),
            'days_since_contact': int(request.form.get('days_since_contact', 0)),
            'mutual_connections': request.form.get('mutual_connections', ''),
            'personal_notes': request.form.get('personal_notes', ''),
            'ai_summary': request.form.get('ai_summary', ''),
            'ai_rating': int(request.form.get('ai_rating', 5)),
            'rating_momentum': request.form.get('rating_momentum', 'Stagnant')
        }
        
        save_connection(user_id, data)
        return redirect('/')
        
    except Exception as e:
        print(f"Add connection error: {e}")
        return str(e), 500

@app.route('/search', methods=['POST'])
@login_required
def search():
    """AI-powered network search with structured responses"""
    user_id = get_current_user_id()
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({"error": "Query too short. Please provide more detail."}), 400
        
        logger.info(f"AI Search for user {user_id}: {query}")
        
        # Get user's connections
        app_connections = get_user_connections(user_id)
        
        if not app_connections:
            return jsonify({
                "content": {
                    "title": "Empty Network",
                    "summary": "Your network is empty",
                    "body": "Add connections to get started with AI-powered insights.",
                    "insights": [],
                    "suggestions": ["Add your first connection to begin"]
                },
                "metadata": {"result_count": 0}
            }), 200
        
        # Convert to search connections
        search_connections = [
            connection_to_search_connection(conn) 
            for conn in app_connections
        ]
        
        # Execute search
        response = search_engine.search(
            query=query,
            connections=search_connections,
            user_id=user_id
        )
        
        logger.info(f"Search complete: intent={response.get('intent')}, "
                   f"results={response.get('metadata', {}).get('result_count', 0)}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        return jsonify({
            "content": {
                "title": "Error",
                "summary": "Unable to process query",
                "body": "An error occurred. Please try again.",
                "insights": [],
                "suggestions": ["Try rephrasing your query"]
            },
            "metadata": {"result_count": 0}
        }), 500

@app.route('/api/process-audio', methods=['POST'])
@login_required
def process_audio():
    try:
        payload = request.json
        audio_data_url = payload.get('audio')
        if not audio_data_url or not audio_data_url.startswith('data:audio/'):
            return jsonify({'error': 'Invalid audio data'}), 400

        header, encoded = audio_data_url.split(',', 1)
        mime = header.split(';')[0].replace('data:', '')
        audio_bytes = base64.b64decode(encoded)

        ext = mime.split('/')[-1] if '/' in mime else 'webm'
        temp_file = f"temp_{int(time.time()*1000)}.{ext}"
        with open(temp_file, 'wb') as f:
            f.write(audio_bytes)

        model = load_whisper_model()
        result = model.transcribe(temp_file, fp16=False)
        raw_text = result["text"].strip()

        os.remove(temp_file)

        if not raw_text:
            return jsonify({'error': 'No speech detected'}), 400

        structured = extract_structured_data(raw_text)
        if not structured:
            return jsonify({'error': 'Could not extract data'}), 500

        analysis = generate_ai_analysis(structured)
        structured.update(analysis)

        user_id = get_current_user_id()
        save_connection(user_id, structured)

        return jsonify({
            'success': True,
            'transcription': raw_text,
            'data': structured
        })

    except Exception as e:
        print(f"Audio processing error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections', methods=['GET'])
@login_required
def get_connections():
    user_id = get_current_user_id()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connections WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/api/search/stats', methods=['GET'])
@login_required
def search_stats():
    """Get search engine statistics"""
    try:
        stats = search_engine.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({"error": "Unable to retrieve stats"}), 500

if __name__ == '__main__':
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)