
import sys
import os
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
EMAIL = "admin@library.com"
PASSWORD = "admin123"

def run_test():
    s = requests.Session()
    
    # Login
    print("Logging in...")
    try:
        s.post(f"{BASE_URL}/", data={"email": EMAIL, "password": PASSWORD})
    except:
        print("Server likely not running.")
        return

    # Test Search
    query = "#1000000005"
    print(f"Searching for '{query}'...")
    
    url = f"{BASE_URL}/member/search_users_json"
    res = s.get(url, params={"q": query})
    
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    
    try:
        data = res.json()
        users = data.get('users', [])
        print(f"Users Found: {len(users)}")
        for u in users:
            print(f" - {u['name']} (ID: {u['user_id']})")
    except:
        print("Failed to parse JSON")

if __name__ == "__main__":
    run_test()
