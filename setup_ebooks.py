
from backend.repository.db_access import execute_query
import os

def setup_ebooks():
    print("Setting up Digital Library...")
    
    # 1. Update Database
    query = """
    ALTER TABLE books
    ADD COLUMN pdf_src VARCHAR(255) DEFAULT NULL;
    """
    
    try:
        execute_query(query)
        print("✅ Column 'pdf_src' added successfully.")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ️ Column 'pdf_src' already exists. Skipping.")
        else:
            print(f"❌ Error adding column: {e}")

    # 2. Create Uploads Directory
    upload_path = os.path.join("static", "uploads", "ebooks")
    os.makedirs(upload_path, exist_ok=True)
    print(f"✅ Created directory: {upload_path}")

if __name__ == "__main__":
    setup_ebooks()
