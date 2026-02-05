import requests

import re

BASE_URL = "http://127.0.0.1:5000"
LOGIN_URL = f"{BASE_URL}/login"
OVERVIEW_URL = f"{BASE_URL}/member/dashboard"

session = requests.Session()

def login():
    print("🔑 Logging in...")
    payload = {
        "email": "tester@automation.com",
        "password": "securepassword123"
    }
    try:
        res = session.post(LOGIN_URL, data=payload)
        is_success = res.url == OVERVIEW_URL or "/member/dashboard" in res.url
        print(f"✅ Login {'Successful' if is_success else 'Failed'}")
        return is_success
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        return False

def check_recommendations():
    print("\n🔮 Checking Recommendations...")
    try:
        res = session.get(OVERVIEW_URL)
        if res.status_code == 200:
            # Simple substring check instead of bs4 dependency if prefered, 
            # but regex is good for counting.
            
            # Check for container
            if "recommendations-container" in res.text:
                print("✅ Netflix UI Container Found")
            else:
                print("❌ UI Container Missing")
            
            # Count Recs
            count = res.text.count("recommendation-card")
            print(f"📚 Found {count} recommendation cards")
            
            # Check for new metadata
            if 'background-image: url(' in res.text:
                 print("✅ Real Cover Images Detected")
            else:
                 print("⚠️ No Real Covers Found (Might be using gradients)")
                 
            if 'line-clamp: 3' in res.text:
                 print("✅ Description Truncation CSS Found")
            
            # Check for match percentage (logic verification)
            if "Match" in res.text:
                print("✅ Match Percentage Displayed")
            
        else:
            print(f"❌ Page Failed: {res.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if login():
        check_recommendations()
