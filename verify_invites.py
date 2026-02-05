
import requests
import sys

BASE_URL = "http://127.0.0.1:5000"
s = requests.Session()

def verify_invites():
    # 1. Login
    print("🔑 Logging in...")
    try:
        res = s.post(f"{BASE_URL}/", data={'email': 'tester@automation.com', 'password': 'AutoTest@123'})
        if res.status_code != 200:
            print(f"❌ Login failed. Status: {res.status_code}, Response: {res.text[:200]}")
            return
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    # 2. Check Pending Invites
    print("📩 Fetching Pending Invites...")
    res = s.get(f"{BASE_URL}/chat/invites/pending")
    
    if res.status_code == 200:
        try:
            data = res.json()
        except Exception:
            print(f"❌ JSON Decode Error. Body: {res.text[:500]}")
            return
        if data.get('success'):
            invites = data.get('invites', [])
            print(f"✅ API Success. Pending Invites Count: {len(invites)}")
            for inv in invites:
                print(f"   - Invite ID: {inv['invite_id']}, From: {inv['sender_name']}, Type: {inv['type']}")
        else:
            print(f"❌ API Error: {data}")
    else:
        print(f"❌ Request Failed: {res.status_code}")

if __name__ == "__main__":
    verify_invites()
