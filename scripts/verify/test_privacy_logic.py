
import sys
import os

# Ensure backend package is importable
sys.path.append(os.getcwd())

from backend.app import create_app
from backend.services.channel_service import create_channel
from backend.routes.chat_routes import route_update_channel_settings, get_conversations_route
from backend.repository.db_access import fetch_all
from flask import session

app = create_app()

def test_logic():
    with app.app_context():
        print("--- Starting Backend Logic Test ---")

        user_id = 1  # Admin usually
        print(f"Mocking User ID: {user_id}")

        def _set_session():
            session['user_id'] = user_id
            session['role'] = 'admin'

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

        print("[Check] Verifying in Public List...")
        with app.test_request_context('/chat/conversations', method='GET'):
            _set_session()
            resp = get_conversations_route()
            data = resp.get_json()
        public_list = data['conversations']['public']
        in_public = any(c['channel_id'] == cid for c in public_list)
        if in_public:
            print("PASS: Found in Public List")
        else:
            print("FAIL: Not in Public List")
            return

        print("\n[Action] Toggling to Private via Route...")
        with app.test_request_context(
            f'/chat/channels/{cid}/settings',
            method='POST',
            data={'is_private': 'true', 'type': 'text'}
        ):
            _set_session()
            resp = route_update_channel_settings(cid)
            res_data = resp.get_json()
        if res_data.get('success'):
            print("Update Success")
        else:
            print(f"Update Failed: {res_data}")
            return

        print("[Check] Verifying in Private Group List...")
        with app.test_request_context('/chat/conversations', method='GET'):
            _set_session()
            resp = get_conversations_route()
            data = resp.get_json()
        group_list = data['conversations']['group']
        in_group = any(c['channel_id'] == cid for c in group_list)
        if in_group:
            print("PASS: Found in Private Group List")
        else:
            print("FAIL: Not in Private Group List")
            parts = fetch_all("SELECT * FROM dm_participants WHERE channel_id = %s", (cid,))
            print(f"DB Participants: {parts}")
            return

        print("\n[Action] Toggling back to Public via Route...")
        with app.test_request_context(
            f'/chat/channels/{cid}/settings',
            method='POST',
            data={'is_private': 'false', 'type': 'text'}
        ):
            _set_session()
            route_update_channel_settings(cid)

        print("[Check] Verifying in Public List (Revert)...")
        with app.test_request_context('/chat/conversations', method='GET'):
            _set_session()
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
