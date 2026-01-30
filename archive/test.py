import sqlite3
import os
import re
from huggingface_hub import InferenceClient

# ── CONFIG ───────────────────────────────────────────────────────────────
# Using the token provided in your snippet
YOUR_HF_TOKEN = "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"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

client = InferenceClient(token=YOUR_HF_TOKEN, model=MODEL)

# ── DATABASE HELPERS ─────────────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect('beta_testers.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_people():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Fetch EVERYTHING to give the AI maximum context
            cursor.execute("SELECT * FROM testers")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        print("Error: Database table 'testers' not found.")
        return []

# ── SEARCH & PRECISION LOGIC ─────────────────────────────────────────────
def find_relevant_candidates(all_people, query, limit=15):
    """
    Ranks candidates based on keywords to ensure the AI only sees 
    the most likely matches. This stops the AI from picking random people.
    """
    query_lower = query.lower()
    scored_list = []
    
    # Common keywords to boost accuracy
    keywords = re.findall(r'\w+', query_lower)
    
    for person in all_people:
        score = 0
        # Combine all searchable text
        search_blob = f"{person['experience']} {person['summary']} {person['jobs']} {person['accomplishments']} {person['personal_notes']}".lower()
        
        for word in keywords:
            if len(word) > 2 and word in search_blob:
                score += 2
                # Extra weight for jobs and experience matches
                if word in str(person['jobs']).lower(): score += 3
                if word in str(person['experience']).lower(): score += 3

        if score > 0:
            scored_list.append((score, person))
    
    # Sort by score descending
    scored_list.sort(key=lambda x: x[0], reverse=True)
    return [p for score, p in scored_list[:limit]]

# ── AI PROMPTING HELPERS ─────────────────────────────────────────────────
def create_selection_prompt(people_list, criteria, user_context):
    candidates_text = ""
    for p in people_list:
        candidates_text += (
            f"--- CANDIDATE: {p['name']} ---\n"
            f"ROLE/EXP: {p['experience']}\n"
            f"CURRENT JOB: {p.get('jobs', 'N/A')}\n"
            f"SUMMARY: {p.get('summary', 'N/A')}\n"
            f"ACCOMPLISHMENTS: {p.get('accomplishments', 'N/A')}\n"
            f"NOTES: {p.get('personal_notes', 'N/A')}\n\n"
        )
    
    return [
        {
            "role": "system", 
            "content": f"You are a professional recruitment and investment analyst. Session Context: {user_context}. Your task is to find the best match based on the user's specific request. Do not hallucinate skills; only use the data provided."
        },
        {
            "role": "user", 
            "content": f"Request: {criteria}\n\nHere are the top candidates from the database:\n\n{candidates_text}\n\nWho is the best match? Format your response as:\nBEST MATCH: [Name]\nREASON: [3-5 sentences explaining exactly why their background, job title, and wins make them the right choice.]"
        }
    ]

# ── MAIN CHAT LOOP ───────────────────────────────────────────────────────
def main():
    print(f"--- AI Database Assistant (Fully Functional) ---")
    
    # Simple one-step setup
    user_context = input("What is the overarching goal for this session? (e.g. 'Finding investors for an AI CRM'): ").strip()
    if not user_context:
        user_context = "General database search"

    all_people = get_all_people()
    if not all_people: return

    print(f"\nSuccessfully loaded {len(all_people)} profiles.")
    print("Commands: 'list' (show all), 'summary [name]', or just type what you are looking for (e.g. 'best potential investor').")

    while True:
        try:
            query = input("\n> ").strip()
            if not query or query.lower() in ["exit", "quit", "q"]: 
                break

            if query.lower() == "list":
                names = [p['name'] for p in all_people]
                print(f"Total People: {', '.join(names)}")
                continue

            # Route to Precision Search
            print("AI is searching and analyzing...", end="\r")
            
            # 1. Narrow down the 100+ people to the most relevant 15
            relevant_candidates = find_relevant_candidates(all_people, query)
            
            if not relevant_candidates:
                # If no keywords match, use the first 15 as a fallback
                relevant_candidates = all_people[:15]

            # 2. Generate the AI Prompt
            messages = create_selection_prompt(relevant_candidates, query, user_context)

            # 3. Stream the AI Result
            print("AI: ", end="", flush=True)
            for chunk in client.chat_completion(messages=messages, max_tokens=600, stream=True):
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
            print()

        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()