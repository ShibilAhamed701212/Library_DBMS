
from backend.repository.db_access import execute, fetch_all

def setup_author_series():
    print("🚀 Initializing Author & Series Management...")
    
    # 1. Create authors table
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS authors (
                author_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) UNIQUE NOT NULL,
                bio TEXT,
                photo_src VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created 'authors' table.")
    except Exception as e:
        print(f"❌ Error creating 'authors': {e}")

    # 2. Create series table
    try:
        execute("""
            CREATE TABLE IF NOT EXISTS series (
                series_id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created 'series' table.")
    except Exception as e:
        print(f"❌ Error creating 'series': {e}")

    # 3. Add foreign keys to books table
    try:
        execute("ALTER TABLE books ADD COLUMN author_id INT")
        execute("ALTER TABLE books ADD COLUMN series_id INT")
        execute("ALTER TABLE books ADD COLUMN series_order INT")
        print("✅ Added relational columns to 'books' table.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ Relational columns already exist in 'books'.")
        else:
            print(f"❌ Error updating 'books': {e}")

    # 4. Data Migration: Populate authors table and link books
    try:
        print("🚚 Migrating existing author data...")
        books = fetch_all("SELECT DISTINCT author FROM books WHERE author IS NOT NULL")
        for b in books:
            author_name = b['author']
            # Insert author if not exists
            execute("INSERT IGNORE INTO authors (name) VALUES (%s)", (author_name,))
            # Link book to new author_id
            execute("""
                UPDATE books b
                JOIN authors a ON b.author = a.name
                SET b.author_id = a.author_id
                WHERE b.author = %s
            """, (author_name,))
        print(f"✅ Migrated {len(books)} unique authors.")
    except Exception as e:
        print(f"❌ Error migrating data: {e}")

if __name__ == "__main__":
    setup_author_series()
