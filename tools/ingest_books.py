import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.brain.rag import rag
from backend.repository.db_access import fetch_all

def ingest_books():
    print("📚 Fetching books from SQL Database...")
    
    # 1. Fetch books with author names
    # Note: 'description' column is missing in schema, so we omit it.
    query = """
        SELECT b.book_id, b.title, b.category, a.name as author_name
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
    """
    books = fetch_all(query)
    
    print(f"📖 Found {len(books)} books. Starting embedding process...")
    
    # 2. Embed and Store
    for i, book in enumerate(books):
        print(f"   Processing [{i+1}/{len(books)}]: {book['title']}")
        
        rag.add_book_to_memory(
            book_id=str(book['book_id']),
            title=book['title'],
            author=book['author_name'] or "Unknown",
            description="", # Description not available in DB
            category=book['category'] or "General"
        )
        
    print("\n✅ Ingestion Complete! The AI now knows about your library inventory.")

if __name__ == "__main__":
    ingest_books()
