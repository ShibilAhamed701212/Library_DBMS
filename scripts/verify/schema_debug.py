
import sys
import os

# Adjust path so backend imports work
sys.path.append(os.getcwd())

from backend.repository.db_access import fetch_all

print("🔍 Checking 'channels' table schema...")
try:
    cols = fetch_all("DESCRIBE channels")
    for c in cols:
        print(f" - {c['Field']} ({c['Type']})")
except Exception as e:
    print(f"❌ Error: {e}")
