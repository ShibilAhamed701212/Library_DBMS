
from backend.repository.db_access import execute_query

def add_fine_tracking():
    print("Updating issues table for fine tracking...")
    
    # Check if column exists (naive check via trying to add it, ignoring error)
    # Better: Query information_schema, but ALTER IGNORE is not supported in all MySQL.
    # We'll rely on "Duplicate column name" error handling or just use specific check.
    
    query = """
    ALTER TABLE issues
    ADD COLUMN fine_paid BOOLEAN DEFAULT FALSE;
    """
    
    try:
        execute_query(query)
        print("✅ Column 'fine_paid' added successfully.")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ️ Column 'fine_paid' already exists. Skipping.")
        else:
            print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_fine_tracking()
