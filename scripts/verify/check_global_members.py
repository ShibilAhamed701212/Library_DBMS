import sys
sys.path.append('.')
from backend.repository.db_access import fetch_all, fetch_one

print("🔍 Checking Channel 1 (Global)...")
channel = fetch_one("SELECT * FROM channels WHERE channel_id = 1")
print(f"Channel 1: {channel}")

print("\n🔍 Checking participants in Channel 1...")
parts = fetch_all("SELECT COUNT(*) as count FROM dm_participants WHERE channel_id = 1")
print(f"Participant Count: {parts[0]['count']}")

print("\n🔍 Checking Total Users...")
users = fetch_all("SELECT COUNT(*) as count FROM users")
print(f"Total Users: {users[0]['count']}")
