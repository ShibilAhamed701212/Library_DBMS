
import sys
import os
sys.path.append(os.getcwd())
from backend.repository.db_access import fetch_all

print("🔍 Checking 'dm_participants' table schema...")
try:
    cols = fetch_all("DESCRIBE dm_participants")
    for c in cols:
        print(f" - {c['Field']} ({c['Type']})")
except Exception as e:
    print(f"❌ Error: {e}")
