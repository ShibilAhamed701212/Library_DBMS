import os
import mysql.connector
from pathlib import Path
from dotenv import load_dotenv

def migrate():
    print("🚀 Standalone migration: Creating 'friend_requests' table...")
    
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
        
        # Create friend_requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS friend_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                receiver_id INT NOT NULL,
                status ENUM('pending', 'accepted', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY uq_friend_request (sender_id, receiver_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        
        conn.commit()
        print("✅ Table 'friend_requests' checked/created successfully!")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate()
