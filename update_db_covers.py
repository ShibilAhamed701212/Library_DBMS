from backend.config.db import get_connection

def add_cover_column():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        print("Checking if cover_url column exists...")
        cursor.execute("SHOW COLUMNS FROM books LIKE 'cover_url'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding cover_url column...")
            cursor.execute("ALTER TABLE books ADD COLUMN cover_url VARCHAR(500) NULL AFTER pdf_src")
            print("✅ cover_url column added.")
        else:
            print("ℹ️ cover_url column already exists.")
            
        print("Checking if description column exists (needed for hover details)...")
        cursor.execute("SHOW COLUMNS FROM books LIKE 'description'")
        result = cursor.fetchone()
        
        if not result:
             print("Adding description column...")
             # Using TEXT for long descriptions
             cursor.execute("ALTER TABLE books ADD COLUMN description TEXT NULL AFTER category")
             print("✅ description column added.")
        else:
             print("ℹ️ description column already exists.")
             
        conn.commit()
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_cover_column()
