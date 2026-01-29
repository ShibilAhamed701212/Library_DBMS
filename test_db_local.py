import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Testing Local MySQL Connection...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"User: {os.getenv('DB_USER')}")
print(f"DB: {os.getenv('DB_NAME')}")

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "app_user"),
        password=os.getenv("DB_PASSWORD", "App@123"),
        database=os.getenv("DB_NAME", "library_db"),
        auth_plugin="mysql_native_password"
    )
    print("✅ Connection SUCCESS!")
    conn.close()
except Exception as e:
    print(f"❌ Connection FAILED: {e}")
    print("\n💡 Tip: Check if 'MySQL' service is running in your Windows Services (services.msc).")
