
from backend.repository.db_access import execute_query

def setup_waitlist():
    print("Creating reservations table...")
    query = """
    CREATE TABLE IF NOT EXISTS reservations (
        reservation_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        book_id INT NOT NULL,
        reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status ENUM('active', 'fulfilled', 'cancelled') DEFAULT 'active',
        
        CONSTRAINT fk_res_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
        CONSTRAINT fk_res_book FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
        UNIQUE(user_id, book_id) -- User can only reserve a book once
    );
    """
    try:
        execute_query(query)
        print("✅ Reservations table created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    setup_waitlist()
