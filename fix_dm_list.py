
import os
import sys
sys.path.append(os.getcwd())
try:
    from backend.repository.db_access import execute, fetch_all, fetch_one
except ImportError:
    from backend.repository.db_access import execute, fetch_all, fetch_one

def fix():
    print("🚀 Fixing DM List from Message History...")
    
    # 1. Get DM Channels
    dms = fetch_all("SELECT channel_id FROM channels WHERE guild_id IS NULL")
    if not dms:
        print("No DM channels found.")
        return

    dm_ids = [str(d['channel_id']) for d in dms]
    ids_str = ",".join(dm_ids)
    
    # 2. Find participants based on messages
    # Join with chat_anon_id to get real user_id
    query = f"""
        SELECT DISTINCT m.channel_id, ca.user_id
        FROM chat_messages m
        JOIN chat_anon_id ca ON m.anon_id = ca.anon_id
        WHERE m.channel_id IN ({ids_str})
    """
    
    rows = fetch_all(query)
    print(f"Found {len(rows)} active participants in DMs.")
    
    count = 0
    for r in rows:
        try:
            execute("INSERT IGNORE INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (r['channel_id'], r['user_id']))
            count += 1
        except Exception as e:
            print(e)
            
    print(f"✅ Restored {count} DM entries.")

if __name__ == "__main__":
    fix()
