
from backend.repository.db_access import execute_query

def setup_wishlist():
    print("Setting up Wishlist...")
    query = """
    CREATE TABLE IF NOT EXISTS wishlist (
        wishlist_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(user_id, book_id),
        CONSTRAINT fk_wish_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT fk_wish_book FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
    );
    """
    try:
        execute_query(query)
        print("✅ Table 'wishlist' created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    setup_wishlist()
