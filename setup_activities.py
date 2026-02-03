
from backend.repository.db_access import execute_query

def setup_activities():
    print("Setting up User Activities table...")
    query = """
    CREATE TABLE IF NOT EXISTS user_activities (
        activity_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        activity_type VARCHAR(50) NOT NULL,
        description TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_act_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(query)
    print("✅ User Activities table set up.")

if __name__ == "__main__":
    setup_activities()
