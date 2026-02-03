import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.repository.db_access import execute, fetch_all, fetch_one

def run_migration():
    print("🚀 Starting Migration: Authors and Series Support...")
    
    try:
        # 1. Create Authors Table
        execute("""
        CREATE TABLE IF NOT EXISTS authors (
            author_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            bio TEXT,
            image_url VARCHAR(255),
            nationality VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Authors table ready.")
        
        # 2. Create Series Table
        execute("""
        CREATE TABLE IF NOT EXISTS series (
            series_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Series table ready.")
        
        # 3. Add columns to books table safely
        columns = fetch_all("SHOW COLUMNS FROM books")
        current_cols = [c['Field'] for c in columns]
        
        if 'author_id' not in current_cols:
            execute("ALTER TABLE books ADD COLUMN author_id INT AFTER author")
            print("✅ Column 'author_id' added to books.")
        
        if 'series_id' not in current_cols:
            execute("ALTER TABLE books ADD COLUMN series_id INT AFTER author_id")
            print("✅ Column 'series_id' added to books.")
            
        if 'series_order' not in current_cols:
            execute("ALTER TABLE books ADD COLUMN series_order INT AFTER series_id")
            print("✅ Column 'series_order' added to books.")
            
        # 4. Add Constraints (using TRY/EXCEPT as they might exist)
        try:
            execute("ALTER TABLE books ADD CONSTRAINT fk_books_author FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE SET NULL")
            print("✅ Constraint 'fk_books_author' added.")
        except:
            print("ℹ️ Constraint 'fk_books_author' possibly already exists.")
            
        try:
            execute("ALTER TABLE books ADD CONSTRAINT fk_books_series FOREIGN KEY (series_id) REFERENCES series(series_id) ON DELETE SET NULL")
            print("✅ Constraint 'fk_books_series' added.")
        except:
            print("ℹ️ Constraint 'fk_books_series' possibly already exists.")
            
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    run_migration()
