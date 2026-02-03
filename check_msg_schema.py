
import os
import sys
sys.path.append(os.getcwd())
try:
    from backend.config.db import get_connection
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DESCRIBE chat_messages")
    rows = cursor.fetchall()
    for r in rows:
        print(f"{r['Field']}: {r['Type']} Null={r['Null']} Default={r['Default']}")
except Exception as e:
    print(e)
