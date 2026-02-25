
from backend.repository.db_access import fetch_all, fetch_one

def get_monthly_borrowing_stats():
    """Returns number of books issued per month for the last 6 months."""
    return fetch_all("""
        SELECT 
            DATE_FORMAT(issue_date, '%b %Y') as month,
            COUNT(*) as count
        FROM issues
        WHERE issue_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY month
        ORDER BY MIN(issue_date) ASC
    """)

def get_category_stats():
    """Returns total books and total issues per category."""
    return fetch_all("""
        SELECT 
            b.category,
            COUNT(DISTINCT b.book_id) as total_books,
            COUNT(i.issue_id) as total_issues
        FROM books b
        LEFT JOIN issues i ON b.book_id = i.book_id
        GROUP BY b.category
        ORDER BY total_issues DESC
        LIMIT 10
    """)

def get_user_engagement_stats():
    """Returns user breakdown based on activity."""
    return fetch_all("""
        SELECT 
            role,
            COUNT(*) as count
        FROM users
        GROUP BY role
    """)

def get_quick_stats():
    """Returns card-style stats for the dashboard overview."""
    books = fetch_one("SELECT COUNT(*) as c FROM books")
    users = fetch_one("SELECT COUNT(*) as c FROM users")
    issues = fetch_one("SELECT COUNT(*) as c FROM issues")
    fines = fetch_one("SELECT SUM(fine) as s FROM issues")
    
    return {
        "total_books": books['c'],
        "total_users": users['c'],
        "total_issues": issues['c'],
        "total_fines": fines['s'] or 0
    }


# ===============================
# CLI ANALYTICS (Pandas-powered)
# ===============================

def search_by_title(keyword):
    """Searches books by title keyword, returns a Pandas DataFrame."""
    import pandas as pd
    rows = fetch_all(
        """
        SELECT b.book_id, b.title, COALESCE(a.name, 'Unknown') as author, 
               b.category, b.available_copies
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        WHERE b.title LIKE %s
        ORDER BY b.title
        """,
        (f"%{keyword}%",)
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def available_books():
    """Returns all books with available_copies > 0 as a Pandas DataFrame."""
    import pandas as pd
    rows = fetch_all(
        """
        SELECT b.book_id, b.title, COALESCE(a.name, 'Unknown') as author, 
               b.category, b.available_copies
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        WHERE b.available_copies > 0
        ORDER BY b.title
        """
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def overdue_books():
    """Returns all currently overdue issues as a Pandas DataFrame."""
    import pandas as pd
    rows = fetch_all(
        """
        SELECT i.issue_id, u.name as user_name, b.title, i.issue_date,
               DATEDIFF(CURDATE(), i.issue_date) as days_held
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL
          AND DATEDIFF(CURDATE(), i.issue_date) > 14
        ORDER BY days_held DESC
        """
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()
