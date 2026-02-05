
import sys
import os

# Add project root
sys.path.append(os.getcwd())

from backend.app import create_app
from backend.repository.db_access import execute_query, fetch_all

app = create_app()

def repair_admins():
    with app.app_context():
        print("--- Repairing Channel Admins ---")
        
        # 1. Fetch all channels with a creator
        channels = fetch_all("SELECT channel_id, name, created_by, is_private, guild_id FROM channels WHERE created_by IS NOT NULL")
        
        fixed_count = 0
        
        for c in channels:
            cid = c['channel_id']
            creator = c['created_by']
            
            # We only care about ensuring they are in dm_participants if it's a private group/DM style channel
            # Guild channels rely on guild_members usually, but let's check how the app handles it.
            # Based on code, 'dm_participants' is used for private channels (guild_id IS NULL OR is_private=1).
            
            if c['guild_id'] is None or c['is_private']:
                # Check if in participants
                exists = fetch_all("SELECT * FROM dm_participants WHERE channel_id = %s AND user_id = %s", (cid, creator))
                
                if not exists:
                    print(f"🛠️ Fixing Channel '{c['name']}' (ID: {cid}). Adding Creator {creator} as Admin.")
                    execute_query("""
                        INSERT INTO dm_participants (channel_id, user_id, role)
                        VALUES (%s, %s, 'admin')
                    """, (cid, creator))
                    fixed_count += 1
                else:
                    # Optional: Ensure they are admin?
                    current_role = exists[0]['role']
                    if current_role != 'admin':
                        print(f"⚠️ Updating Role for Channel '{c['name']}' (ID: {cid}). User {creator} -> Admin.")
                        execute_query("UPDATE dm_participants SET role = 'admin' WHERE channel_id = %s AND user_id = %s", (cid, creator))
                        fixed_count += 1
                        
        print(f"\n✅ Repair Complete. Fixed {fixed_count} channels.")

if __name__ == "__main__":
    try:
        repair_admins()
    except Exception as e:
        print(f"❌ Error: {e}")
