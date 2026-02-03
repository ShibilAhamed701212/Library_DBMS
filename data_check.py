
import os
import sys
sys.path.append(os.getcwd())
from backend.repository.db_access import fetch_all

try:
    print("=== ROOM MEMBERS (Legacy) ===")
    rows = fetch_all("SELECT * FROM room_members LIMIT 5")
    for r in rows:
        print(r)

    print("\n=== DM PARTICIPANTS (New) ===")
    rows = fetch_all("SELECT * FROM dm_participants LIMIT 5")
    for r in rows:
        print(r)
        
    print("\n=== CHANNELS (DMs) ===")
    rows = fetch_all("SELECT channel_id, name, guild_id FROM channels WHERE guild_id IS NULL LIMIT 5")
    for r in rows:
        print(r)

except Exception as e:
    print(f"Error: {e}")
