
import sys
import os

# Ensure backend package is importable
sys.path.append(os.getcwd())

from backend.repository.db_access import execute, fetch_one
from backend.app import create_app

app = create_app()

def reset_global():
    with app.app_context():
        print("--- Resetting Global Community (Channel 1) ---")
        
        # 1. Check if it exists
        glob = fetch_one("SELECT * FROM channels WHERE channel_id = 1")
        if not glob:
            print("Global Channel ID 1 not found! Creating it...")
            execute("INSERT INTO channels (channel_id, name, type, is_private) VALUES (1, 'Global Community', 'public', FALSE)")
        else:
            print(f"Found Global Channel: {glob['name']}")

        # 2. Delete All Messages
        print("Deleting all messages...")
        execute("DELETE FROM chat_messages WHERE channel_id = 1")
        
        # 3. Delete All Participants (Reset membership)
        # Admins are included by default in the logic, so this drops regular members only
        print("Clearing participant list...")
        execute("DELETE FROM dm_participants WHERE channel_id = 1")
        
        # 4. Reset Settings (Optional, but 'reset' implies default state)
        # Reset Icon and Name to defaults
        print("Resetting channel settings...")
        execute("UPDATE channels SET name = 'Global Community', icon = NULL, is_private = FALSE WHERE channel_id = 1")

        print("--- Global Community Reset Complete ---")

if __name__ == "__main__":
    reset_global()
