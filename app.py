from flask import Flask, request, jsonify, render_template, redirect, url_for, session, send_from_directory
from flask_cors import CORS
import whisper
import json
import sqlite3
import os
import base64
import time
from datetime import datetime
from huggingface_hub import InferenceClient
from typing import Dict, Any

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-this-in-production-1234567890'
CORS(app)

# ─── Configuration ──────────────────────────────────────────────────────────────
class Config:
    HF_TOKEN = "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"
    MODEL = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH = r"database/database_two.db"           # ← make sure folder exists
    MAX_RESPONSE_TOKENS = 1000
    TEMPERATURE = 0.1
    EXTRACTION_TEMPERATURE = 0.05

client = InferenceClient(api_key=Config.HF_TOKEN)
whisper_model = None

# ─── Database Helpers ───────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
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

    # Connections table – user-specific
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

        # Transcribe
        model = load_whisper_model()
        result = model.transcribe(temp_file, fp16=False)
        raw_text = result["text"].strip()

        os.remove(temp_file)

        if not raw_text:
            return jsonify({'error': 'No speech detected'}), 400

        # Extract & analyze
        structured = extract_structured_data(raw_text)
        if not structured:
            return jsonify({'error': 'Could not extract data'}), 500

        analysis = generate_ai_analysis(structured)
        structured.update(analysis)

        # Save to current user
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

# ─── Startup ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)