"""
analytics_service.py
--------------------
Handles in-memory analytics using Pandas.

This module is READ-ONLY and analytical in nature.

Responsibilities:
- Search
- Sort
- Filter
- Read-only analytics
- NO writes to database
- NO Flask routes
- NO business rules

Used by:
- CLI
- Admin dashboards
- Reports / exports
"""

# ===============================
# IMPORTS
# ===============================

from typing import Optional
# Optional → used for type hinting clarity (future extensibility)

import pandas as pd
# pandas → used for in-memory analytics (filtering, sorting, grouping)

from backend.repository.db_access import fetch_all
# fetch_all → fetches multiple rows from database (SELECT queries)


# ==========================================================
# INTERNAL HELPER FUNCTION
# ==========================================================

def _get_books_df() -> pd.DataFrame:
    """
    Fetches all books from the database and converts them
    into a Pandas DataFrame.

    This is a PRIVATE helper function (internal use only).

    Returns:
        pd.DataFrame:
        - Always returns a DataFrame
        - Returns empty DataFrame with schema if no data exists
    """

    # Fetch all book records from database
    data = fetch_all("SELECT * FROM books")

    # If database table is empty
    if not data:
        # Return empty DataFrame with predefined columns
        # This prevents runtime errors in Pandas operations
        return pd.DataFrame(
            columns=[
                "book_id",
                "title",
                "author",
                "category",
                "total_copies",
                "available_copies"
            ]
        )

    # Convert list of dictionaries into DataFrame
    return pd.DataFrame(data)


# ==========================================================
# SEARCH OPERATIONS
# ==========================================================

def search_by_title(keyword: str) -> pd.DataFrame:
    """
    Search books by title (case-insensitive).

    Args:
        keyword (str): Search text

    Returns:
        pd.DataFrame: Matching book records
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Filter rows where title contains keyword
    return df[df["title"].str.contains(keyword, case=False, na=False)]


def search_by_author(author: str) -> pd.DataFrame:
    """
    Search books by author name (case-insensitive).

    Args:
        author (str): Author name or partial name

    Returns:
        pd.DataFrame
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Filter rows by author column
    return df[df["author"].str.contains(author, case=False, na=False)]


def search_by_category(category: str) -> pd.DataFrame:
    """
    Search books by category (case-insensitive).

    Args:
        category (str): Category name

    Returns:
        pd.DataFrame
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Filter rows by category column
    return df[df["category"].str.contains(category, case=False, na=False)]


# ==========================================================
# SORT OPERATIONS
# ==========================================================

def sort_by_availability() -> pd.DataFrame:
    """
    Sort books by available copies (highest first).

    Returns:
        pd.DataFrame
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Sort by available_copies column in descending order
    return df.sort_values(by="available_copies", ascending=False)


def sort_by_author() -> pd.DataFrame:
    """
    Sort books alphabetically by author name.

    Returns:
        pd.DataFrame
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Sort by author column alphabetically
    return df.sort_values(by="author")


def sort_by_popularity() -> pd.DataFrame:
    """
    Sort books by how many times they were issued.

    Uses SQL aggregation and then converts results
    into a Pandas DataFrame.

    Returns:
        pd.DataFrame
    """

    # Fetch aggregated issue data from database
    data = fetch_all(
        """
        SELECT
            b.book_id,
            b.title,
            b.author,
            b.category,
            b.total_copies,
            b.available_copies,
            COUNT(i.issue_id) AS times_issued
        FROM books b
        LEFT JOIN issues i ON b.book_id = i.book_id
        GROUP BY b.book_id
        ORDER BY times_issued DESC
        """
    )

    # If no issue data exists
    if not data:
        # Return empty DataFrame with schema
        return pd.DataFrame(
            columns=[
                "book_id",
                "title",
                "author",
                "category",
                "total_copies",
                "available_copies",
                "times_issued"
            ]
        )

    # Convert result set into DataFrame
    return pd.DataFrame(data)


# ==========================================================
# FILTER OPERATIONS
# ==========================================================

def available_books() -> pd.DataFrame:
    """
    Returns books that currently have at least one available copy.

    Returns:
        pd.DataFrame
    """

    # Load books into DataFrame
    df = _get_books_df()

    # Filter books with available copies > 0
    return df[df["available_copies"] > 0]


def overdue_books(max_days: int = 7) -> pd.DataFrame:
    """
    Returns overdue books (not returned after allowed days).

    Args:
        max_days (int): Allowed issue duration before overdue

    Returns:
        pd.DataFrame
    """

    # Fetch all active (not returned) issues
    data = fetch_all(
        """
        SELECT
            i.issue_id,
            u.name AS user_name,
            b.title AS book_title,
            i.issue_date
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL
        """
    )

    # If no active issues exist
    if not data:
        # Return empty DataFrame with schema
        return pd.DataFrame(
            columns=[
                "issue_id",
                "user_name",
                "book_title",
                "issue_date",
                "days_overdue"
            ]
        )

    # Convert result set into DataFrame
    df = pd.DataFrame(data)

    # Convert issue_date column to datetime safely
    df["issue_date"] = pd.to_datetime(df["issue_date"])

    # Calculate overdue days
    df["days_overdue"] = (
        pd.Timestamp.today() - df["issue_date"]
    ).dt.days - max_days

    # Return only overdue records
    return df[df["days_overdue"] > 0]
