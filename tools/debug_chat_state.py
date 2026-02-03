import sys
import os
sys.path.append(os.getcwd())

from backend.repository.db_access import fetch_all
from backend.app import create_app

app = create_app()

with app.app_context():
    print("--- CHAT ROOMS ---")
    rooms = fetch_all("SELECT * FROM chat_rooms ORDER BY created_at DESC LIMIT 5")
    for r in rooms:
        print(f"[{r['room_id']}] {r['name']} (Created by: {r['created_by']})")

    print("\n--- CHAT MEMBERS ---")
    members = fetch_all("SELECT * FROM chat_members ORDER BY joined_at DESC LIMIT 10")
    for m in members:
        print(f"Room {m['room_id']} - User {m['user_id']} ({m['role']})")

    print("\n--- CHAT MESSAGES ---")
    msgs = fetch_all("SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 5")
    for m in msgs:
        print(f"[{m['room_id']}] User {m['user_id']}: {m['content']}")
