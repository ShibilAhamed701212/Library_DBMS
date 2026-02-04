
import sys
import os

sys.path.append(os.getcwd())
from backend.app import create_app
from backend.repository.db_access import execute, fetch_one, fetch_all

app = create_app()

SENDER_ID = 1
TARGET_ID = 10 

def run_debug():
    with app.app_context():
        print(f"--- Debugging DM Creation (Sender: {SENDER_ID}, Target: {TARGET_ID}) ---")
        
        # 1. Clean previous DMs
        print("\n1. Cleaning previous DMs...")
        # Find DM channels with both participants
        dms = fetch_all("""
            SELECT c.channel_id FROM channels c
            JOIN dm_participants dp1 ON c.channel_id = dp1.channel_id
            JOIN dm_participants dp2 ON c.channel_id = dp2.channel_id
            WHERE dp1.user_id = %s AND dp2.user_id = %s AND c.name = 'DM'
        """, (SENDER_ID, TARGET_ID))
        
        for dm in dms:
            cid = dm['channel_id']
            print(f"   Deleting old DM Channel {cid}...")
            execute("DELETE FROM dm_participants WHERE channel_id = %s", (cid,))
            execute("DELETE FROM channels WHERE channel_id = %s", (cid,))
            
        # 2. Create Invite
        print("\n2. Creating Invite...")
        execute("DELETE FROM chat_invitations WHERE sender_id = %s AND target_user_id = %s", (SENDER_ID, TARGET_ID))
        
        inv_id = 999999
        execute("""
            INSERT INTO chat_invitations (invite_id, sender_id, target_user_id, type, status)
            VALUES (%s, %s, %s, 'DM', 'pending')
        """, (inv_id, SENDER_ID, TARGET_ID))
        print(f"   Created Invite {inv_id}")
        
        # 3. Simulate Accept Logic (Backend Logic)
        print("\n3. Simulating Acceptance...")
        invite = fetch_one("SELECT * FROM chat_invitations WHERE invite_id = %s", (inv_id,))
        if not invite:
            print("   ❌ Invite not found!")
            return

        from backend.services.channel_service import create_dm
        cid = create_dm(invite['sender_id'], invite['target_user_id'])
        print(f"   ✅ Created DM Channel ID: {cid}")
        
        # 4. Verify Database Records
        print("\n4. Verifying Database...")
        chan = fetch_one("SELECT * FROM channels WHERE channel_id = %s", (cid,))
        print(f"   Channel: {chan['name']} | Type: {chan['type']} | Private: {chan['is_private']} | Guild: {chan['guild_id']}")
        
        parts = fetch_all("SELECT user_id, role FROM dm_participants WHERE channel_id = %s", (cid,))
        print(f"   Participants: {len(parts)}")
        for p in parts:
            print(f"    - User {p['user_id']} ({p['role']})")
            
        # 5. Verify get_my_dms
        print("\n5. Testing get_my_dms for Target User...")
        from backend.services.channel_service import get_my_dms
        dms = get_my_dms(TARGET_ID)
        found = False
        for d in dms:
            if d['channel_id'] == cid:
                found = True
                print(f"   ✅ Found in get_my_dms! Name='{d['name']}'")
        
        if not found:
            print("   ❌ NOT FOUND in get_my_dms!")
            print("   Dumping DMs found:")
            for d in dms:
                print(f"    - ID: {d['channel_id']} | Name: {d['name']}")

if __name__ == "__main__":
    run_debug()
