import os
import sys

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from backend.services.guild_service import get_my_guilds, get_guild_details, create_guild
from backend.services.channel_service import create_channel, save_message
from backend.repository.db_access import fetch_one

def test_logic():
    print("🧪 Testing Backend Services...")
    
    # 1. Get a test user
    user = fetch_one("SELECT user_id, name FROM users LIMIT 1")
    if not user:
        print("❌ No users found.")
        return
    user_id = user['user_id']
    print(f"👤 Test User: {user['name']} (ID: {user_id})")
    
    # 2. List Guilds
    try:
        guilds = get_my_guilds(user_id)
        print(f"✅ get_my_guilds returned {len(guilds)} guilds.")
    except Exception as e:
        print(f"❌ get_my_guilds failed: {e}")
        return

    # 3. Create Guild if none
    if not guilds:
        print("   -> Creating test guild...")
        try:
            gid = create_guild(user_id, "Test Server")
            print(f"✅ Created Guild ID: {gid}")
            guilds = [{'guild_id': gid, 'name': "Test Server"}]
        except Exception as e:
            print(f"❌ create_guild failed: {e}")
            return
            
    # 4. Get Details
    guild_id = guilds[0]['guild_id']
    try:
        details = get_guild_details(guild_id)
        print("✅ get_guild_details success.")
        print(f"   Structure: {list(details.keys())}")
        print(f"   Hierarchy Nodes: {len(details['hierarchy'])}")
    except Exception as e:
        print(f"❌ get_guild_details failed: {e}")
        return

    print("🎉 Backend logic seems fine!")

if __name__ == "__main__":
    test_logic()
