"""
Complete Database Initialization Script
Creates all tables if they don't exist
"""

import sqlite3

DB_PATH = r"C:\Users\Anson\Desktop\Backend\database\database_two.db"

def init_database():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 Initializing database...")
    
    # Create users table
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
    print("✓ Users table created/verified")
    
    # Create connections table with user_id from the start
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        full_name TEXT,
        contact_info TEXT,
        job_title TEXT,
        company TEXT,
        industry TEXT,
        sector TEXT,
        skills_experience TEXT,
        ai_summary TEXT,
        ai_rating INTEGER DEFAULT 5,
        rating_momentum TEXT DEFAULT 'Stagnant',
        key_accomplishments TEXT,
        relationship_status TEXT DEFAULT 'Professional',
        days_since_contact INTEGER DEFAULT 0,
        mutual_connections TEXT,
        personal_notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    print("✓ Connections table created/verified")
    
    # Create index for faster lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_connections_user_id 
    ON connections(user_id)
    ''')
    print("✓ Index created/verified")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database initialization complete!")
    print(f"📁 Database location: {DB_PATH}")

if __name__ == '__main__':
    init_database()