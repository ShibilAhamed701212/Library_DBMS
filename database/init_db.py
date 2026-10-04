import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.config.db import get_connection

def run_schema():
    """
    Reads database/schema.sql (the consolidated, idempotent schema) and
    executes it to create all tables and reference data.
    """
    # Use absolute project root for reliability
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root_local = os.path.dirname(script_dir)
    schema_path = os.path.join(project_root_local, "database", "schema.sql")
    
    if not os.path.exists(schema_path):
        return f"❌ Schema file not found at {schema_path}", False

    output = ["🚀 Initializing database schema..."]
    
    try:
        conn = get_connection()
        # Use buffered cursor so results are fetched and we can safely run subsequent statements
        cursor = conn.cursor(buffered=True)
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            raw_sql = f.read()
            # Split, filter admin/verification statements, and re-join for multi execution
            parts = [p.strip() for p in raw_sql.split(';')]
            safe_cmds = []
            for cmd in parts:
                if not cmd:
                    continue
                up = cmd.upper()
                if any(k in up for k in (
                    'CREATE USER', 'DROP USER', 'GRANT ', 'FLUSH PRIVILEGES', 'SHOW TABLES', 'DESCRIBE '
                )):
                    continue
                safe_cmds.append(cmd)

            # Execute each statement individually
            failures = 0
            for cmd in safe_cmds:
                cmd = cmd.strip()
                if not cmd:
                    continue
                try:
                    cursor.execute(cmd)
                    # Try to fetch results if any
                    try:
                        while cursor.nextset():
                            pass
                    except Exception:
                        pass
                except Exception as e:
                    # Capture and continue so every problem is reported at once
                    failures += 1
                    sql_lines = [l for l in cmd.splitlines() if l.strip() and not l.strip().startswith('--')]
                    first_line = (sql_lines[0] if sql_lines else cmd)[:120]
                    output.append(f"⚠️ Warning: {e} | SQL: {first_line}")
        
        conn.commit()
        cursor.close()
        conn.close()
        if failures:
            output.append(f"❌ {failures} schema statement(s) failed; see warnings above.")
            return "\n".join(output), False
        output.append("✅ Database tables created successfully!")
        return "\n".join(output), True
        
    except Exception as e:
        return f"❌ Error: {e}", False

if __name__ == "__main__":
    msg, success = run_schema()
    print(msg)
    sys.exit(0 if success else 1)
