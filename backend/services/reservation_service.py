
from backend.repository.db_access import execute_query, fetch_one, fetch_all

def join_waitlist(user_id, book_id):
    """
    Adds a user to the waitlist for a book.
    """
    # Check if book is actually out of stock?
    # Ideally frontend checks, but double check here.
    book = fetch_one("SELECT available_copies FROM books WHERE book_id = %s", (book_id,))
    if not book:
        return "❌ Book not found."
    
    if book['available_copies'] > 0:
        return "⚠️ This book is available! You can request it directly."

    try:
        execute_query(
            "INSERT INTO reservations (user_id, book_id) VALUES (%s, %s)",
            (user_id, book_id)
        )
        return "✅ Added to waitlist! We'll notify you when it's available."
    except Exception as e:
        if "Duplicate entry" in str(e):
            return "⚠️ You are already on the waitlist for this book."
        return f"❌ Error joining waitlist: {str(e)}"

def get_next_in_line(book_id):
    """
    Gets the next user waiting for a book.
    """
    return fetch_one(
        "SELECT * FROM reservations WHERE book_id = %s AND status='active' ORDER BY reserved_at ASC LIMIT 1",
        (book_id,)
    )

def notify_waitlist_user(book_id, book_title):
    """
    Checks if anyone is waiting and notifies the first person.
    Called when a book is returned.
    """
    from backend.services.email_service import send_email, SMTP_USER, SMTP_PASS
    
    reservation = get_next_in_line(book_id)
    if not reservation:
        return # No one waiting
        
    user = fetch_one("SELECT name, email FROM users WHERE user_id = %s", (reservation['user_id'],))
    if not user:
        return

    # Notify via Email
    subject = f"📚 Good News! '{book_title}' is now available"
    body = f"""Hi {user['name']},

Great news! The book you were waiting for, '{book_title}', has been returned to the library.

Please log in and request it immediately to secure your copy.

Best regards,
Library Management Team
"""
    # Send email (async ideally, but here sync is fine for now)
    # Mark reservation as fulfilled? 
    # Or keep it active until they actually Request it?
    # Usually we notify them. If we mark it 'fulfilled' they might miss it.
    # Let's keep it 'active' but maybe add a 'notified_at' column effectively?
    # For simplicity, we just notify. They trigger the Request manually.
    
    # Notify via Email
    send_email(user['email'], subject, body)
    
    # NEW: Notify via In-App Notification
    try:
        from backend.services.notification_service import add_notification
        add_notification(reservation['user_id'], f"📗 Book Available: '{book_title}' is now back in stock!")
    except Exception as e:
        print(f"Waitlist In-App Notification Error: {e}")
