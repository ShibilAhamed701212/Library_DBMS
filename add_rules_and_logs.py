
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.app import create_app
from backend.repository.db_access import execute_query, fetch_one

app = create_app()

def migrate_schema():
    with app.app_context():
        print("--- Migrating Schema for Rules & Logs ---")
        
        # 1. Add RULES column to channels
        print("Checking 'channels' table...")
        col_check = fetch_one("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_schema = DATABASE() 
            AND table_name = 'channels' 
            AND column_name = 'rules'
        """)
        
        if col_check and col_check['count'] == 0:
            print("Adding 'rules' column to channels...")
            execute_query("ALTER TABLE channels ADD COLUMN rules TEXT DEFAULT NULL")
            print("✅ Added 'rules' column.")
        else:
            print("ℹ️ 'rules' column already exists.")

        # 2. Create AUDIT_LOGS table
        print("\nChecking 'audit_logs' table...")
        table_check = fetch_one("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'audit_logs'
        """)
        
        if table_check and table_check['count'] == 0:
            print("Creating 'audit_logs' table...")
            execute_query("""
                CREATE TABLE audit_logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id INT NOT NULL,
                    user_id INT NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    details VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (channel_id) REFERENCES channels(channel_id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            print("✅ Created 'audit_logs' table.")
        else:
            print("ℹ️ 'audit_logs' table already exists.")

if __name__ == "__main__":
    try:
        migrate_schema()
        print("\nMigration Complete!")
    except Exception as e:
        print(f"\n❌ Migration Failed: {e}")
