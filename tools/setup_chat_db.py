import sys
import os

# Add project root to path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)
print(f"DEBUG: Added {root_dir} to sys.path")

from backend.repository.db_access import execute, fetch_all


def setup_chat_db():
    print("🚧 Setting up Chat Database Schema...")
    
    # 1. Update/Create CHAT_ROOMS
    print("Checking 'chat_rooms' table...")
    # Add 'room_type' column if not exists
    try:
        execute("ALTER TABLE chat_rooms ADD COLUMN room_type VARCHAR(50) DEFAULT 'general'")
        print("   + Added 'room_type' column.")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("   - 'room_type' column already exists.")
        else:
            print(f"   - Note: {e}")

    # 2. Update/Create CHAT_MESSAGES
    print("Checking 'chat_messages' table...")
    # Add 'type' column (text, image, system)
    try:
        execute("ALTER TABLE chat_messages ADD COLUMN msg_type VARCHAR(20) DEFAULT 'text'")
        print("   + Added 'msg_type' column.")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("   - 'msg_type' column already exists.")
        else:
            execute("CREATE TABLE IF NOT EXISTS chat_messages ("
                    "message_id INT AUTO_INCREMENT PRIMARY KEY,"
                    "room_id INT,"
                    "user_id INT,"
                    "content TEXT,"
                    "msg_type VARCHAR(20) DEFAULT 'text',"
                    "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
                    "FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id),"
                    "FOREIGN KEY (user_id) REFERENCES users(user_id)"
                    ")")
            print("   + Created 'chat_messages' table.")

    # 3. Create CHAT_MEMBERS (For roles/permissions)
    print("Creating 'chat_members' table...")
    execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            room_id INT,
            user_id INT,
            role VARCHAR(20) DEFAULT 'member',  -- admin, moderator, member
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (room_id, user_id),
            FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    print("   + Verified 'chat_members' table.")
    
    print("✅ Chat Database Schema Ready!")

if __name__ == "__main__":
    setup_chat_db()
