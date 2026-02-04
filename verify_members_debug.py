
import sys
import os
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
EMAIL = "admin@library.com"
PASSWORD = "admin123"

def run_test():
    s = requests.Session()
    
    print("Logging in...")
    try:
        res = s.post(f"{BASE_URL}/", data={"email": EMAIL, "password": PASSWORD})
        if res.status_code != 200:
            print(f"Login failed: {res.status_code}")
            return
    except:
        print("Server likely not running.")
        return

    print("Fetching conversations...")
    res = s.get(f"{BASE_URL}/chat/conversations")
    try:
        data = res.json()
    except:
        print(f"Failed to parse JSON. Status: {res.status_code}")
        print(f"Response Text: {res.text[:500]}...") # Print preview
        return

    groups = data.get('conversations', {}).get('group', [])
    if not groups:
        print("No groups found. Checking specific channel ID 2...")
        cid = 2
    else:
        cid = groups[0]['channel_id']
        print(f"Testing with Group: {groups[0]['name']} (ID: {cid})")

    print(f"\nFetching members for Channel {cid}...")
    res = s.get(f"{BASE_URL}/chat/channels/{cid}/members")
    try:
        m_data = res.json()
        members = m_data.get('members', [])
        print(f"Total Members: {len(members)}")
        for m in members:
            role_str = m['role']
            if m.get('is_owner'): role_str += " (OWNER)"
            print(f"User: {m['name']} | ID: {m['user_id']} | Role: {role_str}")
    except:
        print(f"Failed to parse Members JSON. Status: {res.status_code}")
        print(f"Response: {res.text[:500]}")

if __name__ == "__main__":
    run_test()
