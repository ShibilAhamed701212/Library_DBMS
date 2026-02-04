
import sys
import os

sys.path.append(os.getcwd())

from backend.app import create_app
from backend.repository.db_access import fetch_all

app = create_app()

def test_search_logic():
    with app.app_context():
        print("--- Testing Search Logic ---")
        
        # 1. Get a test user
        target = fetch_all("SELECT user_id, name FROM users LIMIT 1")[0]
        target_id = target['user_id']
        name = target['name']
        public_id_query = f"#{1000000000 + target_id}"
        
        print(f"Target: {name} (ID: {target_id}) -> Query: '{public_id_query}'")
        
        # 2. Simulate Logic from member_routes.py
        query = public_id_query
        
        search_id = None
        if query.startswith('#') and query[1:].isdigit():
            try:
                 search_id = int(query[1:]) - 1000000000
            except:
                 pass
        elif query.isdigit():
            try:
                 search_id = int(query) - 1000000000
            except:
                 pass
        
        print(f"Parsed Search ID: {search_id}")
        
        if search_id:
            users = fetch_all("""
                SELECT user_id, name, profile_pic, role 
                FROM users 
                WHERE user_id = %s OR name LIKE %s OR role LIKE %s
                LIMIT 10
            """, (search_id, f"%{query}%", f"%{query}%"))
        else:
             print("FAIL: ID parsing failed.")
             return

        # 3. Verify Result
        found = any(u['user_id'] == target_id for u in users)
        
        if found:
            print(f"PASS: Logic correctly found user ID {target_id}")
        else:
            print(f"FAIL: Database query returned: {users}")

if __name__ == "__main__":
    test_search_logic()
