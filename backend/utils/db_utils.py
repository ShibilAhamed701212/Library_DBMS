"""
db_utils.py
-----------
Database utility functions including context managers for database operations.
"""

from contextlib import contextmanager
from typing import Any, Iterator, Optional
import logging
from mysql.connector import Error as MySQLError
from mysql.connector.connection import MySQLConnection

from backend.config.db import get_connection

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection() -> Iterator[MySQLConnection]:
    """
    Context manager for database connections.
    
    Ensures proper connection handling and cleanup.
    
    Yields:
        MySQLConnection: A database connection from the pool.
        
    Raises:
        RuntimeError: If connection cannot be established.
    """
    conn = None
    try:
        conn = get_connection()
        yield conn
    except MySQLError as e:
        logger.error(f"Database error: {e}")
        raise RuntimeError("Database operation failed") from e
    finally:
        if conn and conn.is_connected():
            conn.close()

@contextmanager
def transaction() -> Iterator[MySQLConnection]:
    """
    Context manager for database transactions.
    
    Handles transaction commit/rollback automatically.
    
    Yields:
        MySQLConnection: A database connection for the transaction.
        
    Raises:
        RuntimeError: If transaction fails.
    """
    with get_db_connection() as conn:
        try:
            conn.start_transaction()
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed: {e}")
            raise RuntimeError("Transaction failed") from e

def execute_query(query: str, params: Optional[tuple] = None, fetch: bool = True) -> Any:
    """
    Execute a database query with parameters.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        fetch: Whether to fetch results (for SELECT queries)
        
    Returns:
        Query results if fetch=True, otherwise None
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            if fetch and cursor.with_rows:
                return cursor.fetchall()
            return None
        except MySQLError as e:
            logger.error(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            raise
        finally:
            cursor.close()
