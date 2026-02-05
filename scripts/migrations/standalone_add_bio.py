import os
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

def migrate():
    print("🚀 Standalone migration: Adding 'bio' column to 'users' table...")
    
    # Load env
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
    
    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "user": os.getenv("DB_USER", "app_user"),
        "password": os.getenv("DB_PASSWORD", "App@123"),
        "database": os.getenv("DB_NAME", "library_db"),
        "port": int(os.getenv("DB_PORT", 3306)),
    }
    
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'bio'")
        if cursor.fetchone():
            print("ℹ️ Column 'bio' already exists.")
        else:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT AFTER email")
            conn.commit()
            print("✅ Column 'bio' added successfully!")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
