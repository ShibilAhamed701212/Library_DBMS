import sys
sys.path.append('.')
from backend.repository.db_access import execute

print("🛠️ Fixing Channel 2 Creator...")
# Set creator to Ziya (5) if currently NULL
execute("UPDATE channels SET created_by = 5 WHERE channel_id = 2 AND created_by IS NULL")
print("✅ Updated created_by for Channel 2")
