
from backend.repository.db_access import execute_query, fetch_all

def log_action(admin_id, action, details=None):
    """
    Logs an administrative action.
    """
    try:
        execute_query(
            "INSERT INTO audit_logs (admin_id, action, details) VALUES (%s, %s, %s)",
            (admin_id, action, details)
        )
    except Exception as e:
        print(f"❌ Failed to log action: {e}")

def get_audit_logs(limit=50):
    """
    Fetches recent audit logs.
    """
    return fetch_all(
        """
        SELECT l.log_id, u.name AS admin_name, l.action, l.details, l.timestamp
        FROM audit_logs l
        JOIN users u ON l.admin_id = u.user_id
        ORDER BY l.timestamp DESC
        LIMIT %s
        """,
        (limit,)
    )
