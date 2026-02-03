
import os
import requests
from backend.config.config import get_config
from backend.repository.db_access import fetch_all

def discover_by_vibe(user_vibe):
    """
    Uses AI to find books in the catalog that match a user's 'vibe' or mood.
    Supports: Gemini (paid), Hugging Face (free), or local keyword matching.
    """
    config = get_config()
    gemini_key = config.GEMINI_API_KEY
    hf_token = os.getenv('HF_TOKEN')  # Free Hugging Face API token
    
    # Fetch ALL books for semantic mapping (within reasonable limits)
    books = fetch_all("SELECT title, author, category FROM books LIMIT 200")
    book_context = "\n".join([f"- {b['title']} | {b['author']} | {b['category']}" for b in books])
    
    # Method 1: Gemini (if API key provided)
    if gemini_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are a master "Vibe Librarian". A user describes their mood or the "vibe" they want, and you find the best matches from our library catalog.
            
            USER VIBE: "{user_vibe}"
            
            LIBRARY CATALOG:
            {book_context}
            
            TASK:
            1. Analyze the user's vibe (e.g., 'dark', 'cozy', 'hopeful', 'educational').
            2. Select 3-5 books from the CATALOG that best match this vibe.
            3. For each book, write a one-sentence explanation of why it fits the vibe.
            4. Format your response in clean Markdown.
            5. If no books match well, suggest the closest ones and explain why.
            """
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            print(f"⚠️ Gemini Error: {e}")
    
    # Method 2: Hugging Face Free API (Mistral or similar)
    if hf_token:
        try:
            response = call_huggingface_ai(user_vibe, book_context, hf_token)
            if response:
                return response
        except Exception as e:
            print(f"⚠️ Hugging Face Error: {e}")
    
    # Method 3: Local keyword-based matching (no API needed)
    return local_vibe_matching(user_vibe, books)


def call_huggingface_ai(user_vibe, book_context, token):
    """Call Hugging Face's free Inference API."""
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    prompt = f"""<s>[INST] You are a librarian. A user wants books matching this vibe: "{user_vibe}"

Here are available books:
{book_context}

Select 3-5 books that best match the vibe. For each, write a one-sentence explanation. Format in Markdown. [/INST]"""
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('generated_text', '')
    
    return None


def local_vibe_matching(user_vibe, books):
    """
    Simple keyword-based matching when no AI API is available.
    Works completely offline!
    """
    vibe_lower = user_vibe.lower()
    
    # Define vibe-to-category mappings
    vibe_mappings = {
        'dark': ['Fiction', 'Mystery', 'Horror', 'Thriller'],
        'cozy': ['Fiction', 'Romance', 'Self Help'],
        'inspiring': ['Biography', 'Self Help', 'History'],
        'educational': ['Science', 'Technology', 'Reference', 'History'],
        'exciting': ['Fiction', 'Adventure', 'Thriller'],
        'relaxing': ['Fiction', 'Poetry', 'Romance'],
        'mysterious': ['Mystery', 'Fiction', 'Thriller'],
        'happy': ['Fiction', 'Romance', 'Self Help'],
        'sad': ['Fiction', 'Biography', 'Poetry'],
        'adventurous': ['Fiction', 'Adventure', 'History'],
    }
    
    # Find matching categories based on keywords in user vibe
    matched_categories = set()
    for keyword, categories in vibe_mappings.items():
        if keyword in vibe_lower:
            matched_categories.update(categories)
    
    # If no specific vibe matched, use general fiction
    if not matched_categories:
        matched_categories = {'Fiction', 'Self Help', 'Biography'}
    
    # Filter books by matched categories
    matching_books = [b for b in books if b['category'] in matched_categories]
    
    # If still no matches, return top 5 books
    if not matching_books:
        matching_books = books[:5]
    else:
        matching_books = matching_books[:5]
    
    # Format response
    if matching_books:
        response = f"### 📚 Books matching your vibe: *\"{user_vibe}\"*\n\n"
        for book in matching_books:
            response += f"- **{book['title']}** by {book['author']} ({book['category']})\n"
        response += "\n*💡 Tip: Add a Gemini or Hugging Face API key for smarter AI recommendations!*"
        return response
    else:
        return "No books found matching your vibe. Try browsing the catalog!"
