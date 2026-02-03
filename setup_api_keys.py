
from backend.repository.db_access import execute_query

def setup_api_keys():
    print("Setting up API Keys table...")
    query = """
    CREATE TABLE IF NOT EXISTS api_keys (
        key_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        api_key VARCHAR(64) UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_api_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(query)
    print("✅ API Keys table set up.")

if __name__ == "__main__":
    setup_api_keys()
