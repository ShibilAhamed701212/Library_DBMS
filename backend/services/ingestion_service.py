from backend.utils.snowflake import generate_id
from backend.utils.rate_limiter import check_rate_limit
from backend.services.channel_service import save_message
from backend.services.gateway_service import GatewayService
from flask_socketio import emit

class IngestionService:
    """
    Central Pipeline for Message Processing.
    Steps: RateLimit -> Validate -> Persist -> Fan-out
    """
    
    @staticmethod
    def process_message(user_id, channel_id, content, socket_io_instance, user_profile, attachment=None, reply_to_id=None):
        """
        Ingests a message payload.
        Returns: Success (Bool), Error (String or None)
        """
        
        # 1. Rate Limiting
        # Key = rate:channel:{cid}:user:{uid}
        rate_key = f"rate:channel:{channel_id}:user:{user_id}"
        if not check_rate_limit(rate_key):
             return False, "You are being rate limited."
             
        # 2. Validation (Length, Content)
        # Content can be empty if attachment exists
        if not content and not attachment:
             return False, "Message cannot be empty."
        if content and len(content) > 4000:
             return False, "Message too long."
             
        # 3. Persistence (DB)
        # Determine sender_type based on profile (set by socket_service)
        sender_type = 'anon' if user_profile.get('name') == 'Anonymous Member' else 'user'
        
        file_url = attachment.get('url') if attachment else None
        
        try:
            # save_message returns dict with message_id, etc.
            msg_obj = save_message(user_id, channel_id, text=content, file_url=file_url, reply_to_id=reply_to_id, sender_type=sender_type)
        except Exception as e:
            print(f"❌ DB Insert Failed: {e}")
            return False, "Database Error"

        # 4. Fan-Out (Broadcast)
        # We should ideally fetch the reply_to content for the UI
        reply_to_content = None
        if reply_to_id:
             # Optimization: Pass it in or fetch it lightly.
             # For now we'll just send the ID and let frontend handle or fetch if needed
             # Or backend can fetch strictly the content snippet.
             # Skipping strict fetch for speed, frontend will just show "Replied to message"
             pass

        payload = {
            'message_id': msg_obj['message_id'],
            'content': content,
            'channel_id': channel_id,
            'sender_id': user_id,
            'sender_type': 'other',
            'user_profile': user_profile,
            'nonce': generate_id(),
            'created_at': 'Just now',
            'attachment': attachment,
            'reply_to_id': reply_to_id,
            # 'reply_to': { 'content': ... } # If we fetched it
        }
        
        from backend import socketio
        socketio.emit('receive_message', payload, to=str(channel_id), include_self=False)
        
        # Ack to sender with same payload
        payload['sender_type'] = 'me'
        return True, payload
