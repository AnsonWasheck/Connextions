import whisper
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from huggingface_hub import InferenceClient
import time
import json
import sqlite3
import os

# Settings
class Config:
    # SECURITY: Replace this with your NEW token. 
    # Best practice: use os.getenv("HF_TOKEN")
    HF_TOKEN: str = "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" 
    MODEL: str = "Qwen/Qwen2.5-7B-Instruct"
    DB_PATH = r"C:\Users\Anson\Desktop\Backend\database\database_two.db"
    FS = 16000 
    FILENAME = "live_recording.wav"
    MAX_RESPONSE_TOKENS: int = 500
    TEMPERATURE: float = 0.1

client = InferenceClient(api_key=Config.HF_TOKEN)

def save_to_db(data):
    """Inserts categorized data into the database, handling list-to-string conversion."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # FIX: SQLite doesn't accept Python lists. 
        # Convert any list values (like skills or connections) into comma-separated strings.
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = ", ".join(map(str, value))
            elif value is None:
                data[key] = "" # Handle nulls as empty strings for cleaner DB entries

        query = """
        INSERT INTO connections (
            full_name, contact_info, job_title, company, industry, sector,
            skills_experience, key_accomplishments, relationship_status,
            days_since_contact, mutual_connections, personal_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            data.get('personal_notes')
        )
        
        cursor.execute(query, values)
        conn.commit()
        conn.close()
        print(f"✅ Successfully saved {data.get('full_name', 'Unknown')} to database.")
    except Exception as e:
        print(f"❌ Database Error: {e}")

def record_audio():
    """Handles the live audio recording via sounddevice."""
    print("\nReady! Type 'start' to begin recording.")
    cmd = input("> ").lower().strip()
    
    if cmd == "start":
        print("\n🔴 RECORDING... (Press Ctrl+C to stop)")
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
            return True
    return False

def process_and_categorize():
    """Transcribes audio and uses LLM to structure the data."""
    # 1. Transcribe
    print("🧠 Transcribing audio...")
    try:
        model = whisper.load_model("base")
        result = model.transcribe(Config.FILENAME, fp16=False)
        raw_text = result["text"]
        print(f"\n[Transcribed Text]: {raw_text}")
    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return

    # 2. Categorize with AI
    print(f"🏷️  Extracting entities using {Config.MODEL}...")
    
    prompt = f"""
    Extract professional networking data from the text below. 
    Return a valid JSON object with these EXACT keys:
    - full_name
    - contact_info
    - job_title
    - company
    - industry
    - sector
    - skills_experience
    - key_accomplishments
    - relationship_status
    - days_since_contact
    - mutual_connections
    - personal_notes

    Text: "{raw_text}"
    
    Return ONLY the raw JSON. If information is missing, use null.
    """

    try:
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=Config.MAX_RESPONSE_TOKENS,
            temperature=Config.TEMPERATURE
        )
        
        content = response.choices[0].message.content
        # Clean potential markdown formatting from LLM response
        clean_json = content.replace("```json", "").replace("```", "").strip()
        structured_data = json.loads(clean_json)

        # 3. Save to Database
        save_to_db(structured_data)

    except json.JSONDecodeError:
        print("❌ Error: AI returned invalid JSON format.")
    except Exception as e:
        print(f"❌ Processing Error: {e}")

if __name__ == "__main__":
    if record_audio():
        process_and_categorize()