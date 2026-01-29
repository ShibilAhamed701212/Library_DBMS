import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing exact db.py connection logic...")
host = os.getenv("DB_HOST", "127.0.0.1")
ssl_disabled = False if host != "127.0.0.1" else True

print(f"Host: {host}")
print(f"SSL Disabled: {ssl_disabled}")

try:
    conn = mysql.connector.connect(
        host=host,
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "app_user"),
        password=os.getenv("DB_PASSWORD", "App@123"),
        database=os.getenv("DB_NAME", "library_db"),
        ssl_disabled=ssl_disabled,
        auth_plugin="mysql_native_password"
    )
    print("✅ Connection SUCCESS!")
    conn.close()
except Exception as e:
    print(f"❌ Connection FAILED: {type(e).__name__}: {e}")
    if hasattr(e, 'msg'):
        print(f"Error Msg field exists: {e.msg}")
    else:
        print("Error Msg field DOES NOT EXIST - this is the source of the AttributeError!")
