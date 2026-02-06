from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import whisper
import numpy as np
from scipy.io.wavfile import write
from huggingface_hub import InferenceClient
import json
import sqlite3
import os
import base64
import io
import wave
from typing import Dict, Any

app = Flask(__name__)
CORS(app)

# Settings
class Config:
    HF_TOKEN: str = "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" 
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH = "database_two.db"
    FS = 16000 
    MAX_RESPONSE_TOKENS: int = 1000
    TEMPERATURE: float = 0.1
    EXTRACTION_TEMPERATURE: float = 0.05

client = InferenceClient(api_key=Config.HF_TOKEN)
whisper_model = None

def load_whisper_model():
    """Load Whisper model on startup"""
    global whisper_model
    if whisper_model is None:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
    return whisper_model

def validate_and_clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates extracted data and ensures proper formatting."""
    
    schema = {
        'full_name': (str, ""),
        'contact_info': (str, ""),
        'job_title': (str, ""),
        'company': (str, ""),
        'industry': (str, ""),
        'sector': (str, ""),
        'skills_experience': (str, ""),
        'key_accomplishments': (str, ""),
        'relationship_status': (str, "New Contact"),
        'days_since_contact': (int, 0),
        'mutual_connections': (str, ""),
        'personal_notes': (str, "")
    }
    
    cleaned = {}
    for key, (expected_type, default) in schema.items():
        value = data.get(key)
        
        if value is None or value == "null" or value == "":
            cleaned[key] = default
            continue
            
        if isinstance(value, list):
            cleaned[key] = ", ".join(str(v) for v in value if v)
            continue
            
        try:
            if expected_type == int:
                cleaned[key] = int(value) if str(value).isdigit() else default
            else:
                cleaned[key] = str(value).strip()
        except (ValueError, TypeError):
            cleaned[key] = default
    
    return cleaned

def extract_structured_data(raw_text: str) -> Dict[str, Any]:
    """Multi-stage extraction with precise field definitions"""
    print(f"🏷️  Extracting entities using {Config.MODEL}...")
    
    extract_prompt = f"""You are a professional data extraction assistant. Extract networking information from the transcribed speech below and categorize it precisely.

TRANSCRIBED TEXT:
"{raw_text}"

FIELD DEFINITIONS AND INSTRUCTIONS:

1. **full_name**: The person's complete name (First Last). Extract ONLY if explicitly mentioned.

2. **contact_info**: Email addresses, phone numbers, LinkedIn URLs, or other contact methods. Format as comma-separated list.

3. **job_title**: Current position/role (e.g., "Senior Software Engineer", "VP of Sales"). Extract ONLY the title, not the company.

4. **company**: Current employer/organization name. Extract ONLY the company name.

5. **industry**: Broad sector (e.g., "Technology", "Healthcare", "Finance", "Manufacturing", "Consulting"). Choose ONE that best fits.

6. **sector**: Specific niche within industry (e.g., "SaaS", "Biotechnology", "Investment Banking", "E-commerce"). Be specific.

7. **skills_experience**: Technical skills, expertise areas, years of experience, specializations. Include specific technologies, methodologies, or domains mentioned. Separate with commas.

8. **key_accomplishments**: Concrete achievements, projects led, revenue generated, awards, publications, successful outcomes. ONLY include measurable or significant accomplishments explicitly mentioned.

9. **relationship_status**: Nature of relationship. Choose EXACTLY ONE:
   - "New Contact" (just met)
   - "Existing Acquaintance" (know them casually)
   - "Professional Contact" (worked together before)
   - "Close Colleague" (regular collaboration)
   - "Strategic Partner" (formal partnership)

10. **days_since_contact**: Number of days since last interaction. Extract ONLY if a timeframe is mentioned (e.g., "spoke last week" = 7, "met yesterday" = 1, "haven't talked in a month" = 30). Use 0 if this is first contact or not mentioned.

11. **mutual_connections**: Names of people you both know. Comma-separated list. ONLY include if explicitly mentioned.

12. **personal_notes**: Any personal details, interests, context, or memorable facts about the person (hobbies, family info, preferences, conversation topics). This is the catch-all for relationship-building details.

CRITICAL RULES:
- Return ONLY valid JSON with the exact field names above
- Use null for missing information - do NOT guess or infer
- Be precise: extract ONLY what was explicitly stated
- Keep each field focused on its specific purpose
- No markdown, no explanation, just pure JSON

OUTPUT FORMAT:
{{
  "full_name": "...",
  "contact_info": "...",
  "job_title": "...",
  "company": "...",
  "industry": "...",
  "sector": "...",
  "skills_experience": "...",
  "key_accomplishments": "...",
  "relationship_status": "...",
  "days_since_contact": 0,
  "mutual_connections": "...",
  "personal_notes": "..."
}}"""

    try:
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": extract_prompt}],
            max_tokens=Config.MAX_RESPONSE_TOKENS,
            temperature=Config.EXTRACTION_TEMPERATURE
        )
        
        content = response.choices[0].message.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        structured_data = json.loads(content)
        cleaned_data = validate_and_clean_data(structured_data)
        
        return cleaned_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None

def generate_ai_analysis(data: Dict[str, Any]) -> Dict[str, str]:
    """Generates a professional summary and strict 1-10 business rating"""
    print("\n📊 Generating AI Summary and Rating...")
    
    analysis_prompt = f"""You are a strategic business analyst. Rate this connection honestly and precisely on a 1-10 scale. Do NOT default to the middle. Use the FULL range. Map the person directly to the score that fits them.

CONNECTION DATA:
- Name: {data.get('full_name', 'Unknown')}
- Role: {data.get('job_title', 'N/A')} at {data.get('company', 'N/A')}
- Industry/Sector: {data.get('industry', 'N/A')} / {data.get('sector', 'N/A')}
- Skills: {data.get('skills_experience', 'N/A')}
- Accomplishments: {data.get('key_accomplishments', 'N/A')}
- Relationship: {data.get('relationship_status', 'N/A')}
- Personal Notes: {data.get('personal_notes', 'N/A')}

RATING SCALE — match the person to the score that describes them:

1 — No skills, no role, no industry relevance whatsoever. Adds nothing professionally.
2 — Has a job but it is completely unrelated. No skills or accomplishments worth noting.
3 — Slightly adjacent industry or a very entry-level role. Unlikely to ever be useful professionally.
4 — Recognizable industry, but junior with no real leverage or skills of note.
5 — Mid-level, some relevant skills. Could come up in passing but not someone you would actively seek out.
6 — Solid mid-career professional. Useful for casual advice or a warm intro if the moment is right.
7 — Senior, skilled, and in a relevant space. Actively worth staying in touch with. Real potential for collaboration.
8 — Decision-maker or a well-connected influencer with a strong track record. Opens doors.
9 — Major player. C-suite, investor, or someone with direct power to greenlight big things in your world. Life-changing contact potential.
10 — Transformative. The kind of connection that could completely reshape your trajectory — top investor, dream client, or the single most important person in your industry for your goals.

RULES:
- If the person has no skills and does nothing, rate them a 1. Do not soften it.
- If the person is genuinely a 9 or 10 based on the descriptions above, rate them a 9 or 10. Do not hold back.
- Rate based ONLY on what is in the data. Do not invent qualifications.
- If key fields are empty or N/A, that LOWERS the rating — missing info means missing value.
- The summary should be 2 sentences: what they bring and why they matter (or do not).

Return ONLY valid JSON:
{{
  "ai_summary": "Two-sentence summary of their actual value.",
  "ai_rating": 5,
  "rating_momentum": "Stagnant"
}}"""

    try:
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=400,
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(content)
        analysis['rating_momentum'] = "Stagnant"
        
        rating = analysis.get('ai_rating', 5)
        if not isinstance(rating, int) or rating < 1 or rating > 10:
            print(f"⚠️ Invalid rating {rating}, defaulting to 5")
            analysis['ai_rating'] = 5
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Analysis Error: {e}")
        return {
            "ai_summary": "Summary generation failed - manual review recommended.",
            "ai_rating": 5,
            "rating_momentum": "Stagnant"
        }

def save_to_db(data: Dict[str, Any]) -> None:
    """Inserts categorized data and AI analysis into the database"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        query = """
        INSERT INTO connections (
            full_name, contact_info, job_title, company, industry, sector,
            skills_experience, key_accomplishments, relationship_status,
            days_since_contact, mutual_connections, personal_notes,
            ai_summary, ai_rating, rating_momentum
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
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
        )
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully saved {data.get('full_name', 'Unknown')} to database.")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")
        raise

# Serve the frontend HTML
@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """Endpoint to receive audio data and process it"""
    try:
        # Get audio data from request
        audio_data = request.json.get('audio')
        
        if not audio_data:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
        
        # Save temporarily
        temp_filename = 'temp_recording.wav'
        with open(temp_filename, 'wb') as f:
            f.write(audio_bytes)
        
        # Transcribe
        model = load_whisper_model()
        result = model.transcribe(temp_filename, fp16=False)
        raw_text = result["text"].strip()
        
        print(f"Transcribed: {raw_text}")
        
        # Extract structured data
        structured_data = extract_structured_data(raw_text)
        
        if structured_data is None:
            return jsonify({'error': 'Failed to extract structured data'}), 500
        
        # Generate AI analysis
        analysis_results = generate_ai_analysis(structured_data)
        structured_data.update(analysis_results)
        
        # Save to database
        save_to_db(structured_data)
        
        # Clean up temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        return jsonify({
            'success': True,
            'transcription': raw_text,
            'data': structured_data
        })
        
    except Exception as e:
        print(f"Error processing audio: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/connections', methods=['GET'])
def get_connections():
    """Endpoint to retrieve all connections from database"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM connections ORDER BY id DESC")
        rows = cursor.fetchall()
        
        connections = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(connections)
        
    except Exception as e:
        print(f"Error fetching connections: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Initialize database if it doesn't exist
    if not os.path.exists(Config.DB_PATH):
        print("Creating database...")
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            contact_info TEXT,
            job_title TEXT,
            company TEXT,
            industry TEXT,
            sector TEXT,
            skills_experience TEXT,
            key_accomplishments TEXT,
            relationship_status TEXT,
            days_since_contact INTEGER,
            mutual_connections TEXT,
            personal_notes TEXT,
            ai_summary TEXT,
            ai_rating INTEGER,
            rating_momentum TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Database created!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)