
from backend.repository.db_access import fetch_all, fetch_one, execute

def get_author_details(author_id):
    """Fetches full bio and metadata for an author."""
    return fetch_one("SELECT * FROM authors WHERE author_id = %s", (author_id,))

def get_author_books(author_id):
    """Fetches all books written by a specific author."""
    return fetch_all("""
        SELECT book_id, title, category, available_copies, pdf_src 
        FROM books 
        WHERE author_id = %s
    """, (author_id,))

def get_series_details(series_id):
    """Fetches description and title for a series."""
    return fetch_one("SELECT series_id, name as title, description, created_at FROM series WHERE series_id = %s", (series_id,))

def get_series_books(series_id):
    """Fetches all books in a series, ordered by their sequence."""
    return fetch_all("""
        SELECT book_id, title, series_order 
        FROM books 
        WHERE series_id = %s 
        ORDER BY series_order ASC
    """, (series_id,))

def update_author_bio(author_id, bio, nationality=None):
    """Updates author information."""
    if nationality:
        execute("UPDATE authors SET bio = %s, nationality = %s WHERE author_id = %s", (bio, nationality, author_id))
    else:
        execute("UPDATE authors SET bio = %s WHERE author_id = %s", (bio, author_id))
    return "✅ Author updated"

def get_all_authors():
    """Returns a list of all authors for dropdowns/discovery."""
    return fetch_all("SELECT author_id, name FROM authors ORDER BY name ASC")

def get_all_series():
    """Returns a list of all series with book counts."""
    return fetch_all("""
        SELECT s.series_id, s.name as title, s.description, 
               (SELECT COUNT(*) FROM books b WHERE b.series_id = s.series_id) as book_count 
        FROM series s 
        ORDER BY s.name ASC
    """)
