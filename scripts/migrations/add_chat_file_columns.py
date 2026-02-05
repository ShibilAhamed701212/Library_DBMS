"""
Migration script to add file_url and sender_type columns to chat_messages table.
Run this once to fix file upload persistence.
"""
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.repository.db_access import get_connection

def migrate():
    print("🚀 Adding file_url and sender_type columns to chat_messages...")
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Add file_url column
        print("🔹 Adding file_url column...")
        cursor.execute("""
            ALTER TABLE chat_messages 
            ADD COLUMN IF NOT EXISTS file_url VARCHAR(500) NULL
        """)
        
        # Add sender_type column
        print("🔹 Adding sender_type column...")
        cursor.execute("""
            ALTER TABLE chat_messages 
            ADD COLUMN IF NOT EXISTS sender_type VARCHAR(20) DEFAULT 'user'
        """)
        
        # Add is_edited column
        print("🔹 Adding is_edited column...")
        cursor.execute("""
            ALTER TABLE chat_messages 
            ADD COLUMN IF NOT EXISTS is_edited BOOLEAN DEFAULT FALSE
        """)

        conn.commit()
        print("✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        
        # Try alternative syntax if IF NOT EXISTS fails (MySQL 5.x)
        print("🔄 Retrying with alternative syntax...")
        try:
            # Check if columns exist first
            cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'file_url'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN file_url VARCHAR(500) NULL")
                print("✅ Added file_url column")
            
            cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'sender_type'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN sender_type VARCHAR(20) DEFAULT 'user'")
                print("✅ Added sender_type column")
            
            cursor.execute("SHOW COLUMNS FROM chat_messages LIKE 'is_edited'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE chat_messages ADD COLUMN is_edited BOOLEAN DEFAULT FALSE")
                print("✅ Added is_edited column")
            
            conn.commit()
            print("✅ Migration completed with alternative method!")
        except Exception as e2:
            conn.rollback()
            print(f"❌ Alternative migration also failed: {e2}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
