import sys
sys.path.append('.')
from backend.repository.db_access import fetch_one

print("🔍 Checking Channel 2 Type...")
c = fetch_one("SELECT * FROM channels WHERE channel_id = 2")
if c:
    print(f"Channel 2: type='{c.get('type')}', is_private={c.get('is_private')}, name='{c.get('name')}'")
else:
    print("Channel 2 not found")
