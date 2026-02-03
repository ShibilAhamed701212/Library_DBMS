import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.repository.db_access import execute, fetch_all

def migrate():
    print("Checking chat_rooms schema...")
    columns = fetch_all("DESCRIBE chat_rooms")
    col_names = [c['Field'] for c in columns]
    print(f"Existing columns: {col_names}")

    if 'description' not in col_names:
        print("Adding 'description' column...")
        execute("ALTER TABLE chat_rooms ADD COLUMN description TEXT")
    
    if 'room_avatar' not in col_names:
        print("Adding 'room_avatar' column...")
        execute("ALTER TABLE chat_rooms ADD COLUMN room_avatar VARCHAR(255)")

    print("Migration complete.")

if __name__ == "__main__":
    migrate()
