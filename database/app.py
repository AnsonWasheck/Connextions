import sqlite3
import pandas as pd
from flask import Flask

app = Flask(__name__)
DB_PATH = 'database_two.db'

def get_table_names():
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT name FROM sqlite_master WHERE type='table';"
        return [row[0] for row in conn.execute(query).fetchall()]

@app.route('/')
def index():
    try:
        tables = get_table_names()
        html_content = "<h1>Database Viewer</h1>"
        
        with sqlite3.connect(DB_PATH) as conn:
            for table in tables:
                html_content += f"<h3>Table: {table}</h3>"
                df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 10", conn)
                # Convert dataframe to a nice HTML table
                html_content += df.to_html(classes='table table-striped', index=False)
                html_content += "<hr>"
        
        return f"<html><head><link rel='stylesheet' href='https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css'></head><body class='container'>{html_content}</body></html>"
    
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    print("Starting website at http://127.0.0.1:5000")
    app.run(debug=True)