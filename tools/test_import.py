import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from backend.services import chat_service
    print("Import successful!")
    print(dir(chat_service))
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
