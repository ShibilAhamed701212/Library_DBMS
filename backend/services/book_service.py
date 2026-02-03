"""
book_service.py
----------------
Handles book-related operations.

Responsibilities:
- Add new books
- View existing books
- Fetch a single book
- Delete books

This module:
- Contains business logic related to books
- Uses repository layer for database access
- Does NOT contain Flask routes
"""

# ===============================
# IMPORTS
# ===============================

from backend.repository.db_access import fetch_all, fetch_one, execute
# fetch_all → retrieve multiple records (SELECT)
# fetch_one → retrieve a single record
# execute   → execute INSERT / UPDATE / DELETE queries


# ===============================
# ADD BOOK
# ===============================

def add_book(title, author_id, category, total_copies, pdf_src=None, series_id=None, series_order=None):
    """
    Adds a new book to the library with relational author/series support.
    """

    if total_copies <= 0:
        return "❌ Total copies must be positive"

    book_id = execute(
        """
        INSERT INTO books
            (title, author_id, category, total_copies, available_copies, pdf_src, series_id, series_order)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (title, author_id, category, total_copies, total_copies, pdf_src, series_id, series_order)
    )

    return book_id


# ===============================
# UPDATE BOOK
# ===============================

def update_book(book_id, title, author_id, category, total_copies, series_id=None, series_order=None):
    """
    Updates existing book details and intelligently manages inventory counts.
    """
    book = get_book(book_id)
    if not book:
        return "❌ Book not found"

    # Calculate stock adjustment
    diff = total_copies - book['total_copies']
    new_available = book['available_copies'] + diff

    if new_available < 0:
        return f"❌ Cannot reduce stock to {total_copies}. {abs(new_available)} copies are currently issued."

    execute(
        """
        UPDATE books 
        SET title = %s, author_id = %s, category = %s, total_copies = %s, 
            available_copies = %s, series_id = %s, series_order = %s
        WHERE book_id = %s
        """,
        (title, author_id, category, total_copies, new_available, series_id, series_order, book_id)
    )

    return "✅ Book updated successfully"


# ===============================
# VIEW ALL BOOKS (PAGINATED & SEARCHABLE)
# ===============================

def view_books_paginated(page: int = 1, per_page: int = 10, search_query: str = "", author_id: int = None, category_filter: str = None):
    """
    Fetches books with enriched author and series metadata.
    """
    offset = (page - 1) * per_page
    
    # Base Query with JOINs
    query = """
        SELECT b.*, a.name as author_name, s.name as series_title 
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        LEFT JOIN series s ON b.series_id = s.series_id
        WHERE 1=1
    """
    params = []
    
    if search_query:
        query += " AND (b.title LIKE %s OR a.name LIKE %s OR b.category LIKE %s)"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])
        
    if author_id:
        query += " AND b.author_id = %s"
        params.append(author_id)
        
    if category_filter:
        query += " AND b.category = %s"
        params.append(category_filter)
        
    count_query = query.replace("SELECT b.*, a.name as author_name, s.name as series_title", "SELECT COUNT(*) AS c", 1)
    count_params = params.copy()
    
    query += " ORDER BY b.title ASC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    books = fetch_all(query, tuple(params))
    total_count = fetch_one(count_query, tuple(count_params))["c"]
    
    import math
    return {
        "books": books,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total_count / per_page)
    }


def view_books():
    """
    Legacy helper: Fetches ALL books without pagination.
    Avoid using for large datasets.
    """
    return fetch_all("SELECT * FROM books ORDER BY title ASC")


# ===============================
# GET SINGLE BOOK
# ===============================

def get_book(book_id: int):
    """
    Fetch a single book with author and series info.
    """
    return fetch_one(
        """
        SELECT b.*, a.name as author_name, s.name as series_title 
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        LEFT JOIN series s ON b.series_id = s.series_id
        WHERE b.book_id = %s
        """,
        (book_id,)
    )


# ===============================
# DELETE BOOK
# ===============================

def delete_book(book_id: int):
    """
    Deletes a book from the system.

    Args:
        book_id (int): Primary key of the book

    Returns:
        Status message indicating success or failure
    """

    # Execute delete query
    affected = execute(
        "DELETE FROM books WHERE book_id = %s",
        (book_id,)
    )

    # If no rows were affected, book does not exist
    if affected == 0:
        return "❌ Book not found"

    # Confirm deletion
    return "🗑️ Book deleted successfully"


def import_books_csv(file_stream):
    """
    Imports books from a CSV file stream.
    Expected columns: Title, Author, Category, Copies
    """
    import pandas as pd
    import io
    
    try:
        # Read CSV
        df = pd.read_csv(file_stream)
        
        # Normalize headers: strip space, lower case
        df.columns = [c.strip().lower() for c in df.columns]
        
        required = {'title', 'author', 'category', 'copies'}
        if not required.issubset(df.columns):
            return f"❌ CSV missing required columns: {required - set(df.columns)}"
            
        success_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                title = str(row['title']).strip()
                author = str(row['author']).strip()
                category = str(row['category']).strip()
                copies = int(row['copies'])
                
                if copies < 1:
                    errors.append(f"Row {index+1}: Copies must be > 0")
                    continue
                    
                # Call add_book
                add_book(title, author, category, copies)
                success_count += 1
                
            except Exception as row_err:
                errors.append(f"Row {index+1}: {str(row_err)}")
                
        result = f"✅ Imported {success_count} books."
        if errors:
            result += f" ( {len(errors)} failed inputs)"
            # Optionally log errors
            
        return result
        
    except Exception as e:
        return f"❌ Import failed: {str(e)}"

def get_all_authors():
    """Returns authors from the normalized authors table."""
    return fetch_all("SELECT * FROM authors ORDER BY name ASC")

def get_all_categories():
    return fetch_all("SELECT DISTINCT category FROM books ORDER BY category")
