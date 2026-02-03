import time
from backend.utils.snowflake import generate_id

# In-Memory Session Store (Simulating Redis)
# Map: socket_id -> { user_id, last_heartbeat, connected_at }
_sessions = {}
# Map: user_id -> set(socket_ids)
_user_sockets = {}

class GatewayService:
    """
    Manages WebSocket Connection Lifecycle.
    """
    
    @staticmethod
    def register_connection(socket_id, user_id):
        """Registers a new socket connection."""
        print(f"🔌 Gateway: Registering {user_id} on {socket_id}")
        
        # Zombie Cleanup (Max 1 session for MVP)
        existing = _user_sockets.get(user_id)
        if existing:
            # logic to force disconnect old socket could go here
            pass
            
        _sessions[socket_id] = {
            'user_id': user_id,
            'connected_at': time.time(),
            'last_heartbeat': time.time(),
            'session_id': generate_id()
        }
        
        if user_id not in _user_sockets:
            _user_sockets[user_id] = set()
        _user_sockets[user_id].add(socket_id)
        
        return _sessions[socket_id]['session_id']

    @staticmethod
    def deregister_connection(socket_id):
        """Removes a socket connection."""
        session = _sessions.pop(socket_id, None)
        if session:
            uid = session['user_id']
            if uid in _user_sockets:
                _user_sockets[uid].discard(socket_id)
                if not _user_sockets[uid]:
                    del _user_sockets[uid]
            print(f"🔌 Gateway: Deregistered {uid}")

    @staticmethod
    def update_heartbeat(socket_id):
        """Updates the heartbeat timestamp."""
        if socket_id in _sessions:
            _sessions[socket_id]['last_heartbeat'] = time.time()
            return True
        return False

    @staticmethod
    def get_online_users():
        """Returns list of online user IDs."""
        return list(_user_sockets.keys())
