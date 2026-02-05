
import requests
import time
import sys

BASE_URL = "http://127.0.0.1:5000"
EMAIL = "admin@library.com"
PASSWORD = "admin123"

def run_test():
    s = requests.Session()
    
    # 1. Login
    print(f"Logging in as {EMAIL}...")
    res = s.post(f"{BASE_URL}/", data={"email": EMAIL, "password": PASSWORD})
    if "Dashboard" not in res.text and res.status_code != 200:
        print("Login Failed")
        print(res.text[:500])
        return

    # 2. Creates Public Group
    group_name = f"TestGroup_Back_{int(time.time())}"
    print(f"Creating Public Group: {group_name}")
    
    # API for create channel?
    # Found in chat_routes.py: @chat_bp.route('/channels', methods=['POST'])
    # Payload: guild_id, name, type, is_private
    
    payload = {
        "guild_id": None, # Global
        "name": group_name,
        "type": "text",
        "is_private": False
    }
    
    res = s.post(f"{BASE_URL}/chat/channels", json=payload)
    if res.status_code != 200:
        print(f"Failed to create group: {res.text}")
        return
        
    try:
        data = res.json()
    except:
        print(f"JSON Decode Error. Status: {res.status_code}")
        print(f"Response: {res.text}")
        return
        
    channel_id = data['channel_id']
    print(f"Created Channel ID: {channel_id}")
    
    # 3. Verify in Public Tab
    print("Verifying in Public List...")
    res = s.get(f"{BASE_URL}/chat/conversations")
    convs = res.json().get('conversations', {})
    
    public_list = convs.get('public', [])
    found = any(c['channel_id'] == channel_id for c in public_list)
    
    if found:
        print("PASS: Group found in 'public' list")
    else:
        print("FAIL: Group NOT found in 'public' list")
        print("Public List:", [c['name'] for c in public_list])
        return

    # 4. Switch to Private
    print("Switching to Private...")
    # Route: /channels/<int:channel_id>/settings (POST)
    # Form Data: is_private (true/false), type
    
    update_data = {
        "is_private": "true",
        "type": "text"
    }
    
    # Use multipart form data check?
    # requests handles dict as form-encoded by default if not json param
    res = s.post(f"{BASE_URL}/chat/channels/{channel_id}/settings", data=update_data)
    
    if res.json().get('success'):
        print("Update Successful")
    else:
        print(f"Update Failed: {res.text}")
        return
        
    # 5. Verify in Private Groups Tab
    print("Verifying in Private Groups List...")
    res = s.get(f"{BASE_URL}/chat/conversations")
    convs = res.json().get('conversations', {})
    
    group_list = convs.get('group', [])
    found = any(c['channel_id'] == channel_id for c in group_list)
    
    if found:
        print("PASS: Group found in 'group' list")
    else:
        print("FAIL: Group NOT found in 'group' list")
        print("Group List:", [c['name'] for c in group_list])
        # Check if it's still in public?
        public_list = convs.get('public', [])
        if any(c['channel_id'] == channel_id for c in public_list):
            print("... It is still in 'public' list!")
        return

    # 6. Switch back to Public
    print("Switching back to Public...")
    update_data = {
        "is_private": "false",
        "type": "text"
    }
    res = s.post(f"{BASE_URL}/chat/channels/{channel_id}/settings", data=update_data)
    
    if not res.json().get('success'):
        print(f"Update Revert Failed: {res.text}")
        return

    # 7. Verify in Public Tab
    print("Verifying in Public List (After Revert)...")
    res = s.get(f"{BASE_URL}/chat/conversations")
    convs = res.json().get('conversations', {})
    
    public_list = convs.get('public', [])
    found = any(c['channel_id'] == channel_id for c in public_list)
    
    if found:
        print("PASS: Group returned to 'public' list")
    else:
        print("FAIL: Group NOT found in 'public' list")
        
    print("TEST COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Error: {e}")
