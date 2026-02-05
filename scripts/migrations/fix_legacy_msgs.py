
import os
import sys
sys.path.append(os.getcwd())
try:
    from backend.repository.db_access import execute
except ImportError:
    from backend.repository.db_access import execute

def fix_legacy():
    print("🚀 Updating legacy messages to sender_type='user'...")
    # Update ALL messages to 'user' so we don't accidentally hide past history
    # New messages will use the correct type via the new save_message logic
    try:
        execute("UPDATE chat_messages SET sender_type = 'user' WHERE sender_type = 'anon'")
        print("✅ Updated legacy messages.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_legacy()
