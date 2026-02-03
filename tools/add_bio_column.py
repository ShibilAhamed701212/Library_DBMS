import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.repository.db_access import execute_query

def migrate():
    print("🚀 Adding 'bio' column to 'users' table...")
    try:
        # Check if column exists first (to be idempotent)
        # However, for MySQL/MariaDB, we can just use ALTER TABLE and catch the error or use information_schema
        execute_query("""
            ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT AFTER email;
        """)
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
