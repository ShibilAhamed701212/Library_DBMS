import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.repository.db_access import get_connection

def reset_and_migrate():
    print("🚀 Resetting Chat System Database Schema...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # DROP TABLES (Order matters due to foreign keys)
        print("🔥 Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS chat_messages")
        cursor.execute("DROP TABLE IF EXISTS room_members")
        cursor.execute("DROP TABLE IF EXISTS room_invites")
        cursor.execute("DROP TABLE IF EXISTS chat_members") # Legacy table
        cursor.execute("DROP TABLE IF EXISTS chat_rooms")
        cursor.execute("DROP TABLE IF EXISTS chat_anon_id")
        
        conn.commit()
        print("✅ Tables dropped.")

        # Re-run migration logic (copy-pasted from migrate script for self-containment)
        
        # 1. chat_anon_id
        print("🔹 Creating table: chat_anon_id")
        cursor.execute("""
            CREATE TABLE chat_anon_id (
                anon_id VARCHAR(50) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # 2. chat_rooms
        print("🔹 Creating table: chat_rooms")
        cursor.execute("""
            CREATE TABLE chat_rooms (
                room_id INT AUTO_INCREMENT PRIMARY KEY,
                room_name VARCHAR(100) NOT NULL,
                room_type VARCHAR(20) NOT NULL, -- public, private, study, librarian
                created_by INT NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # 3. room_members
        print("🔹 Creating table: room_members")
        cursor.execute("""
            CREATE TABLE room_members (
                room_id INT NOT NULL,
                anon_id VARCHAR(50) NOT NULL,
                role VARCHAR(20) DEFAULT 'member', -- admin, moderator, member
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_muted BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (room_id, anon_id),
                FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
                FOREIGN KEY (anon_id) REFERENCES chat_anon_id(anon_id) ON DELETE CASCADE
            )
        """)

        # 4. room_invites
        print("🔹 Creating table: room_invites")
        cursor.execute("""
            CREATE TABLE room_invites (
                invite_code VARCHAR(50) PRIMARY KEY,
                room_id INT NOT NULL,
                created_by INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NULL,
                max_uses INT DEFAULT 1,
                uses_count INT DEFAULT 0,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # 5. chat_messages
        print("🔹 Creating table: chat_messages")
        cursor.execute("""
            CREATE TABLE chat_messages (
                message_id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                anon_id VARCHAR(50) NOT NULL,
                message_text TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (room_id) REFERENCES chat_rooms(room_id) ON DELETE CASCADE,
                FOREIGN KEY (anon_id) REFERENCES chat_anon_id(anon_id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("✅ Schema Reset & Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Reset failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_and_migrate()
