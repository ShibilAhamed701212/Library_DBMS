
import os
import sys
sys.path.append(os.getcwd())
from backend.app import create_app
app = create_app()

with app.app_context():
    from backend.services.channel_service import save_message
    try:
        user_id = 1
        channel_id = 1
        print(f"Testing save_message for user {user_id}, channel {channel_id}")
        res = save_message(user_id, channel_id, text="Diagnostic Test")
        print(f"Success! Message ID: {res['message_id']}")
    except Exception as e:
        import traceback
        traceback.print_exc()
