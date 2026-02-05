import sys
import os
import time
import socketio

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create standard python-socketio client
sio = socketio.Client()

@sio.event
def connect():
    print("✅ [Client] Connected!")
    
@sio.event
def connect_error(data):
    print(f"❌ [Client] Connection failed: {data}")

@sio.event
def disconnect():
    print("❌ [Client] Disconnected")

@sio.event
def receive_message(data):
    print(f"📩 [Client] Received message: {data}")

@sio.event
def error(data):
    print(f"❌ [Client] Error: {data}")

def run_test():
    print("🚀 Starting SocketIO Test Client...")
    
    # Needs a valid cookie/session? 
    # Our socket_service checks session.get('user_id').
    # Standard socketio client doesn't share Flask session automatically.
    # We might get rejected by 'handle_connect'.
    
    # Try connecting
    try:
        sio.connect('http://127.0.0.1:5000')
        print("⏳ Waiting for connection...")
        time.sleep(1)
        
        if sio.connected:
            # Join room
            print("Joining room 1...")
            sio.emit('join_room', {'room_id': 1})
            time.sleep(1)
            
            # Send message
            print("Sending message...")
            sio.emit('send_message', {'room_id': 1, 'message': 'TEST MSG FROM SCRIPT'})
            time.sleep(2)
            
            sio.disconnect()
        else:
            print("⚠️ Client not connected.")
            
    except Exception as e:
        print(f"🔥 Exception: {e}")

if __name__ == "__main__":
    run_test()
