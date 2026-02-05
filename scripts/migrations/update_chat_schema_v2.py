from backend.repository.db_access import get_connection

def migrate_v2():
    print("🚀 Starting Chat System Schema Update (v2)...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 1. Update chat_messages table
        print("🔹 Updating table: chat_messages")
        
        # Check if columns exist before adding (using a try-catch approach per column or just ADD COLUMN IF NOT EXISTS syntax if supported by MySQL 8+, but generic ADD is safer with try-except for robust script)
        
        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN sender_type ENUM('anon', 'user') DEFAULT 'anon' AFTER anon_id")
            print("   - Added sender_type")
        except Exception as e:
            print(f"   - sender_type might already exist: {e}")

        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN file_url VARCHAR(255) NULL AFTER message_text")
            print("   - Added file_url")
        except Exception as e:
            print(f"   - file_url might already exist: {e}")

        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN is_edited BOOLEAN DEFAULT FALSE AFTER sent_at")
            print("   - Added is_edited")
        except Exception as e:
            print(f"   - is_edited might already exist: {e}")
            
        
        # 2. Update chat_rooms schema for Broadcasts
        # Ensure room_type supports 'broadcast'
        # MySQL ENUMs are tricky to modify in place cleanly without full definitions
        # We will modify the column to include 'broadcast'
        print("🔹 Updating table: chat_rooms")
        try:
            cursor.execute("ALTER TABLE chat_rooms MODIFY COLUMN room_type ENUM('public', 'private', 'study', 'librarian', 'broadcast') NOT NULL")
            print("   - Updated room_type enum to include 'broadcast'")
        except Exception as e:
            print(f"   - Failed to update room_type: {e}")

        conn.commit()
        print("✅ Schema Update V2 completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Update failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate_v2()
