"""
Migration script to add reply_to_id column to chat_messages table.
"""
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.repository.db_access import get_connection

def migrate():
    print("🚀 Adding reply_to_id column to chat_messages...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if columns exist first (MySQL 5.x doesn't support ADD COLUMN IF NOT EXISTS reliably)
        cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'reply_to_id'")
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE chat_messages 
                ADD COLUMN reply_to_id INT NULL,
                ADD CONSTRAINT fk_reply_to FOREIGN KEY (reply_to_id) REFERENCES chat_messages(message_id) ON DELETE SET NULL
            """)
            print("✅ Added reply_to_id column and foreign key")
        else:
            print("ℹ️ reply_to_id column already exists")

        conn.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
