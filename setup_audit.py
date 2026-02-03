
from backend.repository.db_access import execute_query

def setup_audit():
    print("Setting up Audit Logs...")
    query = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        admin_id INT NOT NULL,
        action VARCHAR(100) NOT NULL,
        details TEXT DEFAULT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        CONSTRAINT fk_audit_admin FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    try:
        execute_query(query)
        print("✅ Table 'audit_logs' created successfully.")
    except Exception as e:
        print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    setup_audit()
