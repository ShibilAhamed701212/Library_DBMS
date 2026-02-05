
from backend.repository.db_access import execute_query

def create_reviews_table():
    print("Creating reviews table...")
    query = """
    CREATE TABLE IF NOT EXISTS reviews (
        review_id INT AUTO_INCREMENT PRIMARY KEY,
        book_id INT NOT NULL,
        user_id INT NOT NULL,
        rating INT CHECK (rating >= 1 AND rating <= 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT fk_reviews_book
            FOREIGN KEY (book_id) REFERENCES books(book_id)
            ON DELETE CASCADE,
            
        CONSTRAINT fk_reviews_user
            FOREIGN KEY (user_id) REFERENCES users(user_id)
            ON DELETE CASCADE,
            
        UNIQUE (book_id, user_id)
    );
    """
    try:
        execute_query(query)
        print("✅ Reviews table created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    create_reviews_table()
