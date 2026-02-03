import random
import string
from backend.repository.db_access import fetch_one, fetch_all, execute

def generate_anon_id():
    """Generates a random anonymous ID like 'anon_9fA32X'."""
    suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"anon_{suffix}"

def get_or_create_anon_id(user_id):
    """
    Retrieves the existing anonymous ID for a user, or creates a new one.
    """
    # Check if exists
    existing = fetch_one("SELECT anon_id FROM chat_anon_id WHERE user_id = %s", (user_id,))
    if existing:
        return existing['anon_id']
    
    # Create new (retry if collision, though unlikely)
    for _ in range(3):
        new_id = generate_anon_id()
        try:
            execute(
                "INSERT INTO chat_anon_id (anon_id, user_id) VALUES (%s, %s)",
                (new_id, user_id)
            )
            return new_id
        except Exception:
            continue # Retry
            
    raise Exception("Failed to generate unique Anonymous ID")

def create_room(user_id, name, room_type):
    """
    Creates a new chat room and adds the creator as 'admin'.
    """
    # 1. Create Room
    execute(
        "INSERT INTO chat_rooms (room_name, room_type, created_by) VALUES (%s, %s, %s)",
        (name, room_type, user_id)
    )
    
    # Get the ID (Warning: fetch_one("SELECT LAST_INSERT_ID()") is safer in same transaction, 
    # but db_access.execute commits immediately. We will query by name/creator/time or use max ID)
    # Ideally db_access should return lastrowid. Inspecting db_access execute... it returns rowcount.
    # We will query max_id for this user.
    room = fetch_one(
        "SELECT room_id FROM chat_rooms WHERE created_by = %s ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    if not room:
        raise Exception("Room creation failed")
    
    room_id = room['room_id']
    
    # 2. Add Creator as Admin
    # First get their anon ID
    anon_id = get_or_create_anon_id(user_id)
    
    join_room_internal(room_id, anon_id, role='admin')
    
    return room_id

def join_room(user_id, room_id, role='member'):
    """
    Public method for a user to join a room.
    """
    room = fetch_one("SELECT room_type FROM chat_rooms WHERE room_id = %s", (room_id,))
    if not room:
        raise Exception("Channel not found")
    
    if room['room_type'] != 'public':
        raise Exception("Unauthorized: This channel is private")

    anon_id = get_or_create_anon_id(user_id)
    return join_room_internal(room_id, anon_id, role)

def join_room_internal(room_id, anon_id, role='member'):
    """
    Adds an anon user to a room. Handles re-joining.
    """
    # Check if already member
    existing = fetch_one(
        "SELECT * FROM room_members WHERE room_id = %s AND anon_id = %s",
        (room_id, anon_id)
    )
    if existing:
        return True # Already there
        
    execute(
        "INSERT INTO room_members (room_id, anon_id, role) VALUES (%s, %s, %s)",
        (room_id, anon_id, role)
    )
    return True

def save_message(user_id, channel_id, text=None, file_path=None, sender_type='anon', reply_to_id=None):
    """
    Saves a message (text or file) from a user to a channel.
    Matches the updated 'channel_id' schema.
    """
    anon_id = get_or_create_anon_id(user_id)
    
    if text is None:
        text = ""

    execute(
        """
        INSERT INTO chat_messages (channel_id, anon_id, message_text, file_url, sender_type, reply_to_id) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (channel_id, anon_id, text, file_path, sender_type, reply_to_id)
    )
    
    # Return the message object for broadcasting
    return {
        "channel_id": channel_id,
        "anon_id": anon_id,
        "message_text": text,
        "file_url": file_path,
        "sender_type": sender_type,
        "reply_to_id": reply_to_id
    }

def edit_message(user_id, message_id, new_text):
    anon_id = get_or_create_anon_id(user_id)
    
    # Verify ownership
    msg = fetch_one("SELECT * FROM chat_messages WHERE message_id = %s", (message_id,))
    if not msg:
        raise Exception("Message not found")
        
    if msg['anon_id'] != anon_id:
        raise Exception("Unauthorized")
        
    execute(
        "UPDATE chat_messages SET message_text = %s, is_edited = TRUE WHERE message_id = %s",
        (new_text, message_id)
    )
    return True

def delete_message(user_id, message_id):
    anon_id = get_or_create_anon_id(user_id)
    
    # Verify ownership or admin
    msg = fetch_one("SELECT * FROM chat_messages WHERE message_id = %s", (message_id,))
    if not msg:
        raise Exception("Message not found")
        
    if msg['anon_id'] != anon_id:
        # Allow room admin to delete?
        member = fetch_one("SELECT role FROM room_members WHERE room_id = %s AND anon_id = %s", (msg['room_id'], anon_id))
        if not member or member['role'] not in ['admin', 'moderator']:
             raise Exception("Unauthorized")

    execute("UPDATE chat_messages SET is_deleted = TRUE WHERE message_id = %s", (message_id,))
    return True

def invite_user_to_room(room_id, email, requester_id):
    """Invites a user by email to a private room."""
    # Logic: Find user by email, generate invite or force join
    user = fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
    if not user:
        raise Exception("User not found")
        
    target_user_id = user['user_id']
    
    # Check requester permissions (must be member/admin of room)
    # For now, allow any member to invite? Or just admins?
    # Let's say any member for now.
    
    send_notification = True # We should notify them
    
    # Add to room members directly
    target_anon_id = get_or_create_anon_id(target_user_id)
    join_room_internal(room_id, target_anon_id, role='member')
    
    return True

def get_public_rooms():
    return fetch_all("SELECT * FROM chat_rooms WHERE room_type = 'public' ORDER BY created_at DESC")

def get_my_rooms(user_id):
    anon_id = get_or_create_anon_id(user_id)
    rooms = fetch_all("""
        SELECT r.*, m.role as user_role
        FROM chat_rooms r
        JOIN room_members m ON r.room_id = m.room_id
        WHERE m.anon_id = %s
    """, (anon_id,))
    
    # Enrich private rooms with peer info
    for room in rooms:
        # Only override name for DMs (which default to "Direct Message")
        # Custom private groups should keep their names
        if room['room_type'] == 'private' and room['room_name'] == 'Direct Message':
            # Find the other member (peer)
            peer = fetch_one("""
                SELECT u.name, u.profile_pic, ca.anon_id
                FROM room_members rm
                JOIN chat_anon_id ca ON rm.anon_id = ca.anon_id
                JOIN users u ON ca.user_id = u.user_id
                WHERE rm.room_id = %s AND rm.anon_id != %s
                LIMIT 1
            """, (room['room_id'], anon_id))
            
            if peer:
                room['room_name'] = peer['name']
                room['room_avatar'] = peer['profile_pic']
                room['peer_anon_id'] = peer['anon_id']
                # Expose real user_id to frontend for matching with friend list
                room['peer_user_id'] = fetch_one("SELECT user_id FROM chat_anon_id WHERE anon_id = %s", (peer['anon_id'],))['user_id']
            else:
                 room['room_name'] = "Unknown User"

    return rooms

def update_room(user_id, room_id, name, description, avatar_path=None):
    """Updates room details if the user is the creator."""
    # Verify permissions
    room = fetch_one("SELECT * FROM chat_rooms WHERE room_id = %s", (room_id,))
    if not room:
        raise Exception("Room not found")
        
    # Check if user is owner OR if it's a private chat (DM) where both are equals
    can_edit = False
    if room['created_by'] == user_id:
        can_edit = True
    elif room['room_type'] == 'private':
        # Check if member
        anon_id = get_or_create_anon_id(user_id)
        member = fetch_one("SELECT * FROM room_members WHERE room_id = %s AND anon_id = %s", (room_id, anon_id))
        if member:
            can_edit = True
            
    if not can_edit:
        raise Exception("Unauthorized: You are not the owner")
        
    if avatar_path:
        execute(
            "UPDATE chat_rooms SET room_name = %s, description = %s, room_avatar = %s WHERE room_id = %s",
            (name, description, avatar_path, room_id)
        )
    else:
        execute(
            "UPDATE chat_rooms SET room_name = %s, description = %s WHERE room_id = %s",
            (name, description, room_id)
        )

def delete_room(user_id, room_id):
    """Deletes a room if the user is the creator/admin."""
    # Verify ownership
    room = fetch_one("SELECT * FROM chat_rooms WHERE room_id = %s", (room_id,))
    if not room:
        raise Exception("Room not found")
    
    # Check if user is admin of this room
    anon_id = get_or_create_anon_id(user_id)
    member = fetch_one(
        "SELECT role FROM room_members WHERE room_id = %s AND anon_id = %s",
        (room_id, anon_id)
    )
    
    if room['created_by'] != user_id and (not member or member['role'] != 'admin'):
        raise Exception("Unauthorized: Only admins can delete this channel")
        
    # Cascade delete handles members and messages
    execute("DELETE FROM chat_rooms WHERE room_id = %s", (room_id,))
    return True

def get_or_create_dm_room(user_id1, user_id2):
    """
    Finds an existing DM room between two users or creates a new one.
    """
    if user_id1 == user_id2:
        raise Exception("You cannot DM yourself")
        
    anon_id1 = get_or_create_anon_id(user_id1)
    anon_id2 = get_or_create_anon_id(user_id2)
    
    # Try to find existing private room with exactly these two members
    # We look for a room type 'private' that both users are in.
    room = fetch_one("""
        SELECT r.room_id 
        FROM chat_rooms r
        JOIN room_members m1 ON r.room_id = m1.room_id
        JOIN room_members m2 ON r.room_id = m2.room_id
        WHERE r.room_type = 'private' 
        AND m1.anon_id = %s 
        AND m2.anon_id = %s
        AND (SELECT COUNT(*) FROM room_members rm WHERE rm.room_id = r.room_id) = 2
    """, (anon_id1, anon_id2))
    
    if room:
        return room['room_id']
        
    # Create new private room
    # We'll use a specific naming convention for DMs: "DM: UserA & UserB"
    # But for privacy, we'll just name it "null" or "Private Chat" and let UI handle display
    execute(
        "INSERT INTO chat_rooms (room_name, room_type, created_by) VALUES (%s, %s, %s)",
        ("Direct Message", "private", user_id1)
    )
    
    room = fetch_one(
        "SELECT room_id FROM chat_rooms WHERE created_by = %s AND room_type = 'private' ORDER BY created_at DESC LIMIT 1",
        (user_id1,)
    )
    room_id = room['room_id']
    
    # Add both users
    join_room_internal(room_id, anon_id1, role='member')
    join_room_internal(room_id, anon_id2, role='member')
    
    return room_id

