from backend.repository.db_access import execute, fetch_all
from datetime import datetime

class MessageEngine:
    """
    Handles message persistence and retrieval.
    """
    
    @staticmethod
    def save_message(room_id, user_id, content, msg_type="text"):
        """Saves a message to the DB."""
        execute("""
            INSERT INTO chat_messages (room_id, user_id, content, msg_type)
            VALUES (%s, %s, %s, %s)
        """, (room_id, user_id, content, msg_type))
        return True

    @staticmethod
    def get_recent_messages(room_id, limit=50):
        """Fetches recent history for a room."""
        results = fetch_all("""
            SELECT 
                m.message_id, 
                m.content, 
                m.msg_type,
                m.created_at,
                u.user_id, 
                u.name as user_name, 
                u.profile_pic
            FROM chat_messages m
            JOIN users u ON m.user_id = u.user_id
            WHERE m.room_id = %s
            ORDER BY m.created_at DESC
            LIMIT %s
        """, (room_id, limit))
        
        # Convert date to ISO string for JSON serialization
        for msg in results:
            if msg.get('created_at'):
                msg['created_at'] = str(msg['created_at']).replace(" ", "T")
                
        return results

message_engine = MessageEngine()
