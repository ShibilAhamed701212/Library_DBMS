
import os
import sys
sys.path.append(os.getcwd())
try:
    from backend.repository.db_access import execute, fetch_all, fetch_one
except ImportError:
    from backend.repository.db_access import execute, fetch_all, fetch_one

def migrate():
    print("🚀 Migrating Room Members (V2)...")
    
    # 1. Fetch Legacy Rooms to build a Map
    legacy_rooms = fetch_all("SELECT * FROM chat_rooms")
    room_map = {} # old_id -> new_id
    
    for room in legacy_rooms:
        # fuzzy match by name? or exact?
        # The migration script used room['room_name'] or 'channel'
        name = room['room_name'] or 'channel'
        
        # Find corresponding channel
        # We assume most recent one is the migrated one if multiple
        chan = fetch_one("SELECT channel_id FROM channels WHERE name = %s ORDER BY created_at DESC LIMIT 1", (name,))
        if chan:
            room_map[room['room_id']] = chan['channel_id']
            print(f"Map: {room['room_id']} ({name}) -> {chan['channel_id']}")
        else:
            print(f"Warning: No match for room {room['room_id']} ({name})")
            
    # 2. Migrate Members
    members = fetch_all("""
        SELECT rm.room_id, ca.user_id
        FROM room_members rm
        JOIN chat_anon_id ca ON rm.anon_id = ca.anon_id
    """)
    
    count = 0
    for m in members:
        old_id = m['room_id']
        if old_id not in room_map:
            continue
            
        new_id = room_map[old_id]
        user_id = m['user_id']
        
        # Insert
        try:
             # Check type
            chan = fetch_one("SELECT guild_id FROM channels WHERE channel_id = %s", (new_id,))
            if chan and chan['guild_id'] is None:
                execute("INSERT IGNORE INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (new_id, user_id))
                count += 1
            elif chan:
                 execute("INSERT IGNORE INTO guild_members (guild_id, user_id) VALUES (%s, %s)", (chan['guild_id'], user_id))
        except Exception as e:
            print(e)
            
    print(f"✅ Migrated {count} DM entries.")

if __name__ == "__main__":
    migrate()
