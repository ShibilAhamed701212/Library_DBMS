import sys
sys.path.append('.')
from backend.repository.db_access import fetch_all, fetch_one

print("🔍 Checking Channel 1 (Global)...")
c1 = fetch_one("SELECT * FROM channels WHERE channel_id = 1")
print(f"Channel 1: created_by={c1.get('created_by')}")

members1 = fetch_all("""
    SELECT u.user_id, u.name, u.role 
    FROM dm_participants dp
    JOIN users u ON dp.user_id = u.user_id
    WHERE dp.channel_id = 1
""")
print(f"Members in Ch 1: {members1}")

print("\n🔍 Checking Channel 2 (Group)...")
c2 = fetch_one("SELECT * FROM channels WHERE channel_id = 2")
if c2:
    print(f"Channel 2: created_by={c2.get('created_by')}")
    members2 = fetch_all("""
        SELECT u.user_id, u.name, u.role 
        FROM dm_participants dp
        JOIN users u ON dp.user_id = u.user_id
        WHERE dp.channel_id = 2
    """)
    print(f"Members in Ch 2: {members2}")
else:
    print("Channel 2 not found")
