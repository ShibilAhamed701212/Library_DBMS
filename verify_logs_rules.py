
import sys
import os
import requests

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
        print("Server likely not running. Skipping live test.")
        return

    # Use Channel IDs 1 (Global)
    cid = 1
    
    # 1. Update Rules
    print("Test 1: Updating Rules...")
    try:
        res = s.post(f"{BASE_URL}/chat/channels/{cid}/rules", json={"rules": "Rule A: No spam.\nRule B: Be cool."})
        print(f"Status: {res.status_code}, Response: {res.json()}")
    except Exception as e:
        print(f"Update Rules Failed: {e}")

    # 2. Get Rules
    print("\nTest 2: Fetching Rules...")
    try:
        res = s.get(f"{BASE_URL}/chat/channels/{cid}/rules")
        data = res.json()
        print(f"Rules: {data.get('rules')}")
    except Exception as e:
        print(f"Get Rules Failed: {e}")

    # 3. Get Logs (Update Rule should have logged)
    print("\nTest 3: Fetching Logs...")
    try:
        res = s.get(f"{BASE_URL}/chat/channels/{cid}/logs")
        data = res.json()
        logs = data.get('logs', [])
        print(f"Found {len(logs)} logs.")
        if len(logs) > 0:
            print(f"Latest Log: {logs[0]}")
    except Exception as e:
        print(f"Get Logs Failed: {e}")

if __name__ == "__main__":
    run_test()
