
import os
import sys
sys.path.append(os.getcwd())

from backend.app import create_app
app = create_app()

def verify():
    with app.app_context():
        # Clean import to get the latest code
        from backend.services.channel_service import save_message
        
        print("🧪 Testing save_message with text=None (Image Upload Scenario)...")
        try:
            # Using user_id=1, channel_id=1 (General)
            # Assuming they exist from previous diagnostics
            res = save_message(
                user_id=1, 
                channel_id=1, 
                text=None, 
                file_url="/static/uploads/test_image.jpg"
            )
            print(f"✅ Success! Message ID: {res['message_id']}")
            print(f"   Content saved as: '{res['content']}'")
        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    verify()
