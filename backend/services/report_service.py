"""
report_service.py
-----------------
Handles reporting and export functionality using Pandas.

Purpose:
- Generate analytical reports from database data
- Convert SQL results into Pandas DataFrames
- Export reports into CSV and Excel formats

This module is:
- READ-ONLY with respect to database
- Used by admin dashboards, reports pages, and CLI
"""

# ===============================
# IMPORTS
# ===============================

import os
# os → used for directory creation and file path handling

import pandas as pd
# pandas → used for DataFrame-based analytics and exports

from backend.repository.db_access import fetch_all
# fetch_all → executes SELECT queries and returns list of dicts


# ===============================
# EXPORT CONFIGURATION
# ===============================

# Base directory where exported reports will be stored
EXPORT_PATH = "backend/data_exports"


# ==============================
# CORE REPORTS
# ==============================

def most_issued_books():
    """
    Returns books ordered by issue count.

    Report purpose:
    - Identify most popular books
    - Used for analytics and admin insights

    Returns:
        pandas.DataFrame with:
        - title
        - issue_count
    """

    # Execute SQL query to count issues per book
    data = fetch_all(
        """
        SELECT
            b.title,                   -- Book title
            COUNT(i.issue_id) AS issue_count  -- Number of times issued
        FROM issues i
        JOIN books b ON i.book_id = b.book_id
        GROUP BY b.book_id
        ORDER BY issue_count DESC
        """
    )

    # Convert raw DB result into DataFrame
    return pd.DataFrame(data)


def most_active_users():
    """
    Returns users ordered by number of issues.

    Report purpose:
    - Identify most active library members
    - Useful for engagement analysis

    Returns:
        pandas.DataFrame with:
        - name
        - total_issues
    """

    # Execute SQL query to count issues per user
    data = fetch_all(
        """
        SELECT
            u.name,                    -- User name
            COUNT(i.issue_id) AS total_issues  -- Total books issued
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        GROUP BY u.user_id
        ORDER BY total_issues DESC
        """
    )

    # Convert query result to DataFrame
    return pd.DataFrame(data)


def monthly_issue_count():
    """
    Returns monthly issue statistics.

    Report purpose:
    - Track library usage trends over time
    - Useful for charts and reports

    Returns:
        pandas.DataFrame with:
        - month (YYYY-MM)
        - total_issues
    """

    # Execute SQL query to aggregate issues by month
    data = fetch_all(
        """
        SELECT
            DATE_FORMAT(issue_date, '%Y-%m') AS month,  -- Year-Month format
            COUNT(*) AS total_issues                    -- Total issues in that month
        FROM issues
        GROUP BY month
        ORDER BY month
        """
    )

    # Convert result into DataFrame
    return pd.DataFrame(data)


def book_category_distribution():
    """
    Returns count of books per category.
    
    Returns:
        pd.DataFrame with:
        - category
        - book_count
    """
    data = fetch_all(
        """
        SELECT category, COUNT(*) AS book_count
        FROM books
        GROUP BY category
        """
    )
    return pd.DataFrame(data)


# ==============================
# EXPORT UTILITIES
# ==============================

def export_report(df: pd.DataFrame, filename: str):
    """
    Exports a DataFrame to CSV and Excel formats.

    Responsibilities:
    - Create export directories if missing
    - Save report in two formats
    - Keep filenames consistent

    Args:
        df (pd.DataFrame): Report data
        filename (str): Base filename without extension

    Returns:
        str: Success message
    """

    # Ensure CSV export directory exists
    os.makedirs(f"{EXPORT_PATH}/csv", exist_ok=True)

    # Ensure Excel export directory exists
    os.makedirs(f"{EXPORT_PATH}/excel", exist_ok=True)

    # Export DataFrame as CSV (no index column)
    df.to_csv(
        f"{EXPORT_PATH}/csv/{filename}.csv",
        index=False
    )

    # Export DataFrame as Excel (no index column)
    df.to_excel(
        f"{EXPORT_PATH}/excel/{filename}.xlsx",
        index=False
    )

    # Return confirmation message
    return f"✅ Report exported: {filename}"
