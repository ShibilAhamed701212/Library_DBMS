import os
from typing import List, Dict, Any, Optional
from huggingface_hub import InferenceClient
from datetime import datetime

# Initialize environment variables if not already done
# In Flask context, this is usually handled by the app setup, 
# but for standalone testing we might need dotenv.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backend.brain.rag import rag

class Orchestrator:
    """
    The Orchestrator is the central brain of the AI agent.
    It manages:
    1. Conversation State (Memory)
    2. Prompt Construction (System Instructions)
    3. LLM Interaction (Inference)
    4. Tool Execution (future phase)
    """
    
    def __init__(self, model_id: str = "HuggingFaceH4/zephyr-7b-beta"):
        """
        Initialize the Orchestrator with a specific LLM model.
        Args:
            model_id: The HuggingFace model ID to use.
                     Examples: 
                     - "mistralai/Mistral-7B-Instruct-v0.2" (Good balance)
                     - "meta-llama/Llama-2-7b-chat-hf" (requires approval)
                     - "HuggingFaceH4/zephyr-7b-beta" (Excellent chat)
        """
        self.api_token = os.getenv("HF_TOKEN")
        if not self.api_token:
            print("⚠️ WARNING: HF_TOKEN not found in environment variables. AI features may fail.")
            
        self.model_id = model_id
        # Client for sync calls (can facilitate streaming too)
        self.client = InferenceClient(model=model_id, token=self.api_token)
        
        # System Prompt - The core personality and rules
        self.system_prompt = """You are the AI Assistant for the Library Database Management System (LDBMS).
Your goal is to help users find books, understand library rules, and discover new content based on their mood.

RULES:
1. Be helpful, polite, and professional.
2. If you recommend books, try to be specific based on the user's request.
3. If you don't know something, admit it—don't hallucinate facts about the library inventory (unless exploring general book knowledge).
4. Keep responses concise and readable. Use Markdown for formatting.
"""

    def process_message(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Process a user message and return the AI's response.
        """
        if history is None:
            history = []
            
        # 1. Retrieve Context (RAG)
        print(f"🔍 Searching memory for: {user_message}")
        context_docs = rag.search_books(user_message)
        
        context_str = ""
        if context_docs:
            context_str = "\nRELEVANT LIBRARY BOOKS:\n" + "\n".join(
                [f"- {d['title']} by {d['author']} ({d['category']}): {d.get('description', '')[:200]}..." for d in context_docs]
            )
            
        # 2. Build Prompt with Context
        messages = []
        # Add system prompt + Context
        full_system_prompt = self.system_prompt + "\n" + context_str
        messages.append({"role": "system", "content": full_system_prompt})
        
        # Add history
        
        # Add history
        for msg in history[-5:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})
            
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Generate response using Chat Completion API
            response = self.client.chat_completion(
                messages,
                max_tokens=512,
                temperature=0.7,
                top_p=0.95,
                stream=False
            )
            # Response format: response.choices[0].message.content
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            # Fallback for older library versions or different response structures
            try:
                # If chat_completion fails (e.g. old library), try conversational or raw text
                # But for now, let's just error out gracefully
                return f"I apologize, I'm having trouble thinking right now. (Error: {str(e)})"
            except:
                return "I apologize, but I'm having trouble connecting to my brain right now."

    def _build_prompt(self, user_message: str, history: List[Dict[str, str]]) -> str:
        # Legacy helper, might not be needed if using chat_completion
        pass

# Singleton instance for easy import
brain = Orchestrator()
