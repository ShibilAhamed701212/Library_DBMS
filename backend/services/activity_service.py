
from backend.repository.db_access import execute_query, fetch_all

def log_user_activity(user_id, activity_type, description):
    try:
        execute_query(
            "INSERT INTO user_activities (user_id, activity_type, description) VALUES (%s, %s, %s)",
            (user_id, activity_type, description)
        )
    except Exception as e:
        print(f"Failed to log user activity: {e}")

def get_user_activities(user_id, limit=10):
    return fetch_all(
        "SELECT * FROM user_activities WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
        (user_id, limit)
    )
