import requests


BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
LEADERBOARD_API = f"{BASE_URL}/member/api/leaderboard"
PROFILE_URL = f"{BASE_URL}/member/profile/1" # Assuming user 1 exists

session = requests.Session()

def login():
    print("🔑 Logging in...")
    # Using the test user credentials
    payload = {
        "email": "tester@automation.com",
        "password": "securepassword123"
    }
    try:
        res = session.post(LOGIN_URL, data=payload)
        if res.url == f"{BASE_URL}/member/dashboard":
            print("✅ Login Successful")
            return True
        else:
            print(f"❌ Login Failed. Redirected to: {res.url}")
            return False
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def check_leaderboard():
    print("\n🏆 Checking Leaderboard API...")
    try:
        res = session.get(LEADERBOARD_API)
        if res.status_code == 200:
            data = res.json()
            print(f"✅ API Success. Records found: {len(data)}")
            if len(data) > 0:
                print(f"   Top User: {data[0].get('name')} ({data[0].get('books_read')} books)")
        else:
            print(f"❌ API Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ API Error: {e}")

def check_public_profile():
    print("\n👤 Checking Public Profile Route...")
    try:
        # Note: If user 1 is the logged in user, it might redirect.
        # But we just want to ensure it doesn't 500.
        res = session.get(PROFILE_URL)
        if res.status_code == 200:
            print("✅ Profile Page Loaded (200 OK)")
            if "Reader Profile" in res.text:
                print("✅ Content verified")
        elif res.status_code == 302:
             print(f"ℹ️ Redirected (Expected if viewing self): {res.headers['Location']}")
        else:
            print(f"❌ Page Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Profile Error: {e}")

if __name__ == "__main__":
    if login():
        check_leaderboard()
        check_public_profile()
