
from backend.repository.db_access import execute_query

def setup_category_fines():
    print("Setting up Category Fines table...")
    query = """
    CREATE TABLE IF NOT EXISTS category_fines (
        category VARCHAR(100) PRIMARY KEY,
        daily_rate DECIMAL(10, 2) DEFAULT 10.00
    );
    """
    execute_query(query)
    
    # Seed some defaults
    defaults = [
        ('General', 5.00),
        ('Science', 10.00),
        ('Fiction', 7.00),
        ('Reference', 20.00),
        ('History', 8.00)
    ]
    for cat, rate in defaults:
        execute_query("INSERT IGNORE INTO category_fines (category, daily_rate) VALUES (%s, %s)", (cat, rate))
        
    print("✅ Category Fines table set up.")

if __name__ == "__main__":
    setup_category_fines()
