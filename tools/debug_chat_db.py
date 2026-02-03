import sys
import os
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

# Load env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "app_user"),
        password=os.getenv("DB_PASSWORD", "App@123"),
        database=os.getenv("DB_NAME", "library_db"),
        port=int(os.getenv("DB_PORT", 3306))
    )

def debug_chat_db():
    print("🔍 Debugging Chat DB...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Check Tables
        cursor.execute("SHOW TABLES LIKE 'chat%'")
        tables = cursor.fetchall()
        print("Tables found:", [t.values() for t in tables])
        
        # 2. Check chat_messages columns
        print("\nChecking chat_messages schema:")
        cursor.execute("DESCRIBE chat_messages")
        columns = cursor.fetchall()
        for col in columns:
            print(f" - {col['Field']} ({col['Type']})")
            
        # 3. Check Users
        print("\nChecking Users:")
        cursor.execute("SELECT user_id, name, email FROM users LIMIT 5")
        users = cursor.fetchall()
        for u in users:
            print(f" - ID: {u['user_id']}, Name: {u['name']}")
            
        # 4. Check Rooms
        print("\nChecking Rooms:")
        cursor.execute("SELECT room_id, name FROM chat_rooms LIMIT 5")
        rooms = cursor.fetchall()
        for r in rooms:
            print(f" - ID: {r['room_id']}, Name: {r['name']}")
            
        if not rooms:
            print("❌ No rooms found! Creating one...")
            cursor.execute("INSERT INTO chat_rooms (name, description, created_by, is_official) VALUES ('Debug Room', 'Test', 1, 1)")
            conn.commit()
            print("Created Debug Room")
            
        # 5. Try Insert Message
        print("\nAttempting to insert test message...")
        test_room_id = rooms[0]['room_id'] if rooms else 1
        test_user_id = users[0]['user_id'] if users else 1
        
        cursor.execute("""
            INSERT INTO chat_messages (room_id, user_id, content, msg_type)
            VALUES (%s, %s, 'DEBUG MSG', 'text')
        """, (test_room_id, test_user_id))
        conn.commit()
        print(f"✅ inserted message into room {test_room_id} for user {test_user_id}")
        
        # 6. Read back
        cursor.execute("SELECT * FROM chat_messages WHERE content='DEBUG MSG' ORDER BY created_at DESC LIMIT 1")
        msg = cursor.fetchone()
        print("Read back:", msg)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_chat_db()
