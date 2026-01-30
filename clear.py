import sqlite3

conn = sqlite3.connect('database_two.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

# Delete all data from every table
for table in tables:
    cursor.execute(f"DELETE FROM {table[0]};")

conn.commit()
conn.close()
print("Database cleared successfully.")