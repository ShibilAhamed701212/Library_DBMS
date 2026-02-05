from backend.config.db import get_connection
from backend.services.enrichment_service import enrich_book_metadata
import time

def backfill_metadata():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get all books without cover or description
    cursor.execute("SELECT book_id, title FROM books WHERE cover_url IS NULL OR description IS NULL")
    books = cursor.fetchall()
    
    print(f"📚 Found {len(books)} books needing metadata enrichment...")
    
    count = 0
    for book in books:
        book_id = book[0]
        title = book[1]
        print(f"\n🔄 Processing: {title} ({count+1}/{len(books)})")
        
        try:
            enrich_book_metadata(book_id)
            count += 1
            # Rate limit friendly (Google Books has quotas)
            time.sleep(0.5) 
        except Exception as e:
            print(f"❌ Failed: {e}")
            
    print(f"\n✅ Completed! Enriched {count} books.")

if __name__ == "__main__":
    backfill_metadata()
