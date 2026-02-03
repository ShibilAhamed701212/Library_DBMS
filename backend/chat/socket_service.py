from backend import socketio
from flask_socketio import emit, join_room, leave_room
from flask import request, session
from backend.services.channel_service import save_message, get_channel_messages
from backend.services.chat_service import get_or_create_anon_id, delete_message, edit_message # We might need to move these
# Actually, delete/edit should be in channel_service now or compatible. 
# For now, let's assume strict separation. I need to move edit/delete to ChannelService ideally.
# But for speed, I will use direct DB Access here if simple, or import from chat_service if compatible.
# Wait, chat_service operations work on 'chat_messages' table. 
# Since we only renamed the column, the SQL in chat_service might break if it uses 'room_id'.
# I need to update chat_service functions or implement them in channel_service.
# I WILL IMPLEMENT THEM IN channel_service NOW TO BE SAFE.

from backend.repository.db_access import execute, fetch_one
from backend.services.gateway_service import GatewayService
from backend.services.ingestion_service import IngestionService

# --- Helper functions for Edit/Delete in new architecture ---
def service_edit_message(user_id, message_id, new_content):
    anon_id = get_or_create_anon_id(user_id)
    # Check ownership
    msg = fetch_one("SELECT * FROM chat_messages WHERE message_id = %s", (message_id,))
    if not msg: return False
    if msg['anon_id'] != anon_id: return False
    
    execute("UPDATE chat_messages SET message_text = %s, is_edited = TRUE WHERE message_id = %s", (new_content, message_id))
    return True

def service_delete_message(user_id, message_id):
    anon_id = get_or_create_anon_id(user_id)
    msg = fetch_one("SELECT * FROM chat_messages WHERE message_id = %s", (message_id,))
    if not msg: return False
    
    # Allow self or admin (TODO: Check guild permissions for admin)
    if msg['anon_id'] != anon_id: return False 
    
    execute("UPDATE chat_messages SET is_deleted = TRUE WHERE message_id = %s", (message_id,))
    return True
# -----------------------------------------------------------

print("✅ Loaded backend.chat.socket_service event handlers (Discord Arch)", flush=True)

@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if user_id:
        print(f"🔌 User {session.get('name')} (ID: {user_id}) connected.", flush=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 User disconnected: {request.sid}")

@socketio.on('join_channel')
def handle_join_channel(data):
    """User joining a channel (initially called join_room)."""
    # Helper to support both 'room_id' (legacy frontend) and 'channel_id'
    channel_id = data.get('channel_id') or data.get('room_id')
    user_id = session.get('user_id')
    
    if channel_id is None: return

    print(f"🚪 Socket Join Channel: {channel_id}, User {user_id}", flush=True)

    # Verify Channel Exists
    channel = fetch_one("SELECT * FROM channels WHERE channel_id = %s", (channel_id,))
    if not channel:
        emit('error', {'message': 'Channel not found'})
        return

    # Join Socket Room (using channel_id as the room name)
    join_room(str(channel_id))
    
    # Fetch History
    try:
        raw_msgs = get_channel_messages(channel_id)
        # Format for Frontend (Frontend expects specific keys)
        formatted = []
        my_anon_id = get_or_create_anon_id(user_id)
        
        for m in raw_msgs:
            formatted.append({
                'message_id': m['message_id'],
                'content': m['content'],
                'created_at': m['created_at'], # Already formatted in service
                'sender_id': m['sender_id'],
                'sender_type': 'me' if m['anon_id'] == my_anon_id else 'other',
                'file_url': m['file_url'],
                'user_profile': {
                    'name': m['sender_name'] or 'Unknown',
                    'pic': m['sender_pic']
                },
                'sender_name': m['sender_name']
            })
        
        # Send history (Oldest first for scrolling)
        emit('message_history', {'messages': formatted[::-1]})
        
    except Exception as e:
        import traceback
        print(f"❌ Error fetching history: {e}")
        traceback.print_exc()
        emit('error', {'message': "Failed to load history"})


@socketio.on('send_message')
def handle_message(data):
    user_id = session.get('user_id')
    channel_id = data.get('channel_id') or data.get('room_id')
    content = data.get('message') or data.get('content')
    
    if not channel_id: return

    # Anonymous Check
    # Prioritize payload flag (more reliable for real-time toggling)
    # But check session as fallback
    is_anon = data.get('is_anon')
    if is_anon is None:
        is_anon = session.get('is_anon', False)
    
    if is_anon:
        user_profile = {
            'name': 'Anonymous Member',
            'pic': 'default.jpg'
        }
    else:
        user_profile = {
            'name': session.get('name'),
            'pic': session.get('profile_pic', 'default.jpg')
        }
    
    attachment = data.get('attachment')
    reply_to_id = data.get('reply_to_id')

    success, result = IngestionService.process_message(
        user_id, channel_id, content, socketio, user_profile, attachment, reply_to_id
    )
    
    if success:
        # Confirm to sender (Optimistic Ack)
        result['sender_type'] = 'me'
        emit('receive_message', result)
    else:
        # Error (Rate Limit / Validation)
        emit('error', {'message': result})

@socketio.on('edit_message')
def handle_edit(data):
    if service_edit_message(session['user_id'], data['message_id'], data['new_content']):
        channel_id = data.get('channel_id') or data.get('room_id')
        emit('message_updated', {
            'message_id': data['message_id'],
            'new_content': data['new_content']
        }, to=str(channel_id))

@socketio.on('delete_message')
def handle_delete(data):
    if service_delete_message(session['user_id'], data['message_id']):
        channel_id = data.get('channel_id') or data.get('room_id')
        emit('message_deleted', {'message_id': data['message_id']}, to=str(channel_id))

@socketio.on('typing')
def handle_typing(data):
    # Architecture: Throttling could be added here via RateLimiter
    channel_id = data.get('channel_id') or data.get('room_id')
    emit('typing', {'user': session.get('name')}, to=str(channel_id), include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    channel_id = data.get('channel_id') or data.get('room_id')
    emit('stop_typing', {}, to=str(channel_id), include_self=False)
