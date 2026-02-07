import sqlite3
import random
from datetime import datetime, timedelta

# Configuration
DB_FILE = r'database/database_two.db'
TARGET_USER_ID = 1
NUM_RECORDS = 100

# --- Data Pools for Realistic Generation ---
first_names = ["James", "Maria", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Margaret", "Anthony", "Betty", "Mark", "Sandra"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]

job_titles = ["Software Engineer", "Product Manager", "Marketing Director", "Sales Associate", "CEO", "Founder", "HR Specialist", "Data Scientist", "Consultant", "Project Manager", "UX Designer", "Financial Analyst", "Operations Manager", "Accountant", "Legal Counsel"]
companies = ["TechCorp", "Innovate Solutions", "Global Dynamics", "Creative Minds", "Future Systems", "BlueSky Inc.", "Vertex Industries", "Summit Holdings", "Omega Partners", "Alpha Logistics", "NextGen Digital", "Pioneer Group"]
industries = ["Technology", "Finance", "Healthcare", "Education", "Manufacturing", "Retail", "Consulting", "Real Estate", "Entertainment", "Energy"]
sectors = ["Private", "Public", "Non-Profit"]
skills_list = ["Python", "Strategic Planning", "Public Speaking", "Data Analysis", "Leadership", "Project Management", "Marketing", "Sales", "Negotiation", "Cloud Computing", "Machine Learning", "Financial Modeling", "Team Building"]

relationship_statuses = ["New Contact", "Active", "Stagnant", "Warm Lead", "Close Friend", "Professional Network"]
momentums = ["Increasing", "Decreasing", "Stable", "Rapid Growth"]

# --- Helper Functions ---

def generate_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_contact(name):
    # Create a realistic email based on the name
    clean_name = name.lower().replace(" ", ".")
    domains = ["gmail.com", "outlook.com", "yahoo.com", "company.net", "innovate.io"]
    return f"{clean_name}{random.randint(1, 99)}@{random.choice(domains)}"

def generate_skills():
    # Pick 3 random skills
    return ", ".join(random.sample(skills_list, 3))

def generate_summary(name, job, industry):
    templates = [
        f"{name} is a seasoned {job} in the {industry} space with a strong track record.",
        f"High-potential contact. {name} currently works as a {job} and has extensive experience.",
        f"{name} demonstrates strong leadership skills in {industry}. Currently looking for new opportunities.",
        f"Met {name} at a conference. They are an expert {job} focusing on innovation.",
    ]
    return random.choice(templates)

def generate_accomplishments():
    accomplishments = [
        "Led a team of 10 to succesful launch.",
        "Increased revenue by 20% YoY.",
        "Published 3 industry papers.",
        "Keynote speaker at TechSummit 2025.",
        "Developed a proprietary algorithm.",
        "Streamlined operations saving $50k annually."
    ]
    return random.choice(accomplishments)

# --- Main Execution ---

def inject_data():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        print(f"Connected to {DB_FILE}...")
        
        insert_query = """
        INSERT INTO connections (
            full_name, contact_info, job_title, company, industry, sector, 
            skills_experience, key_accomplishments, relationship_status, 
            days_since_contact, mutual_connections, personal_notes, 
            ai_summary, ai_rating, rating_momentum, user_id, 
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        rows_to_insert = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for _ in range(NUM_RECORDS):
            full_name = generate_name()
            job = random.choice(job_titles)
            industry = random.choice(industries)
            
            row = (
                full_name,                                  # full_name
                generate_contact(full_name),                # contact_info
                job,                                        # job_title
                random.choice(companies),                   # company
                industry,                                   # industry
                random.choice(sectors),                     # sector
                generate_skills(),                          # skills_experience
                generate_accomplishments(),                 # key_accomplishments
                random.choice(relationship_statuses),       # relationship_status
                random.randint(0, 365),                     # days_since_contact
                f"{random.randint(0, 50)} mutuals",         # mutual_connections
                "Met at networking event.",                 # personal_notes
                generate_summary(full_name, job, industry), # ai_summary
                random.randint(10, 99),                     # ai_rating
                random.choice(momentums),                   # rating_momentum
                TARGET_USER_ID,                             # user_id
                current_time,                               # created_at
                current_time                                # updated_at
            )
            rows_to_insert.append(row)
            
        cursor.executemany(insert_query, rows_to_insert)
        conn.commit()
        
        print(f"Successfully injected {NUM_RECORDS} records for user_id {TARGET_USER_ID}.")
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inject_data()