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

def debug_specific():
    print("🔍 Inspecting 'ziya' and 'hack club'...")
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Find User
        cursor.execute("SELECT * FROM users WHERE name LIKE '%ziya%'")
        user = cursor.fetchone()
        if not user:
            print("❌ User 'ziya' not found!")
            return
        print(f"✅ User found: ID={user['user_id']}, Name={user['name']}")
        
        # 2. Find Room
        cursor.execute("SELECT * FROM chat_rooms WHERE name LIKE '%hack club%'")
        room = cursor.fetchone()
        if not room:
            print("❌ Room 'hack club' not found!")
            # List all rooms
            cursor.execute("SELECT * FROM chat_rooms")
            print("Available rooms:", cursor.fetchall())
            return
        print(f"✅ Room found: ID={room['room_id']}, Name={room['name']}, Type={room.get('room_type')}, Official={room['is_official']}")
        
        # 3. Check Membership
        cursor.execute("SELECT * FROM chat_members WHERE user_id=%s AND room_id=%s", (user['user_id'], room['room_id']))
        member = cursor.fetchone()
        if member:
            print(f"✅ User is member: Role={member['role']}")
        else:
            print("❌ User is NOT a member of this room!")
            
        # 4. Check Messages
        cursor.execute("SELECT count(*) as cnt FROM chat_messages WHERE room_id=%s", (room['room_id'],))
        count = cursor.fetchone()['cnt']
        print(f"ℹ️  Message count for room: {count}")
        
        cursor.execute("SELECT * FROM chat_messages WHERE room_id=%s ORDER BY created_at DESC LIMIT 3", (room['room_id'],))
        msgs = cursor.fetchall()
        print("Last 3 messages:", msgs)

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    debug_specific()
