import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from backend.repository.db_access import execute, fetch_one, fetch_all

def fix_membership():
    print("🔧 Fixing Legacy Guild Membership...")
    
    # 1. Find the Legacy Guild
    guild = fetch_one("SELECT guild_id, name FROM guilds WHERE name = 'Legacy Community' OR name = 'Public Community' LIMIT 1")
    if not guild:
        print("❌ Legacy Guild not found! Did migration run?")
        return
    
    guild_id = guild['guild_id']
    print(f"✅ Found Guild: {guild['name']} (ID: {guild_id})")
    
    # 2. Get All Users
    users = fetch_all("SELECT user_id, name FROM users")
    print(f"👥 Checking {len(users)} users...")
    
    count = 0
    for u in users:
        uid = u['user_id']
        # Check if member
        exists = fetch_one("SELECT * FROM guild_members WHERE guild_id = %s AND user_id = %s", (guild_id, uid))
        if not exists:
            execute("INSERT INTO guild_members (guild_id, user_id) VALUES (%s, %s)", (guild_id, uid))
            print(f"   + Added {u['name']} (ID: {uid}) to guild.")
            count += 1
            
    print(f"🎉 Added {count} missing members.")

if __name__ == "__main__":
    fix_membership()
