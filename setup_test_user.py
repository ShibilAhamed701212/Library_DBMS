
import sys
import os


# Add project root
sys.path.append(os.getcwd())

# Import DB tools
try:
    from backend.repository.db_access import execute_query, fetch_one
except ImportError:
    from backend.repository.db_access import execute as execute_query, fetch_one

from backend.utils.security import hash_password as generate_password_hash

def setup():
    email = 'tester@automation.com'
    pwd = 'AutoTest@123'
    name = 'Automation Tester'
    
    print(f"Checking {email}...")
    try:
        user = fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
        
        p_hash = generate_password_hash(pwd)
        
        if user:
            print("User exists. Updating password...")
            execute_query("UPDATE users SET password_hash = %s, must_change_password = 0 WHERE email = %s", (p_hash, email))
        else:
            print("Creating user...")
            execute_query(
                "INSERT INTO users (name, email, password_hash, role, must_change_password) VALUES (%s, %s, %s, 'member', 0)",
                (name, email, p_hash)
            )
        print("✅ Test user ready.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup()
