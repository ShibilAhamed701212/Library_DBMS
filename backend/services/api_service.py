
import secrets
import string
from backend.repository.db_access import execute_query, fetch_all, fetch_one

def generate_key(user_id):
    # Generate a random 32-character key
    alphabet = string.ascii_letters + string.digits
    key = ''.join(secrets.choice(alphabet) for i in range(32))
    
    try:
        execute_query("INSERT INTO api_keys (user_id, api_key) VALUES (%s, %s)", (user_id, key))
        return key
    except Exception as e:
        print(f"Key generation failed: {e}")
        return None

def get_user_keys(user_id):
    return fetch_all("SELECT * FROM api_keys WHERE user_id = %s ORDER BY created_at DESC", (user_id,))

def delete_key(key_id, user_id):
    execute_query("DELETE FROM api_keys WHERE key_id = %s AND user_id = %s", (key_id, user_id))
    return "✅ Key deleted."

def validate_key(key):
    res = fetch_one("SELECT user_id FROM api_keys WHERE api_key = %s", (key,))
    return res['user_id'] if res else None
