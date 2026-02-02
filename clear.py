import sqlite3

# Your database path
DB_PATH = r"C:\Users\Anson\Desktop\Backend\database\database_two.db"

# Connect to database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create the connections table
create_table_sql = """
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

cursor.execute(create_table_sql)

# Create indexes for faster searches
cursor.execute("CREATE INDEX IF NOT EXISTS idx_full_name ON connections(full_name)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_company ON connections(company)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_rating ON connections(ai_rating)")

conn.commit()
conn.close()

print("✅ SUCCESS! 'connections' table created in database_two.db")
print(f"   Location: {DB_PATH}")
print("\n📊 Table structure:")
print("   - id (auto-increment)")
print("   - full_name, contact_info, job_title, company")
print("   - industry, sector, skills_experience, key_accomplishments")
print("   - relationship_status, days_since_contact, mutual_connections")
print("   - personal_notes, ai_summary, ai_rating, rating_momentum")
print("   - created_at, updated_at (automatic timestamps)")
print("\n🚀 You're ready to run the network processor!")