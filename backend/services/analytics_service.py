
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
