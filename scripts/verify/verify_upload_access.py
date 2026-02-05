
import requests
import os

BASE_URL = "http://127.0.0.1:5000"
# Login first to get session (using requests.Session)
s = requests.Session()

def test_upload():
    # 1. Login
    print("🔑 Logging in...")
    s.post(f"{BASE_URL}/", data={'email': 'tester@automation.com', 'password': 'AutoTest@123'})
    
    # 2. Upload
    print("📤 Uploading file...")
    # Create a dummy file
    with open("test_upload.txt", "w") as f:
        f.write("This is a test file content.")
        
    try:
        files = {'file': ('test_upload.txt', open('test_upload.txt', 'rb'))}
        res = s.post(f"{BASE_URL}/chat/upload", files=files)
        
        if res.status_code == 200:
            print(f"✅ Upload Success: {res.json()}")
            file_url = res.json().get('file_path')
            
            # 3. Verify Retrieval
            print(f"🔎 Verifying access to {file_url}...")
            # Remove leading slash for URL construction if needed, but browser handles it relative to domain
            # Flask returns /static/..., so we append to BASE_URL
            access_url = f"{BASE_URL}{file_url}"
            res_get = s.get(access_url)
            if res_get.status_code == 200:
                print("✅ File verified accessible (HTTP 200)")
            else:
                print(f"❌ File Not Found! HTTP {res_get.status_code}")
        else:
            print(f"❌ Upload Failed: {res.text}")
            
    finally:
        if os.path.exists("test_upload.txt"):
            os.remove("test_upload.txt")

if __name__ == "__main__":
    test_upload()
