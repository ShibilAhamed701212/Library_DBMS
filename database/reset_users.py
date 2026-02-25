"""
reset_users.py
--------------
Resets the user database:
1. Deletes all non-admin users and their related data
2. Resets admin password to temp password: TempPass@123

Run:
    python database/reset_users.py
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.config.db import get_connection
from backend.utils.security import hash_password

TEMP_PASSWORD = "TempPass@123"

def reset_users():
    print("\n🔄 Starting User Database Reset...")
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Disable FK checks temporarily
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # ── Step 1: Find admin user IDs ──
        cursor.execute("SELECT user_id, name, email FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        
        if not admins:
            print("❌ No admin users found! Aborting.")
            return
        
        admin_ids = [a['user_id'] for a in admins]
        admin_placeholders = ', '.join(['%s'] * len(admin_ids))
        
        print(f"✅ Found {len(admins)} admin(s): {[a['email'] for a in admins]}")
        
        # ── Step 2: Delete non-admin related data ──
        # Delete issues for non-admin users
        cursor.execute(f"DELETE FROM issues WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
        print(f"   🗑️  Deleted {cursor.rowcount} issue records")
        
        # Delete book_requests for non-admin users
        cursor.execute(f"DELETE FROM book_requests WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
        print(f"   🗑️  Deleted {cursor.rowcount} book request records")
        
        # Delete notifications for non-admin users
        try:
            cursor.execute(f"DELETE FROM notifications WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} notification records")
        except Exception:
            pass
        
        # Delete reading goals for non-admin users
        try:
            cursor.execute(f"DELETE FROM reading_goals WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} reading goal records")
        except Exception:
            pass

        # Delete friend requests involving non-admin users
        try:
            cursor.execute(f"DELETE FROM friend_requests WHERE sender_id NOT IN ({admin_placeholders}) OR receiver_id NOT IN ({admin_placeholders})", tuple(admin_ids) + tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} friend request records")
        except Exception:
            pass
        
        # Delete chat anon IDs for non-admin users
        try:
            cursor.execute(f"DELETE FROM chat_anon_id WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} chat anon ID records")
        except Exception:
            pass

        # Delete user activities for non-admin users
        try:
            cursor.execute(f"DELETE FROM user_activities WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} user activity records")
        except Exception:
            pass

        # Delete wishlists for non-admin users
        try:
            cursor.execute(f"DELETE FROM wishlist WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} wishlist records")
        except Exception:
            pass

        # Delete reviews for non-admin users
        try:
            cursor.execute(f"DELETE FROM reviews WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} review records")
        except Exception:
            pass

        # Delete tickets for non-admin users
        try:
            cursor.execute(f"DELETE FROM ticket_replies WHERE sender_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            cursor.execute(f"DELETE FROM tickets WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted ticket records")
        except Exception:
            pass

        # Delete reservations for non-admin users
        try:
            cursor.execute(f"DELETE FROM reservations WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            print(f"   🗑️  Deleted {cursor.rowcount} reservation records")
        except Exception:
            pass

        # Delete gamification data for non-admin users
        try:
            cursor.execute(f"DELETE FROM user_badges WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
            cursor.execute(f"DELETE FROM user_xp WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
        except Exception:
            pass
        
        # ── Step 3: Delete non-admin users ──
        cursor.execute(f"DELETE FROM users WHERE user_id NOT IN ({admin_placeholders})", tuple(admin_ids))
        print(f"   🗑️  Deleted {cursor.rowcount} non-admin users")
        
        # ── Step 4: Reset ALL passwords (including admin) to temp password ──
        temp_hash = hash_password(TEMP_PASSWORD)
        cursor.execute(
            "UPDATE users SET password_hash = %s, must_change_password = FALSE",
            (temp_hash,)
        )
        print(f"   🔑 Reset {cursor.rowcount} user password(s) to: {TEMP_PASSWORD}")
        
        # Re-enable FK checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        conn.commit()
        
        # ── Verify ──
        cursor.execute("SELECT user_id, name, email, role FROM users ORDER BY user_id")
        remaining = cursor.fetchall()
        
        print(f"\n✅ Database reset complete!")
        print(f"📋 Remaining users ({len(remaining)}):")
        for u in remaining:
            print(f"   ID:{u['user_id']} | {u['name']} | {u['email']} | {u['role']}")
        print(f"\n🔑 Temp password for all: {TEMP_PASSWORD}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Reset failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    reset_users()
