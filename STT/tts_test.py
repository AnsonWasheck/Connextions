import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from huggingface_hub import InferenceClient
import time
import json
import sqlite3
import os
from typing import Dict, Any, Optional

# Settings
class Config:
    HF_TOKEN: str = "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" 
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH = r"C:\Users\Anson\Desktop\Backend\database\database_two.db"
    FS = 16000 
    FILENAME = "live_recording.wav"
    MAX_RESPONSE_TOKENS: int = 1000
    TEMPERATURE: float = 0.1
    EXTRACTION_TEMPERATURE: float = 0.05  # Lower for more deterministic extraction

client = InferenceClient(api_key=Config.HF_TOKEN)


def validate_and_clean_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates extracted data and ensures proper formatting."""
    
    # Define expected types and defaults
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
        
        # Handle None or missing values
        if value is None or value == "null" or value == "":
            cleaned[key] = default
            continue
            
        # Handle lists (convert to comma-separated string)
        if isinstance(value, list):
            cleaned[key] = ", ".join(str(v) for v in value if v)
            continue
            
        # Type conversion
        try:
            if expected_type == int:
                cleaned[key] = int(value) if str(value).isdigit() else default
            else:
                cleaned[key] = str(value).strip()
        except (ValueError, TypeError):
            cleaned[key] = default
    
    return cleaned


def extract_structured_data(raw_text: str) -> Dict[str, Any]:
    """
    Multi-stage extraction with precise field definitions and examples.
    Uses detailed prompting to guide the LLM toward accurate categorization.
    """
    print(f"🏷️  Extracting entities using {Config.MODEL}...")
    
    # Stage 1: Detailed extraction with explicit field definitions
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
        
        # Clean JSON extraction
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        structured_data = json.loads(content)
        
        # Validate and clean
        cleaned_data = validate_and_clean_data(structured_data)
        
        print("\n✅ Extracted Data:")
        for key, value in cleaned_data.items():
            print(f"   {key}: {value}")
        
        return cleaned_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"Raw response: {content[:500]}")
        return None
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return None


def generate_ai_analysis(data: Dict[str, Any]) -> Dict[str, str]:
    """
    Generates a professional summary and strict 1-10 business rating.
    Uses comprehensive criteria for precise, consistent ratings.
    """
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
        
        # Clean JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(content)
        
        # Enforce constraints
        analysis['rating_momentum'] = "Stagnant"
        
        # Validate rating is 1-10
        rating = analysis.get('ai_rating', 5)
        if not isinstance(rating, int) or rating < 1 or rating > 10:
            print(f"⚠️ Invalid rating {rating}, defaulting to 5")
            analysis['ai_rating'] = 5
        
        print(f"\n✅ AI Analysis Complete:")
        print(f"   Rating: {analysis['ai_rating']}/10")
        print(f"   Summary: {analysis['ai_summary']}")
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Analysis Error: {e}")
        return {
            "ai_summary": "Summary generation failed - manual review recommended.",
            "ai_rating": 5,
            "rating_momentum": "Stagnant"
        }


def save_to_db(data: Dict[str, Any]) -> None:
    """Inserts categorized data and AI analysis into the database."""
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
        
        print(f"\n✅ Successfully saved {data.get('full_name', 'Unknown')} to database.")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")


def record_audio() -> bool:
    """Handles the live audio recording via sounddevice."""
    print("\n" + "="*60)
    print("🎙️  AUDIO RECORDING SYSTEM")
    print("="*60)
    print("\nReady to record! Type 'start' to begin recording.")
    print("Press Ctrl+C when finished speaking.\n")
    
    cmd = input("> ").lower().strip()
    
    if cmd == "start":
        print("\n🔴 RECORDING IN PROGRESS...")
        print("Speak clearly. Press Ctrl+C when done.\n")
        
        audio_data = []
        try:
            def callback(indata, frames, time_info, status):
                audio_data.append(indata.copy())
            
            with sd.InputStream(samplerate=Config.FS, channels=1, callback=callback):
                while True:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Recording stopped.")
            
        if audio_data:
            full_audio = np.concatenate(audio_data, axis=0)
            write(Config.FILENAME, Config.FS, full_audio)
            print(f"✅ Audio saved to {Config.FILENAME}")
            return True
    
    return False


def process_and_categorize() -> None:
    """Transcribes audio and uses LLM to structure and analyze the data."""
    
    print("\n" + "="*60)
    print("🧠 TRANSCRIPTION & ANALYSIS")
    print("="*60 + "\n")
    
    # Transcribe audio
    print("🎧 Transcribing audio with Whisper...")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(Config.FILENAME, fp16=False)
        raw_text = result["text"].strip()
        
        print(f"\n📝 TRANSCRIBED TEXT:")
        print("-" * 60)
        print(f"{raw_text}")
        print("-" * 60)
        
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return

    # Extract structured data
    structured_data = extract_structured_data(raw_text)
    
    if structured_data is None:
        print("❌ Failed to extract structured data. Aborting.")
        return

    # Generate AI analysis
    analysis_results = generate_ai_analysis(structured_data)
    structured_data.update(analysis_results)

    # Save to database
    save_to_db(structured_data)
    
    print("\n" + "="*60)
    print("✅ PROCESSING COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    if record_audio():
        process_and_categorize()