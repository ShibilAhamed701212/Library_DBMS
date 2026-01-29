"""
book.py
--------
Domain model for Book.

Purpose:
- Represents a Book as a pure data object
- Contains NO database logic
- Contains NO business rules
- Used for clean data transfer between layers
"""

# ===============================
# IMPORTS
# ===============================

# dataclass is used to automatically generate:
# - __init__()
# - __repr__()
# - __eq__()
# and other boilerplate methods
from dataclasses import dataclass


# ===============================
# DOMAIN MODEL
# ===============================

@dataclass
class Book:
    """
    Book domain object.

    This class represents a single book record in the system.
    It mirrors the structure of the `books` table in the database
    but is NOT tied to database operations.

    Used for:
    - Clean data representation
    - Type safety
    - Readability
    - Passing data between services, repository, and views
    """

    # Unique identifier for the book (Primary Key)
    book_id: int

    # Title of the book
    title: str

    # Author name
    author: str

    # Category / genre of the book
    category: str

    # Total number of copies owned by the library
    total_copies: int

    # Number of copies currently available for issue
    available_copies: int
