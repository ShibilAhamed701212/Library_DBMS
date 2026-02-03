import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.services.enrichment_service import enrich_book_metadata
from backend.repository.db_access import fetch_all

def bulk_enrich():
    print("🚀 Starting Bulk AI Enrichment for all books...")
    
    # Fetch all books that either don't have an author_id OR don't have a series_id
    # We want to be thorough.
    books = fetch_all("SELECT book_id, title FROM books")
    total = len(books)
    print(f"📦 Found {total} books to check.")
    
    count = 0
    for b in books:
        count += 1
        print(f"[{count}/{total}] Enriching: {b['title']}...")
        result = enrich_book_metadata(b['book_id'])
        if result == "Success":
            print(f"  ✅ Enriched successfully.")
        else:
            print(f"  ⚠️ Skip/Error: {result}")
            
    print("🎉 Bulk Enrichment completed!")

if __name__ == "__main__":
    bulk_enrich()
