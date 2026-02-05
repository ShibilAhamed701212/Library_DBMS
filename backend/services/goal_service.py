
from datetime import datetime
from backend.repository.db_access import fetch_one, execute

def get_or_create_goal(user_id):
    """Fetches the current year's reading goal for a user (including tier & privacy), creating goal if missing."""
    year = datetime.now().year
    query = """
    SELECT rg.*, u.tier, u.is_public, u.allow_requests, u.show_activity
    FROM reading_goals rg
    JOIN users u ON rg.user_id = u.user_id
    WHERE rg.user_id = %s AND rg.year = %s
    """
    goal = fetch_one(query, (user_id, year))
    
    if not goal:
        execute("INSERT INTO reading_goals (user_id, year, goal_books) VALUES (%s, %s, 12)", (user_id, year))
        goal = fetch_one(query, (user_id, year))
    
    return goal

def update_goal_target(user_id, target):
    """Allows user to set their personal reading target for the current year."""
    year = datetime.now().year
    execute("UPDATE reading_goals SET goal_books = %s WHERE user_id = %s AND year = %s", (target, user_id, year))
    return "✅ Reading goal updated!"

def increment_goal_progress(user_id):
    """Increments the current reading count by 1."""
    year = datetime.now().year
    # Ensure goal exists first
    get_or_create_goal(user_id)
    execute("UPDATE reading_goals SET current_books = current_books + 1 WHERE user_id = %s AND year = %s", (user_id, year))
