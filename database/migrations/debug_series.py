import requests
import re

def debug(title, author_name):
    print(f"\n📘 DEBUGGING SERIES FOR: {title} ({author_name})")
    
    # 1. GOOGLE BOOKS
    print("\n--- Google Books ---")
    gb_url = f"https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author_name}&maxResults=1"
    gb_data = requests.get(gb_url).json()
    
    if gb_data.get('totalItems', 0) > 0:
        info = gb_data['items'][0]['volumeInfo']
        print(f"Title: {info.get('title')}")
        print(f"Subtitle: {info.get('subtitle')}")
        
        # Test Regex
        full_text = f"{info.get('title')} {info.get('subtitle', '')}"
        match = re.search(r'\(([^)]+),?\s+[#]?(\d+)\)', full_text)
        if match:
            print(f"✅ Regex Match: {match.groups()}")
        else:
            print("❌ No Regex Match in Title/Subtitle")
    else:
        print("❌ No Google Books found")

    # 2. OPEN LIBRARY
    print("\n--- Open Library ---")
    ol_url = f"https://openlibrary.org/search.json?title={title}&author={author_name}&limit=1"
    ol_data = requests.get(ol_url).json()
    
    if ol_data['numFound'] > 0:
        doc = ol_data['docs'][0]
        print(f"Key: {doc.get('key')}")
        print(f"Title: {doc.get('title')}")
        
        # Check for 'key' (Work ID)
        work_key = doc.get('key')
        if work_key:
            # Fetch work details
            work_url = f"https://openlibrary.org{work_key}.json"
            print(f"Fetching Work: {work_url}")
            work_details = requests.get(work_url).json()
            if 'series' in work_details:
                print(f"✅ Found 'series' field: {work_details['series']}")
            else:
                print("❌ No 'series' field in Work payload")
    else:
        print("❌ No Open Library found")

if __name__ == "__main__":
    debug("Harry Potter and the Sorcerer's Stone", "J.K. Rowling")
    debug("Dune", "Frank Herbert")
