
import sys
import os

sys.path.append(os.getcwd())
from backend.app import create_app
from backend.repository.db_access import fetch_all, fetch_one

app = create_app()

def debug_roles():
    with app.app_context():
        # Find user 'ziya'
        ziya = fetch_one("SELECT user_id FROM users WHERE name LIKE 'ziya%'")
        if not ziya:
            print("User 'ziya' not found.")
            return

        uid = ziya['user_id']
        print(f"Found User 'ziya' (ID: {uid})")
        
        # Find channels ziya is in
        channels = fetch_all("""
            SELECT c.channel_id, c.name, c.created_by, dp.role
            FROM dm_participants dp
            JOIN channels c ON dp.channel_id = c.channel_id
            WHERE dp.user_id = %s
        """, (uid,))
        
        for c in channels:
            print(f"Channel: {c['name']} (ID: {c['channel_id']})")
            print(f"  - Created By: {c['created_by']}")
            print(f"  - Ziya's Role: {c['role']}")
            
            # Fix if needed
            if c['created_by'] != uid:
                print("  ⚠️ Creator Mismatch! Updating creator to Ziya...")
                from backend.repository.db_access import execute_query
                execute_query("UPDATE channels SET created_by = %s WHERE channel_id = %s", (uid, c['channel_id']))
                print("  ✅ Fixed Creator.")
            
            if c['role'] != 'admin':
                print("  ⚠️ Role Mismatch! Updating role to Admin...")
                from backend.repository.db_access import execute_query
                execute_query("UPDATE dm_participants SET role = 'admin' WHERE channel_id = %s AND user_id = %s", (c['channel_id'], uid))
                print("  ✅ Fixed Role.")

if __name__ == "__main__":
    debug_roles()
