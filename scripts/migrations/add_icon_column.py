
import sys
import os
sys.path.append(os.getcwd())
from backend.repository.db_access import execute

print("🔧 Adding icon column to channels table...")
try:
    execute("ALTER TABLE channels ADD COLUMN icon VARCHAR(255) DEFAULT NULL")
    print("✅ Icon column added successfully!")
except Exception as e:
    if 'Duplicate column' in str(e):
        print("ℹ️ Icon column already exists.")
    else:
        print(f"❌ Error: {e}")
