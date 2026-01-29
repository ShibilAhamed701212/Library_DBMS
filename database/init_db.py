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
    # Use absolute project root for reliability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_local = os.path.dirname(script_dir)
    schema_path = os.path.join(project_root_local, "database", "DBMS_library_db.sql")
    
    if not os.path.exists(schema_path):
        return f"❌ Schema file not found at {schema_path}", False

    output = ["🚀 Initializing database schema..."]
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        with open(schema_path, 'r') as f:
            sql_commands = f.read().split(';')
            
            for command in sql_commands:
                if command.strip():
                    try:
                        cursor.execute(command)
                    except Exception as e:
                        if "DROP" in command.upper():
                            continue
                        output.append(f"⚠️ Warning: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        output.append("✅ Database tables created successfully!")
        return "\n".join(output), True
        
    except Exception as e:
        return f"❌ Error: {e}", False

if __name__ == "__main__":
    msg, success = run_schema()
    print(msg)
