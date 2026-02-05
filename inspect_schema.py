from backend.config.db import get_connection

def inspect_table(table_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        print(f"\n--- {table_name} ---")
        for col in columns:
            print(f"{col['Field']} ({col['Type']})")
    except Exception as e:
        print(f"Error describing {table_name}: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    inspect_table('users')
    inspect_table('reading_goals')
    inspect_table('books')
