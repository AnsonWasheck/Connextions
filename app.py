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
from enum import Enum
from contextlib import contextmanager

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
    MAX_CANDIDATES = 8
    CLASSIFICATION_TEMPERATURE = 0.1
    RESPONSE_TEMPERATURE = 0.6
    SEARCH_MAX_TOKENS = 250

client = InferenceClient(api_key=Config.HF_TOKEN)
whisper_model = None

# ─── Query Categories ───────────────────────────────────────────────────────────
class QueryCategory(Enum):
    SUMMARY_INSIGHTS = "Connection Summary & Insights"
    RECOMMENDATIONS = "Best Connection Recommendations"
    ENGAGEMENT = "Engagement & Follow-up Suggestions"
    ANALYTICS = "Connection Analytics & Tracking"
    OPPORTUNITY_MAPPING = "Opportunity Mapping"

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

    def to_search_text(self) -> str:
        fields = [
            self.full_name or '',
            self.job_title or '',
            self.company or '',
            self.industry or '',
            self.sector or '',
            self.skills_experience or '',
            self.key_accomplishments or '',
            self.personal_notes or ''
        ]
        return ' '.join(fields).lower()

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

# ─── AI Search Engine ───────────────────────────────────────────────────────────
class AISearchEngine:
    
    def __init__(self):
        self.client = InferenceClient(api_key=Config.HF_TOKEN)
    
    def classify_query(self, query: str) -> QueryCategory:
        categories_list = "\n".join([
            f"{i+1}. {cat.value}" 
            for i, cat in enumerate(QueryCategory)
        ])
        
        prompt = f"""Classify this query into ONE category:

CATEGORIES:
{categories_list}

QUERY: "{query}"

Return only the category name."""

        try:
            response = self.client.chat_completion(
                model=Config.MODEL,                      # ← FIXED
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=Config.CLASSIFICATION_TEMPERATURE
            )
            
            category_text = response.choices[0].message.content.strip()
            
            for category in QueryCategory:
                if category.value.lower() in category_text.lower():
                    logger.info(f"Query classified as: {category.value}")
                    return category
            
            return QueryCategory.RECOMMENDATIONS
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return QueryCategory.RECOMMENDATIONS
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        stop_words = {
            'who', 'what', 'when', 'where', 'how', 'can', 'should',
            'the', 'for', 'and', 'with', 'about', 'help', 'me', 'my'
        }
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if len(w) > 2 and w not in stop_words]
    
    @staticmethod
    def calculate_relevance_score(
        connection: Connection,
        keywords: List[str],
        category: QueryCategory,
        query_lower: str
    ) -> float:
        score = 0.0
        search_text = connection.to_search_text()
        name_lower = (connection.full_name or '').lower()
        
        for keyword in keywords:
            if keyword in search_text:
                score += 2.0
            if keyword in (connection.industry or '').lower():
                score += 8.0
            if keyword in (connection.sector or '').lower():
                score += 7.0
            if keyword in (connection.job_title or '').lower():
                score += 6.0
            if keyword in name_lower:
                score += 50.0 if any(kw in query_lower for kw in name_lower.split()) else 15.0
        
        if category == QueryCategory.SUMMARY_INSIGHTS:
            if any(kw in name_lower for kw in keywords):
                score += 100.0
        
        elif category == QueryCategory.ENGAGEMENT:
            days = connection.days_since_contact or 0
            if 14 <= days <= 90:
                score += 20.0
            elif days > 90:
                score += 10.0
            
        elif category == QueryCategory.ANALYTICS:
            score += (connection.ai_rating or 5) * 3.0
            if connection.rating_momentum == 'improving':
                score += 12.0
        
        else:
            score += (connection.ai_rating or 5) * 2.5
            if connection.relationship_status in ['inner circle', 'professional']:
                score += 10.0
        
        return score
    
    def find_relevant_connections(
        self,
        query: str,
        category: QueryCategory,
        all_connections: List[Connection],
        limit: int = Config.MAX_CANDIDATES
    ) -> List[Connection]:
        
        if not all_connections:
            return []
        
        keywords = self.extract_keywords(query)
        query_lower = query.lower()
        
        scored_connections = []
        
        for connection in all_connections:
            score = self.calculate_relevance_score(
                connection, keywords, category, query_lower
            )
            
            if score > 3.0:
                scored_connections.append((score, connection))
        
        scored_connections.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Found {len(scored_connections)} relevant connections")
        return [conn for _, conn in scored_connections[:limit]]
    
    def generate_response(
        self, 
        category: QueryCategory, 
        query: str, 
        candidates: List[Connection]
    ) -> str:
        
        if not candidates:
            return self._generate_empty_response(query)
        
        context = self._build_candidate_context(candidates[:5])
        
        system_prompts = {
            QueryCategory.SUMMARY_INSIGHTS: 
                "You're a network advisor. Provide brief, insightful analysis of connections. Keep it under 100 words.",
            
            QueryCategory.RECOMMENDATIONS: 
                "You're a networking strategist. Recommend 2-3 connections with brief reasoning. Keep it under 120 words.",
            
            QueryCategory.ENGAGEMENT: 
                "You're a relationship expert. Suggest engagement approach in 2-3 sentences with one actionable tip.",
            
            QueryCategory.ANALYTICS: 
                "You're a network analyst. Highlight 2-3 key patterns or insights. Keep it under 100 words.",
            
            QueryCategory.OPPORTUNITY_MAPPING: 
                "You're a strategy advisor. Provide focused action plan with 2-3 connections. Keep it under 120 words."
        }
        
        user_prompt = f"""QUERY: "{query}"

TOP CONNECTIONS:
{context}

{self._get_category_instruction(category)}

REQUIREMENTS:
- Keep response under {self._get_word_limit(category)} words
- Use clear, simple formatting
- Be specific and actionable
- No fluff or repetition
- List names naturally in recommendations

Response:"""

        try:
            response = self.client.chat_completion(
                model=Config.MODEL,                      # ← FIXED
                messages=[
                    {"role": "system", "content": system_prompts[category]},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=Config.SEARCH_MAX_TOKENS,
                temperature=Config.RESPONSE_TEMPERATURE
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Response generation error: {e}")
            return "Unable to generate response. Please try rephrasing your query."
    
    def _build_candidate_context(self, candidates: List[Connection]) -> str:
        lines = []
        for i, c in enumerate(candidates, 1):
            lines.append(
                f"{i}. {c.full_name} - {c.job_title or 'N/A'} at {c.company or 'N/A'} "
                f"({c.industry or 'N/A'}) | Rating: {c.ai_rating}/10 | "
                f"Last contact: {c.days_since_contact}d ago"
            )
        return "\n".join(lines)
    
    def _get_word_limit(self, category: QueryCategory) -> int:
        limits = {
            QueryCategory.SUMMARY_INSIGHTS: 100,
            QueryCategory.RECOMMENDATIONS: 120,
            QueryCategory.ENGAGEMENT: 80,
            QueryCategory.ANALYTICS: 100,
            QueryCategory.OPPORTUNITY_MAPPING: 120
        }
        return limits.get(category, 100)
    
    def _get_category_instruction(self, category: QueryCategory) -> str:
        instructions = {
            QueryCategory.SUMMARY_INSIGHTS: 
                "Provide key insights about this connection's value and relationship status.",
            
            QueryCategory.RECOMMENDATIONS: 
                "List 2-3 best connections for this need with brief reasoning.",
            
            QueryCategory.ENGAGEMENT: 
                "Suggest when and how to reach out with one specific conversation starter.",
            
            QueryCategory.ANALYTICS: 
                "Identify 2-3 meaningful patterns in the network data.",
            
            QueryCategory.OPPORTUNITY_MAPPING: 
                "Show how 2-3 connections can help achieve this goal with clear next steps."
        }
        return instructions[category]
    
    def _generate_empty_response(self, query: str) -> str:
        return f'No matches found for: "{query}"\n\nTry broader search terms or add more connections to your network.'

# ─── Initialize Search Engine ───────────────────────────────────────────────────
search_engine = AISearchEngine()

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
            model=Config.MODEL,                          # ← FIXED
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
            model=Config.MODEL,                          # ← FIXED
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

def get_user_connections_as_objects(user_id: int) -> List[Connection]:
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
    user_id = get_current_user_id()
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query or len(query) < 3:
            return jsonify({"answer": "Please provide a more specific query."}), 400
        
        logger.info(f"Processing advanced AI search for user {user_id}: {query}")
        
        all_connections = get_user_connections_as_objects(user_id)
        
        if not all_connections:
            return jsonify({"answer": "Your network is empty. Add connections to get started with AI-powered insights."}), 200
        
        category = search_engine.classify_query(query)
        
        candidates = search_engine.find_relevant_connections(
            query, category, all_connections
        )
        
        answer = search_engine.generate_response(category, query, candidates)
        
        return jsonify({"answer": answer}), 200
        
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({"answer": "Unable to process your query. Please try again."}), 500

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

if __name__ == '__main__':
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)