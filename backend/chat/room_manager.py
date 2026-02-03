from backend.repository.db_access import execute, fetch_all, fetch_one
from datetime import datetime

class RoomManager:
    """
    Manages logic for chat rooms, membership, and permissions.
    """
    
    @staticmethod
    def create_room(name, description, user_id, room_type="general", is_official=False):
        """Creates a new room."""
        # 1. Create Room
        room_id = execute("""
            INSERT INTO chat_rooms (name, description, created_by, is_official, room_type)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, description, user_id, 1 if is_official else 0, room_type))
        
        # 2. Add Creator as Admin
        RoomManager.add_member(room_id, user_id, role='admin')
        
        return room_id

    @staticmethod
    def add_member(room_id, user_id, role="member"):
        """Adds a user to a room."""
        # Check if already exists
        exists = fetch_one("SELECT 1 FROM chat_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        if exists:
            return False
            
        execute("""
            INSERT INTO chat_members (room_id, user_id, role)
            VALUES (%s, %s, %s)
        """, (room_id, user_id, role))
        return True

    @staticmethod
    def remove_member(room_id, user_id):
        execute("DELETE FROM chat_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))

    @staticmethod
    def get_user_rooms(user_id):
        """Returns rooms the user is a member of."""
        return fetch_all("""
            SELECT r.*, m.role, m.joined_at
            FROM chat_rooms r
            JOIN chat_members m ON r.room_id = m.room_id
            WHERE m.user_id = %s
            ORDER BY m.joined_at DESC
        """, (user_id,))

    @staticmethod
    def get_public_rooms():
        """Returns list of public/official rooms."""
        return fetch_all("""
            SELECT * FROM chat_rooms 
            WHERE is_official = 1 OR room_type = 'public'
            ORDER BY created_at DESC
        """)

    @staticmethod
    def get_room_details(room_id):
        return fetch_one("SELECT * FROM chat_rooms WHERE room_id=%s", (room_id,))

    @staticmethod
    def is_member(room_id, user_id):
        res = fetch_one("SELECT 1 FROM chat_members WHERE room_id=%s AND user_id=%s", (room_id, user_id))
        return res is not None

room_manager = RoomManager()
