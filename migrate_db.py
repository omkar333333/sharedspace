import sqlite3
import os

db_path = 'resources.db'

def run():
    print(f"Connecting to {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Adding trust_score to user table...")
        cursor.execute("ALTER TABLE user ADD COLUMN trust_score INTEGER DEFAULT 100")
        print("Added trust_score.")
    except Exception as e:
        print(f"Error adding trust_score (maybe already exists): {e}")
        
    try:
        print("Creating notification table...")
        cursor.execute("""
            CREATE TABLE notification (
                id INTEGER NOT NULL, 
                user_id INTEGER NOT NULL, 
                message TEXT NOT NULL, 
                is_read BOOLEAN, 
                created_at DATETIME NOT NULL, 
                PRIMARY KEY (id), 
                FOREIGN KEY(user_id) REFERENCES user (id)
            )
        """)
        print("Created notification table.")
    except Exception as e:
        print(f"Error creating notification table: {e}")

    conn.commit()
    conn.close()
    print("Database update complete.")

if __name__ == '__main__':
    run()
