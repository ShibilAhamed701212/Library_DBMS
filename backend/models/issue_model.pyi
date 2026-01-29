"""
issue.py
---------
Domain model for Issue record.

Purpose:
- Represents a book issue / borrowing record
- Pure data container (NO database queries)
- Used across services, analytics, and views
"""

# ===============================
# IMPORTS
# ===============================

# dataclass simplifies class creation by auto-generating
# __init__, __repr__, __eq__, etc.
from dataclasses import dataclass

# date is used to represent issue and return dates
from datetime import date


# ===============================
# DOMAIN MODEL
# ===============================

@dataclass
class Issue:
    """
    Issue domain object.

    Represents one row from the `issues` table.
    Tracks when a book was issued, returned, and any fine incurred.

    This class:
    - Does NOT talk to the database
    - Does NOT calculate fines
    - Only stores structured data
    """

    # Unique identifier for the issue record (Primary Key)
    issue_id: int

    # ID of the user who issued the book (Foreign Key → users.user_id)
    user_id: int

    # ID of the issued book (Foreign Key → books.book_id)
    book_id: int

    # Date when the book was issued
    issue_date: date

    # Date when the book was returned
    # Can be None if the book is not yet returned
    return_date: date | None

    # Fine amount charged for late return (0 if none)
    fine: int
