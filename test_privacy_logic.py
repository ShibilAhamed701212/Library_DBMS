
import sys
import os

# Ensure backend package is importable
sys.path.append(os.getcwd())

from backend.app import create_app
from backend.services.channel_service import create_channel, get_my_dms
from backend.routes.chat_routes import route_update_channel_settings, get_conversations_route
from backend.repository.db_access import execute, fetch_one, fetch_all
from flask import session

app = create_app()

def test_logic():
    with app.app_context():
        print("--- Starting Backend Logic Test ---")
        
        # 1. Setup Mock User
        # Find a real user or create one
        user_id = 1 # Admin usually
        session['user_id'] = user_id
        session['role'] = 'admin'
        
        print(f"Mocking User ID: {user_id}")
        
        # 2. Create Public Group
        # Directly call service to avoid route overhead, or mocking request?
        # Let's call service for creation, then route for update (since route has the fix logic)
        
        # Create Public Channel
        print("\n[Action] Creating Public Channel via Service...")
        cid = create_channel(
            guild_id=None, 
            category_id=None, 
            name="LogicTest_Public", 
            type="text", 
            is_private=False, 
            creator_id=user_id
        )
        print(f"Created Channel ID: {cid}")
        
        # Verify in Conversations -> Public
        # We need to mock 'get_conversations_route' or call the queries directly.
        # Let's call the route function, but it returns a Response object (jsonify).
        
        print("[Check] Verifying in Public List...")
        # get_conversations_route returns jsonify response
        resp = get_conversations_route()
        data = resp.get_json()
        
        public_list = data['conversations']['public']
        in_public = any(c['channel_id'] == cid for c in public_list)
        
        if in_public:
            print("PASS: Found in Public List")
        else:
            print("FAIL: Not in Public List")
            return

        # 3. Toggle to Private using the ROUTE (to trigger the fix in chat_routes.py)
        print("\n[Action] Toggling to Private via Route...")
        
        # Need to mock request.form and request.files
        with app.test_request_context(
            f'/chat/channels/{cid}/settings',
            method='POST',
            data={'is_private': 'true', 'type': 'text'}
        ):
            # Session needs to be set again in this context?
            session['user_id'] = user_id
            session['role'] = 'admin'
            
            # Call route handler directly
            resp = route_update_channel_settings(cid)
            res_data = resp.get_json()
            
            if res_data.get('success'):
                print("Update Success")
            else:
                print(f"Update Failed: {res_data}")
                return

        # 4. Verify in Private Group List
        print("[Check] Verifying in Private Group List...")
        resp = get_conversations_route()
        data = resp.get_json()
        
        group_list = data['conversations']['group']
        in_group = any(c['channel_id'] == cid for c in group_list)
        
        if in_group:
            print("PASS: Found in Private Group List")
        else:
            print("FAIL: Not in Private Group List")
            # Check DB participants
            parts = fetch_all("SELECT * FROM dm_participants WHERE channel_id = %s", (cid,))
            print(f"DB Participants: {parts}")
            return

        # 5. Toggle back to Public
        print("\n[Action] Toggling back to Public via Route...")
        with app.test_request_context(
            f'/chat/channels/{cid}/settings',
            method='POST',
            data={'is_private': 'false', 'type': 'text'}
        ):
            session['user_id'] = user_id
            session['role'] = 'admin'
            
            resp = route_update_channel_settings(cid)
            
        # 6. Verify in Public List
        print("[Check] Verifying in Public List (Revert)...")
        resp = get_conversations_route()
        data = resp.get_json()
        
        public_list = data['conversations']['public']
        in_public = any(c['channel_id'] == cid for c in public_list)
        
        if in_public:
            print("PASS: Found in Public List after revert")
        else:
            print("FAIL: Not in Public List after revert")
            return

        print("\n--- ALL LOGIC TESTS PASSED ---")

if __name__ == "__main__":
    test_logic()
