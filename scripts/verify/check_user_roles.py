import sys
sys.path.append('.')
from backend.repository.db_access import fetch_all

print("🔍 Checking Users and Roles...")
users = fetch_all("SELECT user_id, name, role FROM users")
for u in users:
    print(f"User {u['user_id']}: {u['name']} - Role: '{u['role']}'")
