
import sys
import os
import requests

# Adjust if we want to test via API locally
BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def verify_categorization():
    email = "tester@automation.com"
    password = "AutoTest@123"
    
    # Login
    print("🔑 Logging in...")
    res = session.post(f"{BASE_URL}/", data={'email': email, 'password': password})
    if res.status_code != 200:
        print("❌ Login failed")
        return

    # 1. Create Public Group
    print("📢 Creating Public Group...")
    res = session.post(f"{BASE_URL}/chat/channels", json={
        'name': 'Auto Public Group',
        'type': 'text',
        'is_private': False
    })
    pub_id = res.json().get('channel_id')
    print(f"   - Created Public ID: {pub_id}")

    # 2. Create Private Group
    print("🔒 Creating Private Group...")
    res = session.post(f"{BASE_URL}/chat/channels", json={
        'name': 'Auto Private Group',
        'type': 'text',
        'is_private': True
    })
    priv_id = res.json().get('channel_id')
    print(f"   - Created Private ID: {priv_id}")
    
    # 3. Fetch Conversations
    print("📜 Fetching Sidebar...")
    res = session.get(f"{BASE_URL}/chat/conversations")
    data = res.json()
    
    if not data.get('success'):
        print("❌ Failed to fetch conversations")
        return
        
    convs = data['conversations']
    
    # Check Public
    public_found = any(c['channel_id'] == pub_id for c in convs['public'])
    if public_found:
        print("✅ Public group found in 'public' list.")
    else:
        print("❌ Public group MISSING from 'public' list.")
        
    # Check Private (should be in 'group' list)
    private_found = any(c['channel_id'] == priv_id for c in convs['group'])
    if private_found:
        print("✅ Private group found in 'group' list.")
    else:
        print("❌ Private group MISSING from 'group' list.")
        # Debug: check where it is
        if any(c['channel_id'] == priv_id for c in convs['personal']):
             print("   ⚠️ It was found in 'personal' list instead.")
        elif any(c['channel_id'] == priv_id for c in convs['public']):
             print("   ⚠️ It was found in 'public' list instead.")

if __name__ == "__main__":
    verify_categorization()
