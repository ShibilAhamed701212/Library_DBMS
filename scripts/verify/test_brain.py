import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.brain.orchestrator import brain

def test_brain():
    print("🧠 Testing Orchestrator...")
    print(f"Model ID: {brain.model_id}")
    
    if not brain.api_token:
        print("❌ HF_TOKEN not found!")
        return

    user_input = "Hello! Recommend me a book about space adventure."
    print(f"\nUser: {user_input}")
    
    print("thinking...")
    # The orchestrator now prints "🔍 Searching memory..." automatically
    response = brain.process_message(user_input)
    
    print(f"\nAssistant: {response}")

if __name__ == "__main__":
    test_brain()
