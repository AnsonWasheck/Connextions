"""
Migration Helper: Assign existing connections to a user
Run this AFTER creating your first user account
"""

import sqlite3

DB_PATH = "database_two.db"

def show_users():
    """Display all users in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, email, first_name, last_name FROM users')
    users = cursor.fetchall()
    
    conn.close()
    
    if not users:
        print("❌ No users found! Please register a user first.")
        return None
    
    print("\n📋 Available Users:")
    print("-" * 60)
    for user in users:
        print(f"ID: {user[0]} | Email: {user[1]} | Name: {user[2]} {user[3]}")
    print("-" * 60)
    
    return users

def count_unassigned_connections():
    """Count connections without a user_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM connections WHERE user_id IS NULL')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

def assign_connections_to_user(user_id):
    """Assign all unassigned connections to a specific user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE connections SET user_id = ? WHERE user_id IS NULL', (user_id,))
    updated = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return updated

def main():
    print("=" * 60)
    print("  Connection Migration Helper")
    print("=" * 60)
    
    # Check for unassigned connections
    unassigned = count_unassigned_connections()
    print(f"\n🔍 Found {unassigned} connections without a user assignment")
    
    if unassigned == 0:
        print("✅ All connections are already assigned!")
        return
    
    # Show available users
    users = show_users()
    if not users:
        return
    
    # Get user choice
    print("\n" + "=" * 60)
    try:
        user_id = int(input("Enter the User ID to assign connections to: "))
        
        # Verify user exists
        valid_ids = [u[0] for u in users]
        if user_id not in valid_ids:
            print(f"❌ Invalid User ID. Please choose from: {valid_ids}")
            return
        
        # Confirm
        print(f"\n⚠️  This will assign {unassigned} connections to User ID {user_id}")
        confirm = input("Continue? (yes/no): ").lower()
        
        if confirm in ['yes', 'y']:
            updated = assign_connections_to_user(user_id)
            print(f"\n✅ Successfully assigned {updated} connections to User ID {user_id}")
        else:
            print("\n❌ Migration cancelled")
    
    except ValueError:
        print("❌ Invalid input. Please enter a number.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()