
import sys
import os
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
EMAIL = "admin@library.com"
PASSWORD = "admin123"

def run_test():
    s = requests.Session()
    
    # login
    print("Logging in...")
    try:
        s.post(f"{BASE_URL}/", data={"email": EMAIL, "password": PASSWORD})
    except:
        print("Server likely not running.")
        return

    # Fetch Conversations to find a group channel
    print("Fetching conversations...")
    res = s.get(f"{BASE_URL}/chat/conversations")
    data = res.json()
    
    groups = data.get('conversations', {}).get('group', [])
    if not groups:
        print("No groups found. Checking Global Chat (ID 1)...")
        cid = 1
    else:
        cid = groups[0]['channel_id']
        print(f"Testing with Group: {groups[0]['name']} (ID: {cid})")

    # Fetch Members
    print(f"\nFetching members for Channel {cid}...")
    res = s.get(f"{BASE_URL}/chat/channels/{cid}/members")
    m_data = res.json()
    
    if m_data.get('success'):
        members = m_data.get('members', [])
        print(f"Total Members: {len(members)}")
        print("-" * 40)
        for m in members:
            # Print details to see if name/role is correct
            role_str = m['role']
            if m.get('is_owner'): role_str += " (OWNER)"
            print(f"User: {m['name']} | ID: {m['user_id']} | Role: {role_str}")
        print("-" * 40)
    else:
        print(f"Failed to fetch members: {m_data}")

if __name__ == "__main__":
    run_test()
