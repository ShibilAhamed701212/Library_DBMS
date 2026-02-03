
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
    # Using format specifiers for multiple categories
    format_strings = ','.join(['%s'] * len(categories))
    query = f"""
        SELECT b.*, COALESCE(AVG(r.rating), 0) as avg_rating
        FROM books b
        LEFT JOIN reviews r ON b.book_id = r.book_id
        WHERE b.category IN ({format_strings})
        AND b.book_id NOT IN (SELECT book_id FROM issues WHERE user_id = %s)
        GROUP BY b.book_id
        ORDER BY avg_rating DESC, RAND()
        LIMIT %s
    """
    params = categories + [user_id, limit]
    
    results = fetch_all(query, params)
    
    # Fallback if categories don't yield enough new books
    if len(results) < limit:
        remaining = limit - len(results)
        extra = fetch_all("""
            SELECT b.*, COALESCE(AVG(r.rating), 0) as avg_rating
            FROM books b
            LEFT JOIN reviews r ON b.book_id = r.book_id
            WHERE b.book_id NOT IN (SELECT book_id FROM issues WHERE user_id = %s)
            AND b.book_id NOT IN (%s)
            GROUP BY b.book_id
            ORDER BY RAND()
            LIMIT %s
        """, (user_id, ','.join([str(r['book_id']) for r in results]) if results else 0, remaining))
        results.extend(extra)
        
    return results
