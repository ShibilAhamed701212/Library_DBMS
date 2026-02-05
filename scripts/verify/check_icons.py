import sys
sys.path.append('.')
from backend.repository.db_access import fetch_all

print("🔍 Checking ALL channel icons in database...")
channels = fetch_all('SELECT channel_id, name, icon FROM channels')
for c in channels:
    icon = c.get('icon') or 'None'
    print(f"Channel {c['channel_id']}: {c['name'][:20]:20s} - Icon: {icon}")
