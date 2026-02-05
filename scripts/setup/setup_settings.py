
from backend.repository.db_access import execute_query

def setup_settings():
    print("Setting up Settings table...")
    query = """
    CREATE TABLE IF NOT EXISTS settings (
        setting_key VARCHAR(50) PRIMARY KEY,
        setting_value VARCHAR(255) NOT NULL
    );
    """
    execute_query(query)
    
    # Initialize maintenance_mode if not exists
    execute_query("INSERT IGNORE INTO settings (setting_key, setting_value) VALUES ('maintenance_mode', 'false')")
    print("✅ Settings table set up.")

if __name__ == "__main__":
    setup_settings()
