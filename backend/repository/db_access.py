# ===============================
# REPOSITORY / DATA ACCESS LAYER
# ===============================
# This file acts as the ONLY layer that talks directly to the database.
# All SQL queries from services and routes pass through this file.
# This keeps database logic centralized and maintainable.

from backend.config.db import get_connection
# get_connection() is imported from db.py
# It is responsible ONLY for opening a database connection


# ===============================
# READ OPERATIONS
# ===============================

def fetch_all(query, params=None):
    """
    Fetch multiple rows from the database.

    Used for:
    - SELECT queries that return many rows
    - Lists (users, books, issues, reports, etc.)
    """

    # Create a new database connection
    conn = get_connection()

    # Create a cursor that returns rows as dictionaries
    # Example: {"user_id": 1, "name": "Admin"}
    cursor = conn.cursor(dictionary=True)

    try:
        # Execute the SQL query
        # params are safely injected to prevent SQL injection
        cursor.execute(query, params or ())

        # Fetch all matching rows from the database
        return cursor.fetchall()

    finally:
        # Always close cursor to free DB resources
        cursor.close()

        # Always close connection to avoid connection leaks
        conn.close()


def fetch_one(query, params=None):
    """
    Fetch a single row from the database.

    Used for:
    - Login checks
    - Fetching one user/book/issue by ID
    - Validations
    """

    # Create a new database connection
    conn = get_connection()

    # Create a dictionary cursor
    cursor = conn.cursor(dictionary=True)

    try:
        # Execute SQL query with parameters
        cursor.execute(query, params or ())

        # Fetch exactly one row (or None if no match)
        return cursor.fetchone()

    finally:
        # Close cursor
        cursor.close()

        # Close database connection
        conn.close()


# ===============================
# WRITE OPERATIONS
# ===============================

def execute(query, params=None):
    """
    Execute INSERT, UPDATE, or DELETE queries.

    Used for:
    - Creating users
    - Updating passwords
    - Issuing / returning books
    - Deleting records
    """

    # Create a new database connection
    conn = get_connection()

    # Cursor without dictionary mode (not needed for writes)
    cursor = conn.cursor()

    try:
        # Execute write query safely with parameters
        cursor.execute(query, params or ())

        # Commit the transaction to persist changes
        conn.commit()

        # Return number of affected rows
        return cursor.rowcount

    except Exception:
        # Roll back transaction if ANY error occurs
        # This protects data consistency
        conn.rollback()

        # Re-raise exception so caller knows something failed
        raise

    finally:
        # Close cursor
        cursor.close()

        # Close database connection
        conn.close()
