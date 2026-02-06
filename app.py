"""
Flask app with multi-user support
Simple session-based authentication (no encryption for local use)
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'  # Change this to any random string

DB_PATH = "database_two.db"

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
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
    
    # Create index for faster lookups
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_connections_user_id 
    ON connections(user_id)
    ''')
    
    conn.commit()
    conn.close()

# ============================================================================
# AUTHENTICATION HELPERS
# ============================================================================

def get_current_user_id():
    """Get the current logged-in user's ID from session"""
    return session.get('user_id')

def is_logged_in():
    """Check if user is logged in"""
    return 'user_id' in session

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# USER MANAGEMENT
# ============================================================================

def create_user(email, password, first_name, last_name, company):
    """Create a new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO users (email, password, first_name, last_name, company)
            VALUES (?, ?, ?, ?, ?)
        ''', (email, password, first_name, last_name, company))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def authenticate_user(email, password):
    """Authenticate user and return user_id if successful"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()
    
    return user['id'] if user else None

# ============================================================================
# CONNECTION MANAGEMENT (USER-SPECIFIC)
# ============================================================================

def get_user_connections(user_id):
    """Get all connections for a specific user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM connections 
        WHERE user_id = ?
        ORDER BY ai_rating DESC, days_since_contact ASC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": row['id'],
            "full_name": row['full_name'] or "Unnamed",
            "contact_info": row['contact_info'] or "",
            "job_title": row['job_title'] or "Not specified",
            "company": row['company'] or "Not specified",
            "industry": row['industry'] or "Not specified",
            "sector": row['sector'] or "Not specified",
            "skills_experience": row['skills_experience'] or "",
            "ai_rating": row['ai_rating'] or 5,
            "rating_momentum": row['rating_momentum'] or "Stagnant",
            "days_since_contact": row['days_since_contact'] or 0,
            "relationship_status": row['relationship_status'] or "Professional",
            "mutual_connections": row['mutual_connections'] or "",
            "key_accomplishments": row['key_accomplishments'] or "",
            "personal_notes": row['personal_notes'] or "",
            "ai_summary": row['ai_summary'] or ""
        }
        for row in rows
    ]

def add_user_connection(user_id, data):
    """Add a connection for a specific user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO connections (
                user_id, full_name, contact_info, job_title, company, industry,
                sector, skills_experience, ai_summary, ai_rating,
                rating_momentum, key_accomplishments, relationship_status,
                days_since_contact, mutual_connections, personal_notes
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
            data.get('ai_summary'),
            int(data.get('ai_rating', 5)),
            data.get('rating_momentum'),
            data.get('key_accomplishments'),
            data.get('relationship_status'),
            int(data.get('days_since_contact', 0)),
            data.get('mutual_connections'),
            data.get('personal_notes')
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding connection: {e}")
        conn.close()
        return False

# ============================================================================
# ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_id = authenticate_user(email, password)
        
        if user_id:
            session['user_id'] = user_id
            session['email'] = email
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password")
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    company = request.form.get('company')
    
    user_id = create_user(email, password, first_name, last_name, company)
    
    if user_id:
        session['user_id'] = user_id
        session['email'] = email
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error="Email already exists")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# ROUTES - MAIN APP
# ============================================================================

@app.route('/')
@login_required
def index():
    user_id = get_current_user_id()
    connections = get_user_connections(user_id)
    return render_template('index.html', members=connections)

@app.route('/add', methods=['POST'])
@login_required
def add_connection():
    user_id = get_current_user_id()
    data = request.form.to_dict()
    
    success = add_user_connection(user_id, data)
    
    if success:
        return redirect(url_for('index'))
    else:
        return "Error adding connection", 500

@app.route('/ai_search', methods=['POST'])
@login_required
def ai_search():
    """Handle AI query with user-specific connection filtering"""
    from ai_backend import process_ai_query
    
    user_id = get_current_user_id()
    query = request.json.get('query', '')
    
    if not query:
        return jsonify({"response": "Please ask a question about your network."})
    
    # Process AI query with user-specific connections
    response = process_ai_query(query, user_id)
    
    return jsonify({"response": response})

# ============================================================================
# APP INITIALIZATION
# ============================================================================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)