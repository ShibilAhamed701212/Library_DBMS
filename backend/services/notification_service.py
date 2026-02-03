
from backend.repository.db_access import execute_query, fetch_all

def add_notification(user_id, message):
    try:
        execute_query(
            "INSERT INTO notifications (user_id, message) VALUES (%s, %s)",
            (user_id, message)
        )
    except Exception as e:
        print(f"Failed to add notification: {e}")

def get_unread_notifications(user_id):
    return fetch_all(
        """
        SELECT * FROM notifications 
        WHERE user_id = %s AND is_read = FALSE
        ORDER BY created_at DESC
        """,
        (user_id,)
    )

def mark_notification_read(notification_id, user_id):
    execute_query("UPDATE notifications SET is_read = TRUE WHERE notification_id = %s AND user_id = %s", (notification_id, user_id))

def mark_all_read(user_id):
    execute_query("UPDATE notifications SET is_read = TRUE WHERE user_id = %s", (user_id,))
