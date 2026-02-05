import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.repository.db_access import fetch_all

try:
    print("Columns in 'books':")
    books_cols = fetch_all("DESCRIBE books")
    print([c['Field'] for c in books_cols])
    
    print("\nColumns in 'authors':")
    authors_cols = fetch_all("DESCRIBE authors")
    print([c['Field'] for c in authors_cols])
except Exception as e:
    print(e)
