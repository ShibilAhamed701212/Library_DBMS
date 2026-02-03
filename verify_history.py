
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"
s = requests.Session()

def verify_history_structure():
    # 1. Login
    print("🔑 Logging in...")
    s.post(f"{BASE_URL}/", data={'email': 'tester@automation.com', 'password': 'AutoTest@123'})
    
    # 2. Get Global Channel Messages (ID 1)
    print("📥 Fetching history for Channel 1...")
    res = s.get(f"{BASE_URL}/chat/channels/1/messages")
    
    if res.status_code == 200:
        data = res.json()
        msgs = data.get('messages', [])
        print(f"✅ Fetched {len(msgs)} messages.")
        
        found_attachment = False
        for m in msgs:
            if m.get('attachment'):
                print(f"📸 Found Attachment Metadata: {m['attachment']}")
                found_attachment = True
                if 'url' in m['attachment'] and 'type' in m['attachment']:
                    print("   ✅ Structure is correct (url + type present)")
                else:
                    print("   ❌ Structure incomplete!")
                    
        if not found_attachment:
            print("⚠️ No attachments found in history to verify (Try uploading one manually first).")
    else:
        print(f"❌ Failed to fetch history: {res.status_code}")

if __name__ == "__main__":
    verify_history_structure()
