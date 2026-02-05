
from backend.repository.db_access import execute_query

def setup_membership_tiers():
    print("Setting up Membership Tiers...")
    
    # 1. Add tier column to users if it doesn't exist
    # Note: MySQL doesn't have IF NOT EXISTS for columns easily in a single script without a procedure, 
    # but we can try-except or just run it if we know the schema.
    try:
        execute_query("ALTER TABLE users ADD COLUMN tier ENUM('Silver', 'Gold', 'Platinum') DEFAULT 'Silver'")
        print("✅ Added 'tier' column to users table.")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("ℹ️ 'tier' column already exists in users table.")
        else:
            print(f"⚠️ Error adding tier column: {e}")

    # 2. Create membership_configs table
    q_table = """
    CREATE TABLE IF NOT EXISTS membership_configs (
        tier ENUM('Silver', 'Gold', 'Platinum') PRIMARY KEY,
        max_books INT NOT NULL,
        loan_days INT NOT NULL
    );
    """
    execute_query(q_table)
    
    # 3. Seed configurations
    configs = [
        ('Silver', 3, 14),
        ('Gold', 7, 30),
        ('Platinum', 999, 60)
    ]
    
    for tier, max_books, loan_days in configs:
        execute_query("""
            INSERT INTO membership_configs (tier, max_books, loan_days) 
            VALUES (%s, %s, %s) 
            ON DUPLICATE KEY UPDATE max_books=%s, loan_days=%s
        """, (tier, max_books, loan_days, max_books, loan_days))
        
    print("✅ Membership configurations seeded.")

if __name__ == "__main__":
    setup_membership_tiers()
