import os
import sys
import time

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

from backend.utils.rate_limiter import check_rate_limit

def test_ratelimit():
    print("🚦 Testing Rate Limiter (5 req / 2 sec)...")
    key = "user:test:123"
    
    # Burst 5
    for i in range(5):
        allowed = check_rate_limit(key)
        print(f"Req {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")
        if not allowed:
            print("❌ Error: Should have been allowed!")
            return

    # 6th should fail
    allowed = check_rate_limit(key)
    print(f"Req 6: {'✅ Allowed' if allowed else '🛡️ Blocked correctly'}")
    if allowed:
        print("❌ Error: Should have been blocked!")
        return
        
    print("⏳ Waiting 2 seconds for refill...")
    time.sleep(2.1)
    
    # Should work again
    allowed = check_rate_limit(key)
    print(f"Req 7 (After Wait): {'✅ Allowed' if allowed else '❌ Blocked'}")
    if not allowed:
        print("❌ Error: Should have refilled!")
        return

    print("🎉 Rate Limiter works!")

if __name__ == "__main__":
    test_ratelimit()
