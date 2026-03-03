import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def check_schema():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor(dictionary=True)
        
        tables = ['books', 'users', 'issues']
        for table in tables:
            print(f"\n--- {table} ---")
            cursor.execute(f"DESCRIBE {table}")
            for row in cursor.fetchall():
                print(row)
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
