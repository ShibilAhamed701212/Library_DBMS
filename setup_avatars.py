
from backend.repository.db_access import execute_query
import os

def setup_avatars():
    print("Setting up profile pictures...")
    
    # 1. Update Database
    query = """
    ALTER TABLE users
    ADD COLUMN profile_pic VARCHAR(255) DEFAULT NULL;
    """
    
    try:
        execute_query(query)
        print("✅ Column 'profile_pic' added successfully.")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ️ Column 'profile_pic' already exists. Skipping.")
        else:
            print(f"❌ Error adding column: {e}")

    # 2. Create Uploads Directory
    # Assuming run from root, backend/static/uploads/avatars
    # Flask static folder is usually 'backend/static' or just 'static' depending on config.
    # Looking at project structure, 'templates' and 'backend' are at root.
    # Usually Flask apps serve static from a 'static' folder.
    # Let's check where 'static' is.
    
    # Based on previous file views, I haven't seen a 'static' folder at root.
    # But usually it's `backend/static` or `static`.
    # I'll create `static/uploads/avatars` at root specific to run.py context.
    
    upload_path = os.path.join("static", "uploads", "avatars")
    os.makedirs(upload_path, exist_ok=True)
    print(f"✅ Created directory: {upload_path}")

if __name__ == "__main__":
    setup_avatars()
