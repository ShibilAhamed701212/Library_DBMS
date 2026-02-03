
from backend.repository.db_access import execute

def setup_social_features():
    print("🚀 Initializing Social Features...")
    
    # 1. Add is_public column to users table
    try:
        execute("ALTER TABLE users ADD COLUMN is_public BOOLEAN DEFAULT 0")
        print("✅ Added 'is_public' column to 'users' table.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ 'is_public' column already exists.")
        else:
            print(f"❌ Error adding 'is_public': {e}")

    # 2. (Optional) Create a review_likes table for future engagement
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS review_likes (
                like_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                review_id INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, review_id)
            )
        """)
        print("✅ Created 'review_likes' table.")
    except Exception as e:
        print(f"❌ Error creating 'review_likes': {e}")

if __name__ == "__main__":
    setup_social_features()
