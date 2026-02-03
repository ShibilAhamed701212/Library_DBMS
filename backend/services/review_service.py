
from backend.repository.db_access import execute_query, fetch_all, fetch_one

def add_review(user_id, book_id, rating, comment):
    """
    Adds a review for a book.
    Ensures user handles constraints (one review per book per user).
    """
    try:
        # Check if review already exists
        existing = fetch_one(
            "SELECT review_id FROM reviews WHERE user_id = %s AND book_id = %s",
            (user_id, book_id)
        )
        if existing:
            return "❌ You have already reviewed this book."

        execute_query(
            "INSERT INTO reviews (user_id, book_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (user_id, book_id, rating, comment)
        )
        return "✅ Review submitted successfully."
    except Exception as e:
        return f"❌ Error submitting review: {str(e)}"

def get_book_reviews(book_id):
    """
    Fetches all reviews for a book details page.
    """
    query = """
    SELECT r.rating, r.comment, r.created_at, u.name as user_name
    FROM reviews r
    JOIN users u ON r.user_id = u.user_id
    WHERE r.book_id = %s
    ORDER BY r.created_at DESC
    """
    return fetch_all(query, (book_id,))

def get_average_rating(book_id):
    """
    Calculates average rating for a book.
    """
    res = fetch_one("SELECT AVG(rating) as avg_rating, COUNT(*) as count FROM reviews WHERE book_id = %s", (book_id,))
    if res and res['avg_rating']:
        return round(res['avg_rating'], 1), res['count']
    return 0, 0
