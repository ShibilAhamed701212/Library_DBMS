from backend.repository.db_access import execute, fetch_all, fetch_one
from backend.services.chat_service import get_or_create_dm_room

def send_friend_request(sender_id, search_query):
    """Sends a friend request from one user to another. search_query can be user_id or anon_id."""
    
    # Resolve receiver_id
    receiver_id = None
    
    # 1. Try as direct user_id (if numeric)
    if str(search_query).isdigit():
        receiver = fetch_one("SELECT user_id FROM users WHERE user_id = %s", (search_query,))
        if receiver:
            receiver_id = receiver['user_id']
            
    # 2. Try as anon_id
    if not receiver_id:
        anon_map = fetch_one("SELECT user_id FROM chat_anon_id WHERE anon_id = %s", (search_query,))
        if anon_map:
            receiver_id = anon_map['user_id']
            
    if not receiver_id:
        raise Exception("User not found")

    # Check privacy settings
    receiver_data = fetch_one("SELECT allow_requests FROM users WHERE user_id = %s", (receiver_id,))
    if receiver_data and receiver_data.get('allow_requests') == 0:
        raise Exception("This user is not accepting friend requests")

    if sender_id == receiver_id:
        raise Exception("You cannot add yourself as a friend")
    
    # Check if a request already exists
    existing = fetch_one(
        "SELECT id, status FROM friend_requests WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)",
        (sender_id, receiver_id, receiver_id, sender_id)
    )
    
    if existing:
        if existing['status'] == 'accepted':
            raise Exception("You are already friends")
        if existing['status'] == 'pending':
            raise Exception("A friend request is already pending")
        # If rejected, we allow a new one? Or just update it? Let's just allow a new one by deleting old
        execute("DELETE FROM friend_requests WHERE id = %s", (existing['id'],))

    execute(
        "INSERT INTO friend_requests (sender_id, receiver_id, status) VALUES (%s, %s, 'pending')",
        (sender_id, receiver_id)
    )
    return True

def get_pending_requests(user_id):
    """Gets all pending friend requests for a user."""
    return fetch_all("""
        SELECT f.id, f.sender_id, u.name as sender_name, u.profile_pic as sender_pic
        FROM friend_requests f
        JOIN users u ON f.sender_id = u.user_id
        WHERE f.receiver_id = %s AND f.status = 'pending'
    """, (user_id,))

def get_friends_list(user_id):
    """Gets the list of friends for a user."""
    return fetch_all("""
        SELECT 
            CASE 
                WHEN sender_id = %s THEN receiver_id 
                ELSE sender_id 
            END as friend_id,
            u.name, u.profile_pic, u.email
        FROM friend_requests f
        JOIN users u ON u.user_id = CASE WHEN f.sender_id = %s THEN f.receiver_id ELSE f.sender_id END
        WHERE (sender_id = %s OR receiver_id = %s) AND status = 'accepted'
    """, (user_id, user_id, user_id, user_id))

def respond_to_friend_request(request_id, current_user_id, status):
    """Accepts or rejects a friend request."""
    if status not in ['accepted', 'rejected']:
        raise Exception("Invalid status")
    
    request = fetch_one("SELECT * FROM friend_requests WHERE id = %s AND receiver_id = %s", (request_id, current_user_id))
    if not request:
        raise Exception("Request not found")
    
    execute("UPDATE friend_requests SET status = %s WHERE id = %s", (status, request_id))
    
    if status == 'accepted':
        # Automatically create/join a DM room
        get_or_create_dm_room(request['sender_id'], request['receiver_id'])
        
    return True

    return True

def update_privacy_settings(user_id, is_public, allow_requests, show_activity):
    """Updates user granular privacy settings."""
    try:
        val_public = 1 if is_public else 0
        val_requests = 1 if allow_requests else 0
        val_activity = 1 if show_activity else 0
        
        execute("""
            UPDATE users 
            SET is_public = %s, allow_requests = %s, show_activity = %s 
            WHERE user_id = %s
        """, (val_public, val_requests, val_activity, user_id))
        
        return "✅ Privacy settings updated."
    except Exception as e:
        return f"❌ Error updating privacy: {str(e)}"

def get_leaderboard(limit=50):
    """
    Fetches top readers for the leaderboard.
    Only includes users with is_public = 1.
    """
    from datetime import datetime
    year = datetime.now().year
    
    return fetch_all("""
        SELECT 
            u.user_id, u.name, u.profile_pic, u.tier,
            COALESCE(rg.current_books, 0) as books_read,
            COALESCE(rg.goal_books, 0) as goal_books
        FROM users u
        LEFT JOIN reading_goals rg ON u.user_id = rg.user_id AND rg.year = %s
        WHERE u.is_public = 1
        ORDER BY books_read DESC, goal_books DESC
        LIMIT %s
    """, (year, limit))

def get_public_profile(target_user_id, viewer_id):
    """
    Fetches public profile data if the user is public.
    """
    # 1. Fetch User Basics & Privacy
    query = """
        SELECT user_id, name, bio, profile_pic, tier, created_at, 
               is_public, allow_requests, show_activity
        FROM users WHERE user_id = %s
    """
    user = fetch_one(query, (target_user_id,))
    
    if not user:
        return None, "User not found"
        
    if user['is_public'] == 0 and user['user_id'] != viewer_id:
        return None, "This profile is private."
        
    # 2. Fetch Reading Stats (Current Year)
    from datetime import datetime
    year = datetime.now().year
    goal = fetch_one("SELECT * FROM reading_goals WHERE user_id = %s AND year = %s", (target_user_id, year))
    
    # 3. Check Friendship Status
    friend_status = "none"
    if viewer_id:
         f_req = fetch_one("""
            SELECT status, sender_id FROM friend_requests 
            WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s)
         """, (viewer_id, target_user_id, target_user_id, viewer_id))
         
         if f_req:
             if f_req['status'] == 'accepted':
                 friend_status = "friends"
             elif f_req['status'] == 'pending':
                 friend_status = "sent" if f_req['sender_id'] == viewer_id else "received"

    return {
        "user": user,
        "goal": goal,
        "friend_status": friend_status
    }, None
