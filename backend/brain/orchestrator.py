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
       - Primary: HuggingFace API (Mistral/Phi-3)
       - Fallback: Local TinyLlama (Offline)
       - Last Resort: Rule-Based Logic
    """
    
    def __init__(self):
        self.api_token = os.getenv("HF_TOKEN")
        self.local_pipeline = None
        self.using_local = False
        
        # System Prompt
        self.system_prompt = """You are the AI Assistant for the Library Database Management System (LDBMS).
Your goal is to help users find books, understand library rules, and discover new content.
RULES:
1. Be helpful, polite, and professional.
2. Provide specific book recommendations when possible.
3. Keep responses concise (under 3 sentences where possible).
"""

        # Initialize Brain connection
        if self.api_token:
            print("🧠 AI Brain: Connected to HuggingFace API (Mistral-7B)")
            # self.client = ... (Initialized on demand or here)
            # using updated simple inference for robustness
            self.client = InferenceClient(token=self.api_token)
            self.model_id = "mistralai/Mistral-7B-Instruct-v0.2" 
        else:
            print("🧠 AI Brain: No API Token found. Switching to LOCAL MODE.")
            self._init_local_model()

    def _init_local_model(self):
        """Initializes a small local model for offline use."""
        try:
            from transformers import pipeline
            print("📥 Loading local model (TinyLlama-1.1B)... This may take a moment first time.")
            
            # TinyLlama is ~600MB and runs fast on CPU
            model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
            
            self.local_pipeline = pipeline(
                "text-generation", 
                model=model_id, 
                torch_dtype="auto", 
                device_map="auto",
                max_new_tokens=256
            )
            self.using_local = True
            print("✅ Local Brain Ready!")
        except Exception as e:
            print(f"❌ Local Brain Init Failed: {e}")
            print("⚠️ Falling back to Rule-Based responses.")
            self.using_local = False

    def process_message(self, user_message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Process a user message and return the AI's response.
        """
        if history is None:
            history = []
            
        # 1. Retrieve Context (RAG)
        print(f"🔍 Searching memory for: {user_message}")
        try:
            context_docs = rag.search_books(user_message)
        except:
            context_docs = []
        
        context_str = ""
        if context_docs:
            context_str = "\nCONTEXT BOOKS:\n" + "\n".join(
                [f"- {d['title']} by {d['author']}" for d in context_docs[:3]]
            )
            
        # 2. Generate Response
        full_user_msg = f"{context_str}\n\nUser: {user_message}"
        
        try:
            if self.api_token:
                return self._call_api(full_user_msg, history)
            elif self.using_local and self.local_pipeline:
                return self._call_local(full_user_msg, history)
            else:
                return self._rule_based_fallback(user_message)
        except Exception as e:
            print(f"❌ Brain Error: {e}")
            return self._rule_based_fallback(user_message)

    def _call_api(self, message: str, history: List[Dict[str, str]]) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        # Simplified history
        for msg in history[-3:]:
             messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        
        try:
            response = self.client.chat_completion(messages, model=self.model_id, max_tokens=512)
            return response.choices[0].message.content
        except Exception as e:
            print(f"API Error, trying local: {e}")
            if not self.local_pipeline: 
                self._init_local_model()
            if self.local_pipeline:
                 return self._call_local(message, history)
            return self._rule_based_fallback(message)

    def _call_local(self, message: str, history: List[Dict[str, str]]) -> str:
        # Construct a simple prompt for TinyLlama
        # TinyLlama Chat format: <|system|>\n{sys}<|user|>\n{query}<|assistant|>
        prompt = f"<|system|>\n{self.system_prompt}</s>\n"
        for msg in history[-2:]:
            role = msg.get("role", "user")
            prompt += f"<|{role}|>\n{msg.get('content')}</s>\n"
        prompt += f"<|user|>\n{message}</s>\n<|assistant|>\n"
        
        outputs = self.local_pipeline(prompt, max_new_tokens=256, do_sample=True, temperature=0.7)
        generated_text = outputs[0]['generated_text']
        # Extract only the assistant part
        return generated_text.split("<|assistant|>\n")[-1].strip()

    def _rule_based_fallback(self, message: str) -> str:
        """Simple keyword matching when no brain is available."""
        msg = message.lower()
        if "hello" in msg or "hi" in msg:
            return "Hello! Welcome to the library. How can I verify your books today?"
        if "book" in msg:
            return "I can help you find books. Try searching in the Catalog!"
        if "goal" in msg:
            return "You can set your reading goals in the 'My Goals' section."
        return "I'm currently operating in offline mode. Please check the Catalog for specific book inquiries."

# Singleton instance
brain = Orchestrator()
