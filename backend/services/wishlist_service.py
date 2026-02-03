
from backend.repository.db_access import execute_query, fetch_all

def add_to_wishlist(user_id, book_id):
    try:
        execute_query(
            "INSERT INTO wishlist (user_id, book_id) VALUES (%s, %s)",
            (user_id, book_id)
        )
        # Activity Log
        from backend.services.activity_service import log_user_activity
        log_user_activity(user_id, "WISHLIST", f"Added book #{book_id} to wishlist")
        
        return "✅ Added to wishlist"
    except Exception as e:
        if "Duplicate" in str(e):
            return "⚠️ Already in wishlist"
        return f"❌ Failed to add: {str(e)}"

def remove_from_wishlist(user_id, book_id):
    execute_query("DELETE FROM wishlist WHERE user_id = %s AND book_id = %s", (user_id, book_id))
    return "✅ Removed from wishlist"

def get_user_wishlist(user_id):
    return fetch_all(
        """
        SELECT b.*, w.added_at 
        FROM wishlist w
        JOIN books b ON w.book_id = b.book_id
        WHERE w.user_id = %s
        ORDER BY w.added_at DESC
        """,
        (user_id,)
    )
