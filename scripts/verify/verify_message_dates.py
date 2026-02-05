import sys
import os
sys.path.append(os.getcwd())

from backend.chat.message_engine import message_engine
from datetime import datetime

print("Testing get_recent_messages serialization...")

# Fetch messages for room 1 (General Lounge, assumed to exist/have msgs)
# Or create a dummy one if needed, but existing DB has data.
try:
    msgs = message_engine.get_recent_messages(1, limit=5)
    
    if not msgs:
        print("⚠️ No messages found in room 1. Cannot verify.")
    else:
        fail = False
        for m in msgs:
            created_at = m['created_at']
            if isinstance(created_at, datetime):
                 print(f"❌ FAIL: Message {m['message_id']} has datetime object: {created_at}")
                 fail = True
            elif isinstance(created_at, str):
                 print(f"✅ PASS: Message {m['message_id']} has string: {created_at}")
            else:
                 print(f"❓ UNKNOWN: Message {m['message_id']} has type {type(created_at)}")
        
        if not fail:
            print("\n🎉 ALL CHECKS PASSED: Dates are JSON serializable.")
        else:
            print("\n❌ CHECKS FAILED.")

except Exception as e:
    print(f"❌ EXECUTION A ERROR: {e}")
