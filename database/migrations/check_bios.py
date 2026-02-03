import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.repository.db_access import fetch_all

def check():
    print("🔍 Checking Author Bios...")
    authors = fetch_all("SELECT name, bio FROM authors WHERE bio IS NOT NULL LIMIT 5")
    
    for a in authors:
        bio = a['bio']
        print(f"\n👤 Author: {a['name']}")
        print(f"📏 Length: {len(bio)} chars")
        print(f"📄 Preview: {bio[:200]}...")
        if "<" in bio:
            print("⚠️ WARNING: HTML Tags detected!")
        else:
            print("✅ Verified: Clean Text")

if __name__ == "__main__":
    check()
