
from backend.repository.db_access import fetch_all, fetch_one

def get_smart_recommendations(user_id, limit=6):
    """
    Suggests books based on user's borrowing history.
    1. Finds top categories borrowed by user.
    2. Suggests highest-rated/popular books in those categories not yet borrowed by user.
    """
    # Step 1: Get user's top 2 categories
    user_categories = fetch_all("""
        SELECT b.category, COUNT(*) as count
        FROM issues i
        JOIN books b ON i.book_id = b.book_id
        WHERE i.user_id = %s
        GROUP BY b.category
        ORDER BY count DESC
        LIMIT 2
    """, (user_id,))
    
    if not user_categories:
        # Fallback: Just return popular books if no history
        return fetch_all("""
            SELECT b.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM books b
            LEFT JOIN reviews r ON b.book_id = r.book_id
            GROUP BY b.book_id
            ORDER BY avg_rating DESC, available_copies DESC
            LIMIT %s
        """, (limit,))

    categories = [c['category'] for c in user_categories]
    
    # Step 2: Get recommendations from these categories
    # Excluding books already borrowed
    
    # We need to construct the placeholder string for the IN clause
    placeholders = ', '.join(['%s'] * len(categories))
    
    # Base query for category-based recs
    query = f"""
        SELECT b.book_id, b.title, b.author, b.category, b.cover_url, b.description, COALESCE(AVG(r.rating), 0) as avg_rating
        FROM books b
        LEFT JOIN reviews r ON b.book_id = r.book_id
        WHERE b.category IN ({placeholders})
        AND b.book_id NOT IN (SELECT book_id FROM issues WHERE user_id = %s)
        AND b.available_copies > 0
        GROUP BY b.book_id
        ORDER BY avg_rating DESC, RAND()
        LIMIT %s
    """
    
    # prepare params: categories... + user_id + limit
    params = categories + [user_id, limit]
    
    results = fetch_all(query, tuple(params))
    
    # Fallback if categories don't yield enough new books (or if user has read them all)
    if len(results) < limit:
        remaining = limit - len(results)
        
        # Avoid suggesting what we already found
        found_ids = [r['book_id'] for r in results]
        
        # Query for general popular/random books
        fallback_query = """
            SELECT b.book_id, b.title, b.author, b.category, b.cover_url, b.description, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM books b
            LEFT JOIN reviews r ON b.book_id = r.book_id
            WHERE b.book_id NOT IN (SELECT book_id FROM issues WHERE user_id = %s)
            AND b.available_copies > 0
        """
        
        fallback_params = [user_id]
        
        if found_ids:
            fallback_placeholders = ', '.join(['%s'] * len(found_ids))
            fallback_query += f" AND b.book_id NOT IN ({fallback_placeholders})"
            fallback_params.extend(found_ids)
            
        fallback_query += """
            GROUP BY b.book_id
            ORDER BY avg_rating DESC, RAND()
            LIMIT %s
        """
        fallback_params.append(remaining)
        
        extra = fetch_all(fallback_query, tuple(fallback_params))
        results.extend(extra)
        
    return results
