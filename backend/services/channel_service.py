from backend.repository.db_access import execute, fetch_one, fetch_all, get_connection
from backend.services.chat_service import get_or_create_anon_id

def create_channel(guild_id, category_id, name, type='text', topic=None):
    """Creates a new channel in a guild."""
    return execute("""
        INSERT INTO channels (guild_id, category_id, name, type, topic)
        VALUES (%s, %s, %s, %s, %s)
    """, (guild_id, category_id, name, type, topic))

# ... (get_channel_messages is fine) ...

# ... (save_message is fine) ...

def get_my_dms(user_id):
    """Fetches private DM channels for a user."""
    # Assuming dm_participants table is used.
    # If not populated, this returns empty, which is fine for now.
    return fetch_all("""
        SELECT c.*
        FROM channels c
        JOIN dm_participants dp ON c.channel_id = dp.channel_id
        WHERE dp.user_id = %s AND c.guild_id IS NULL
        ORDER BY c.created_at DESC
    """, (user_id,))

def create_dm(user_id, target_user_id):
    """Creates or Retrieves a DM channel."""
    # Check if exists
    # (Complex SQL to find intersection of channel_ids for both users)
    existing = fetch_one("""
        SELECT c.channel_id 
        FROM channels c
        JOIN dm_participants dp1 ON c.channel_id = dp1.channel_id
        JOIN dm_participants dp2 ON c.channel_id = dp2.channel_id
        WHERE c.guild_id IS NULL 
        AND dp1.user_id = %s 
        AND dp2.user_id = %s
    """, (user_id, target_user_id))
    
    if existing: return existing['channel_id']
    
    # Create
    cid = execute("INSERT INTO channels (name, type, is_private) VALUES ('DM', 'text', TRUE)")
    
    # Add Participants
    execute("INSERT INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (cid, user_id))
    execute("INSERT INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (cid, target_user_id))
    
    return cid
    """Fetches messages for a channel with user profile data."""
    messages = fetch_all("""
        SELECT 
            m.message_id, m.message_text as content, m.file_url, m.sent_at as created_at, m.sender_type,
            u.user_id as sender_id, u.name as sender_name, u.profile_pic as sender_pic,
            ca.anon_id
        FROM chat_messages m
        LEFT JOIN chat_anon_id ca ON m.anon_id = ca.anon_id
        LEFT JOIN users u ON ca.user_id = u.user_id
        WHERE m.channel_id = %s AND m.is_deleted = FALSE
        ORDER BY m.sent_at DESC LIMIT %s
    """, (channel_id, limit))
    
    # Format dates and handle anonymity for JSON
    for msg in messages:
        if msg['created_at']:
            msg['created_at'] = msg['created_at'].strftime("%Y-%m-%d %H:%M:%S")
        
        # Structure Attachment
        if msg['file_url']:
            import os
            ext = os.path.splitext(msg['file_url'])[1].lower()
            msg['attachment'] = {
                'url': msg['file_url'],
                'type': 'image' if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp'] else 'file',
                'name': os.path.basename(msg['file_url'])
            }
        else:
            msg['attachment'] = None
            
        # Anonymity Check
        if msg['sender_type'] == 'anon':
            msg['sender_name'] = 'Anonymous Member'
            msg['sender_pic'] = 'default.jpg'
            msg['sender_id'] = None # Hide real ID
            
    return messages

def save_message(user_id, channel_id, text=None, file_url=None, reply_to_id=None, sender_type='user'):
    """Saves a message to the channel."""
    anon_id = get_or_create_anon_id(user_id)
    
    # Ensure sender_type is valid
    if sender_type not in ['anon', 'user']:
        sender_type = 'user'
        
    # Ensure text is not None if DB requires it
    if text is None:
        text = ""

    msg_id = execute("""
        INSERT INTO chat_messages (channel_id, anon_id, message_text, file_url, reply_to_id, sender_type)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (channel_id, anon_id, text, file_url, reply_to_id, sender_type))
    
    # Return full message object for socket broadcast
    return {
        'message_id': msg_id,
        'channel_id': channel_id,
        'content': text,
        'file_url': file_url,
        'sender_id': user_id,
        'anon_id': anon_id,
        'sender_type': sender_type
    }

def get_my_dms(user_id):
    """Fetches private DM channels for a user."""
    # Assuming dm_participants table is used.
    # If not populated, this returns empty, which is fine for now.
    return fetch_all("""
        SELECT c.*
        FROM channels c
        JOIN dm_participants dp ON c.channel_id = dp.channel_id
        WHERE dp.user_id = %s AND c.guild_id IS NULL
        ORDER BY c.created_at DESC
    """, (user_id,))

def create_dm(user_id, target_user_id):
    """Creates or Retrieves a DM channel."""
    # Check if exists
    # (Complex SQL to find intersection of channel_ids for both users)
    existing = fetch_one("""
        SELECT c.channel_id 
        FROM channels c
        JOIN dm_participants dp1 ON c.channel_id = dp1.channel_id
        JOIN dm_participants dp2 ON c.channel_id = dp2.channel_id
        WHERE c.guild_id IS NULL 
          AND dp1.user_id = %s 
          AND dp2.user_id = %s
    """, (user_id, target_user_id))
    
    if existing: return existing['channel_id']
    
    # Create
    execute("INSERT INTO channels (name, type, is_private) VALUES ('DM', 'text', TRUE)")
    cid = fetch_one("SELECT LAST_INSERT_ID() as id")['id']
    
    # Add Participants
    execute("INSERT INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (cid, user_id))
    execute("INSERT INTO dm_participants (channel_id, user_id) VALUES (%s, %s)", (cid, target_user_id))
    
    return cid
