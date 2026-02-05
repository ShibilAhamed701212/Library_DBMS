
import requests
import sys
import os
sys.path.append(os.getcwd())

# Setup Flask Context to use DB
from backend.app import create_app
from backend.repository.db_access import execute, fetch_one
from backend.utils.security import hash_password

app = create_app()
BASE_URL = "http://127.0.0.1:5000"
TEST_EMAIL = "tester@automation.com"
TEST_PASS = "AutoTest@123"

def setup_test_user():
    with app.app_context():
        print("🛠️ Setting up test user...")
        # Check if exists
        user = fetch_one("SELECT user_id FROM users WHERE email = %s", (TEST_EMAIL,))
        if not user:
            print("   Creating new test user...")
            pw_hash = hash_password(TEST_PASS)
            execute("""
                INSERT INTO users (email, password_hash, name, role, must_change_password)
                VALUES (%s, %s, 'Automation Tester', 'member', FALSE)
            """, (TEST_EMAIL, pw_hash))
            print("   ✅ Test user created.")
        else:
            # Update password to be sure
            print("   Updating existing test user password...")
            pw_hash = hash_password(TEST_PASS)
            execute("UPDATE users SET password_hash = %s WHERE email = %s", (pw_hash, TEST_EMAIL))
            print("   ✅ Test user updated.")

def verify_full_flow():
    session = requests.Session()
    
    # 1. Login
    print(f"🔑 Logging in as {TEST_EMAIL}...")
    res = session.post(f"{BASE_URL}/", data={'email': TEST_EMAIL, 'password': TEST_PASS})
    
    # Check if we got redirected (Success) or stayed on login (Fail)
    if res.history and res.history[0].status_code == 302:
        print("✅ Login Successful (Redirected)")
    elif "dashboard" in res.text or "Logout" in res.text:
         print("✅ Login Successful (Dashboard found)")
    else:
        print("❌ Login Failed.")
        print(f"   Final URL: {res.url}")
        return

    # 2. Check Conversations
    print("\nChecking /chat/conversations...")
    res = session.get(f"{BASE_URL}/chat/conversations")
    if res.status_code == 200:
        try:
            data = res.json()
            if data['success']:
                print(f"✅ API OK. DMs: {len(data['conversations']['personal'])}")
            else:
                print(f"❌ API returned success=False: {data}")
        except:
             print(f"❌ Invalid JSON: {res.text[:100]}")
    else:
        print(f"❌ HTTP {res.status_code}")

    # 3. Check Pending Invites
    print("\nChecking /chat/invites/pending...")
    res = session.get(f"{BASE_URL}/chat/invites/pending")
    if res.status_code == 200:
        print("✅ Invites Endpoint OK")
    else:
        print(f"❌ Invites Endpoint Failed: {res.status_code}")

if __name__ == "__main__":
    setup_test_user()
    verify_full_flow()
