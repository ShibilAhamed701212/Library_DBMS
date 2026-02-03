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
