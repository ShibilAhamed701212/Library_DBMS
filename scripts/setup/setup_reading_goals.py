
from backend.repository.db_access import execute_query

def setup_reading_goals():
    print("Setting up Reading Goals table...")
    query = """
    CREATE TABLE IF NOT EXISTS reading_goals (
        goal_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        year INT NOT NULL,
        target_count INT DEFAULT 12,
        current_count INT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        UNIQUE KEY user_year (user_id, year),
        CONSTRAINT fk_goal_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(query)
    print("✅ Reading Goals table set up.")

if __name__ == "__main__":
    setup_reading_goals()
