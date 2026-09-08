import sqlite3
import os

def upgrade_db():
    db_path = 'resources.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(resource)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'latitude' not in columns:
            print("Adding latitude column...")
            cursor.execute("ALTER TABLE resource ADD COLUMN latitude FLOAT")
        
        if 'longitude' not in columns:
            print("Adding longitude column...")
            cursor.execute("ALTER TABLE resource ADD COLUMN longitude FLOAT")
            
        conn.commit()
        print("Database upgraded successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    upgrade_db()
