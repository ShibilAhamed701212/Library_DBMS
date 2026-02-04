import sys
sys.path.append('.')
from backend.repository.db_access import execute

print("🛠️ Adding role column to dm_participants...")
try:
    execute("ALTER TABLE dm_participants ADD COLUMN role VARCHAR(20) DEFAULT 'member'")
    print("✅ Added 'role' column.")
except Exception as e:
    print(f"⚠️ Could not add column (maybe exists): {e}")

# Verify
from backend.repository.db_access import fetch_all
try:
    cols = fetch_all("SHOW COLUMNS FROM dm_participants")
    print(f"Columns: {[c['Field'] for c in cols]}")
    # Note: fetch_all returns dicts, keys might be different depending on connector
except Exception as e:
    print(f"⚠️ Could not show columns: {e}")
