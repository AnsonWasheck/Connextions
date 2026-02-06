"""
Database initialization script for multi-user connection management
Creates the database schema with users and connections tables
"""

import sqlite3
import os

DB_PATH = r"database\database_two.db"

def init_database():
    """Initialize the database with proper schema"""
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create connections table with user_id foreign key
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        full_name TEXT NOT NULL,
        contact_info TEXT,
        job_title TEXT,
        company TEXT,
        industry TEXT,
        sector TEXT,
        skills_experience TEXT,
        key_accomplishments TEXT,
        relationship_status TEXT,
        days_since_contact INTEGER DEFAULT 0,
        mutual_connections TEXT,
        personal_notes TEXT,
        ai_summary TEXT,
        ai_rating INTEGER DEFAULT 5,
        rating_momentum TEXT DEFAULT 'Stagnant',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    
    # Create index on user_id for faster queries
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_connections_user_id 
    ON connections (user_id)
    ''')
    
    # Create index on rating for faster sorting
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_connections_rating 
    ON connections (ai_rating DESC)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized successfully at {DB_PATH}")
    print("Tables created:")
    print("  - users (id, username, email, password_hash, created_at)")
    print("  - connections (id, user_id, full_name, ... [all connection fields])")


def migrate_existing_data():
    """
    Migration script for existing single-user data.
    This will assign all existing connections to a default user (user_id = 1)
    Run this ONLY if you have existing data from the old schema.
    """
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user_id column exists
    cursor.execute("PRAGMA table_info(connections)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'user_id' not in columns:
        print("🔄 Migrating existing data to multi-user schema...")
        
        # Add user_id column
        cursor.execute('ALTER TABLE connections ADD COLUMN user_id INTEGER')
        
        # Set all existing connections to user_id = 1 (default user)
        cursor.execute('UPDATE connections SET user_id = 1 WHERE user_id IS NULL')
        
        conn.commit()
        print("✅ Migration complete! All existing connections assigned to user_id = 1")
        print("⚠️  Create a user account with ID 1 to access these connections")
    else:
        print("ℹ️  Database already has multi-user support. No migration needed.")
    
    conn.close()


if __name__ == '__main__':
    print("="*60)
    print("DATABASE INITIALIZATION")
    print("="*60)
    print()
    
    # Initialize database
    init_database()
    
    print()
    print("="*60)
    print("MIGRATION CHECK")
    print("="*60)
    print()
    
    # Check for migration needs
    migrate_existing_data()
    
    print()
    print("="*60)
    print("SETUP COMPLETE")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Run the Flask app: python app.py")
    print("2. Visit http://localhost:5000/register to create an account")
    print("3. Log in and start adding connections!")