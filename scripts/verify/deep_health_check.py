
import sys
import os
from dotenv import load_dotenv

# Add root to python path because this script is in scripts/verify/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))


def check_structure():
    print("running structure check...")
    required = [
        'backend/__init__.py',
        'backend/routes/admin_routes.py',
        'backend/routes/member_routes.py',
        'static/css/style.css',
        'static/js/js_channel_settings.js',
        'templates/layout.html',
        'templates/member/community.html',
        'templates/member/overview.html',
        'run.py'
    ]
    missing = []
    for f in required:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        print(f"❌ Missing critical files: {missing}")
        return False
    print("✅ File structure integrity check passed.")
    return True

def check_imports():
    print("running import check...")
    try:
        from backend import create_app
        from backend.repository.db_access import get_db_connection
        print("✅ Backend module imports successful.")
        return True
    except Exception as e:
        print(f"❌ Backend Import Error: {e}")
        return False

def check_db():
    print("checking db connection...")
    try:
        from backend.repository.db_access import get_db_connection
        conn = get_db_connection()
        if conn and conn.is_connected():
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            print("✅ Database connection established.")
            return True
        else:
            print("❌ Database connection failed (None or not connected).")
            return False
    except Exception as e:
        print(f"❌ Database Exception: {e}")
        return False

if __name__ == "__main__":
    print("=== DEEP SYSTEM HEALTH CHECK ===")
    s = check_structure()
    i = check_imports()
    d = check_db()
    
    if s and i and d:
        print("\n🚀 SYSTEM STATUS: GREEN (ALL SYSTEMS GO)")
        sys.exit(0)
    else:
        print("\n⚠️ SYSTEM STATUS: RED (ISSUES DETECTED)")
        sys.exit(1)
