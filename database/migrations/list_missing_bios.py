import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.repository.db_access import fetch_all

def list_missing():
    print("🔍 Scanning for Authors without Bios...")
    authors = fetch_all("SELECT author_id, name FROM authors WHERE bio IS NULL OR length(bio) < 10")
    
    if not authors:
        print("✅ Great news: No authors found with missing bios!")
    else:
        print(f"⚠️ Found {len(authors)} authors with missing/short bios:")
        for a in authors:
            print(f" - [{a['author_id']}] {a['name']}")

if __name__ == "__main__":
    list_missing()
