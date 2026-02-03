
import requests
from backend.services.author_service import add_author
from backend.repository.db_access import fetch_one

def fetch_book_metadata(isbn):
    """
    Fetches book details from OpenLibrary and Google Books APIs.
    Returns a dict with title, author_name, category, and cover_url.
    """
    isbn = isbn.strip().replace("-", "")
    
    # 1. Try Google Books API first (usually better results)
    try:
        gb_url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        resp = requests.get(gb_url, timeout=5)
        data = resp.json()
        
        if data.get("totalItems", 0) > 0:
            item = data["items"][0]["volumeInfo"]
            author_name = item.get("authors", ["Unknown"])[0]
            
            return {
                "title": item.get("title", "Unknown Title"),
                "author_name": author_name,
                "category": item.get("categories", ["General"])[0],
                "description": item.get("description", ""),
                "cover_url": item.get("imageLinks", {}).get("thumbnail", ""),
                "isbn": isbn
            }
    except Exception as e:
        print(f"⚠️ Google Books API error: {e}")

    # 2. Fallback to OpenLibrary API
    try:
        ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
        resp = requests.get(ol_url, timeout=5)
        data = resp.json()
        
        key = f"ISBN:{isbn}"
        if key in data:
            book = data[key]
            author_name = book.get("authors", [{"name": "Unknown"}])[0]["name"]
            
            return {
                "title": book.get("title", "Unknown Title"),
                "author_name": author_name,
                "category": "General", # OL data varies
                "description": book.get("notes", ""),
                "cover_url": book.get("cover", {}).get("large", ""),
                "isbn": isbn
            }
    except Exception as e:
        print(f"⚠️ OpenLibrary API error: {e}")

    return None

def process_metadata_for_form(isbn):
    """
    Fetches metadata and checks if author exists.
    Returns data ready for the frontend form.
    """
    data = fetch_book_metadata(isbn)
    if not data:
        return None
        
    # Check if author exists, if not we might need to handle it on the frontend
    # or return the author_name for the admin to confirm.
    author_res = fetch_one("SELECT author_id FROM authors WHERE name = %s", (data['author_name'],))
    data['author_id'] = author_res['author_id'] if author_res else None
    
    return data
