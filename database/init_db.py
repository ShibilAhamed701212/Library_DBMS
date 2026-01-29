import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.config.db import get_connection

def run_schema():
    """
    Reads the SQL schema file and executes it to create tables.
    """
    schema_path = os.path.join(project_root, "database", "DBMS_library_db.sql")
    
    if not os.path.exists(schema_path):
        print(f"❌ Schema file not found at {schema_path}")
        return

    print("🚀 Initializing database schema...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        with open(schema_path, 'r') as f:
            # Split by semicolon to get individual queries
            # Note: This is a simple parser and might need adjustments for complex SQL
            sql_commands = f.read().split(';')
            
            for command in sql_commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        # Some commands like DROP USER might fail if user doesn't exist
                        # We ignore these during initialization
                        if "DROP" in command.upper():
                            continue
                        print(f"⚠️ Warning during SQL execution: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error during schema initialization: {e}")

if __name__ == "__main__":
    run_schema()
