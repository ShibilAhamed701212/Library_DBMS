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

def add_book(title: str, author: str, category: str, total_copies: int):
    """
    Adds a new book to the library.

    Rules:
    - total_copies must be positive
    - available_copies initially equals total_copies
    """

    # -----------------------------
    # BASIC VALIDATION
    # -----------------------------

    # Ensure total copies is a positive number
    if total_copies <= 0:
        return "❌ Total copies must be positive"

    # -----------------------------
    # INSERT BOOK RECORD
    # -----------------------------

    # Insert new book into database
    execute(
        """
        INSERT INTO books
            (title, author, category, total_copies, available_copies)
        VALUES
            (%s, %s, %s, %s, %s)
        """,
        # available_copies starts equal to total_copies
        (title, author, category, total_copies, total_copies)
    )

    # Confirm successful insertion
    return "✅ Book added successfully"


# ===============================
# VIEW ALL BOOKS (PAGINATED & SEARCHABLE)
# ===============================

def view_books_paginated(page: int = 1, per_page: int = 10, search_query: str = ""):
    """
    Fetches books with pagination and server-side filtering.
    
    Args:
        page (int): Current page number
        per_page (int): Records per page
        search_query (str): Keyword for title, author, or category
        
    Returns:
        dict: { books, total, page, total_pages }
    """
    offset = (page - 1) * per_page
    
    # Build dynamic query for data
    query = "SELECT * FROM books"
    params = []
    
    if search_query:
        query += " WHERE title LIKE %s OR author LIKE %s OR category LIKE %s"
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])
        
    query += " ORDER BY title ASC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])
    
    books = fetch_all(query, tuple(params))
    
    # Build query for total count
    count_query = "SELECT COUNT(*) AS c FROM books"
    count_params = []
    
    if search_query:
        count_query += " WHERE title LIKE %s OR author LIKE %s OR category LIKE %s"
        count_params.extend([pattern, pattern, pattern])
        
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
    Fetch a single book by its ID.

    Args:
        book_id (int): Primary key of the book

    Returns:
        dict or None
    """

    # Retrieve book record matching given ID
    return fetch_one(
        "SELECT * FROM books WHERE book_id = %s",
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
