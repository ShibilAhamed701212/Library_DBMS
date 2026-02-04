
import sys
import os
import requests

# Add project root to path (though requests uses URL)
BASE_URL = "http://127.0.0.1:5000"
EMAIL = "admin@library.com"
PASSWORD = "admin123"

def run_test():
    s = requests.Session()
    
    # 1. Login
    print(f"Logging in as {EMAIL}...")
    # Use / based on previous finding
    res = s.post(f"{BASE_URL}/", data={"email": EMAIL, "password": PASSWORD})
    if "Dashboard" not in res.text and res.status_code != 200:
        print("Login Failed")
        return

    # 2. Search by Name (Control Test)
    print("\nTest 1: Search by Name 'Admin'...")
    res = s.get(f"{BASE_URL}/member/search_users_json?q=Admin")
    data = res.json()
    users = data.get('users', [])
    print(f"Found {len(users)} users.")
    if len(users) > 0:
        print(f"Sample: {users[0]['name']} (ID: {users[0]['user_id']})")
    
    if not users:
        print("FAIL: Name search failed.")
        return

    # Get an ID to test with
    target_id = users[0]['user_id']
    public_id_str = f"#{1000000000 + target_id}"
    
    # 3. Search by ID (Target Test)
    print(f"\nTest 2: Search by ID '{public_id_str}'...")
    res = s.get(f"{BASE_URL}/member/search_users_json?q={public_id_str.replace('#', '%23')}")
    data = res.json()
    users = data.get('users', [])
    
    found = False
    for u in users:
        if u['user_id'] == target_id:
            found = True
            print(f"PASS: Found user {u['name']} by ID query.")
            break
            
    if not found:
        print(f"FAIL: Did not find user by ID query. Response: {users}")

    # 4. Search by Raw ID Number (without #)
    print(f"\nTest 3: Search by Raw ID '{1000000000 + target_id}'...")
    res = s.get(f"{BASE_URL}/member/search_users_json?q={1000000000 + target_id}")
    data = res.json()
    users = data.get('users', [])
    
    found = False
    for u in users:
        if u['user_id'] == target_id:
            found = True
            print(f"PASS: Found user {u['name']} by Raw ID.")
            break
            
    if not found:
         print(f"FAIL: Did not find user by Raw ID.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Test Error: {e}")
