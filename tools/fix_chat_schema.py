import os
import sys
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
from pathlib import Path

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

def fix_schema():
    print("🛠️ Starting Chat Schema Fix (Standalone)...")
    
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Create chat_members table if not exists
        print("Checking 'chat_members' table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_members (
                member_id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                user_id INT NOT NULL,
                role ENUM('member', 'admin') DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY uq_room_user (room_id, user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        print("✅ 'chat_members' table ensured.")

        # 2. Add room_type to chat_rooms if not exists
        print("Checking 'room_type' column in 'chat_rooms'...")
        cursor.execute("""
            SELECT count(*) as cnt 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'chat_rooms' 
            AND COLUMN_NAME = 'room_type'
        """)
        result = cursor.fetchone()
        
        if not result or result['cnt'] == 0:
            print("Adding 'room_type' column...")
            cursor.execute("""
                ALTER TABLE chat_rooms 
                ADD COLUMN room_type ENUM('public', 'private', 'direct') DEFAULT 'public' 
                AFTER is_official
            """)
            print("✅ 'room_type' column added.")
        else:
            print("✅ 'room_type' column already exists.")
            
        conn.commit()
        print("\n✨ Schema fix completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error fixing schema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_schema()
