
# backend/services/ai_service.py

from backend.repository.db_access import fetch_all
import re

def recommend_books_by_mood(user_text):
    """
    A local, rule-based AI that interprets user mood and recommends books.
    No API keys required. 100% Free.
    """
    user_text = user_text.lower()
    
    # 1. Define Mood Mappings (Knowledge Base)
    # Format: 'mood_keyword': ['matching_category_1', 'matching_category_2']
    mood_map = {
        'happy': ['comedy', 'adventure', 'comic', 'romance'],
        'joy': ['comedy', 'romance'],
        'fun': ['comedy', 'adventure', 'comic'],
        'laugh': ['comedy', 'comic'],
        
        'sad': ['drama', 'biography', 'history', 'poetry'],
        'depressed': ['drama', 'philosophy', 'biography'],
        'cry': ['drama', 'romance'],
        'lonely': ['biography', 'fiction'],
        
        'angry': ['thriller', 'mystery', 'action', 'politics'],
        'frustrated': ['philosophy', 'self-help', 'psychology'],
        'stress': ['fantasy', 'fiction', 'comedy'],
        
        'bored': ['fantasy', 'sci-fi', 'mystery', 'thriller'],
        'curious': ['science', 'history', 'non-fiction', 'technology'],
        'learn': ['education', 'science', 'history'],
        'smart': ['philosophy', 'science'],
        
        'inspired': ['biography', 'business', 'self-help'],
        'motivated': ['business', 'sports', 'biography'],
        
        'scared': ['horror', 'thriller'],
        'adventurous': ['adventure', 'travel', 'fantasy'],
        
        'chill': ['fiction', 'poetry', 'art'],
        'relax': ['fiction', 'romance', 'fantasy']
    }
    
    # 2. Analyze User Input (Semantic Matching)
    detected_categories = set()
    detected_moods = []
    
    # Direct keyword match
    for mood, categories in mood_map.items():
        if re.search(r'\b' + re.escape(mood) + r'\b', user_text):
            detected_moods.append(mood)
            detected_categories.update(categories)
            
    # If no moods detected, check for direct category mentions
    if not detected_categories:
        all_cats = fetch_all("SELECT DISTINCT category FROM books")
        for c in all_cats:
            cat_name = c['category'].lower()
            if cat_name in user_text:
                detected_categories.add(c['category'])
                detected_moods.append(f"interested in {cat_name}")

    # 3. Query Database
    if not detected_categories:
        # Fallback: Random "Surprise Me" selection
        return {
            "moods": ["indifferent", "open-minded"],
            "message": "I couldn't quite catch your specific mood, so here are some popular picks from our collection!",
            "books": fetch_all("SELECT * FROM books ORDER BY RAND() LIMIT 5")
        }
    
    # Format categories for SQL
    placeholders = ', '.join(['%s'] * len(detected_categories))
    query = f"""
        SELECT b.*, a.name as author_name 
        FROM books b
        LEFT JOIN authors a ON b.author_id = a.author_id
        WHERE LOWER(b.category) IN ({placeholders})
        ORDER BY RAND()
        LIMIT 6
    """
    
    books = fetch_all(query, tuple(detected_categories))
    
    return {
        "moods": detected_moods,
        "message": f"I see you're feeling {' and '.join(detected_moods[:3])}. tailored these selections just for you:",
        "books": books
    }
