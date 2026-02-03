"""
request_service.py
-------------------
Handles book request operations:
- create request
- view pending requests
- process request (approve/reject)
"""

from datetime import date
from backend.repository.db_access import execute, fetch_all, fetch_one
from backend.services.issue_service import issue_book

def create_request(user_id: int, book_id: int):
    """
    Creates a new book request for a user.
    """
    if not book_id:
        return "❌ Request Failed: No book selected"

    import mysql.connector

    try:
        # Check if user already has a pending or approved request for this book
        # (Optional business rule: prevent spamming requests)
        existing = fetch_one(
            """
            SELECT request_id FROM book_requests 
            WHERE user_id = %s AND book_id = %s AND status = 'Pending'
            """,
            (user_id, book_id)
        )
        if existing:
            return "⚠️ You already have a pending request for this book"

        # Insert request
        execute(
            """
            INSERT INTO book_requests (user_id, book_id, request_date, status)
            VALUES (%s, %s, %s, 'Pending')
            """,
            (user_id, book_id, date.today())
        )
        return "✅ Request sent to admin"
    
    except mysql.connector.Error as err:
        if err.errno == 1146: # Table doesn't exist
            return "❌ Error: 'book_requests' table missing. Contact Admin to run DB setup."
        raise err

def get_pending_requests():
    """
    Fetches all pending requests with user and book details.
    """
    import mysql.connector
    try:
        return fetch_all(
            """
            SELECT 
                r.request_id,
                r.request_date,
                u.name AS user_name,
                b.title AS book_title
            FROM book_requests r
            JOIN users u ON r.user_id = u.user_id
            JOIN books b ON r.book_id = b.book_id
            WHERE r.status = 'Pending'
            ORDER BY r.request_date ASC
            """
        )
    except mysql.connector.Error as err:
        # Gracefully handle missing table error so dashboard doesn't crash
        if err.errno == 1146: # Table doesn't exist
            print("⚠️ Table 'book_requests' missing. Please run database/DBMS_library_db.sql")
            return None # Indicate error to caller
        raise err

def process_request(request_id: int, action: str):
    """
    Approves or Rejects a request.
    If Approved -> Issues the book.
    """
    # Verify request exists
    req = fetch_one(
        """
        SELECT r.user_id, r.book_id, r.status, u.name, u.email, b.title 
        FROM book_requests r
        JOIN users u ON r.user_id = u.user_id
        JOIN books b ON r.book_id = b.book_id
        WHERE r.request_id = %s
        """,
        (request_id,)
    )
    if not req:
        return "❌ Request not found"
    
    if req["status"] != "Pending":
        return f"⚠️ Request is already {req['status']}"

    if action == "approve":
        # Try to issue the book
        result = issue_book(req["user_id"], req["book_id"])
        
        # If issue successful, update request status
        if "✅" in result:
            execute(
                "UPDATE book_requests SET status = 'Approved' WHERE request_id = %s",
                (request_id,)
            )
            return "✅ Request Approved & Book Issued"
        else:
            return f"❌ Approval Failed: {result}"
            
    elif action == "reject":
        execute(
            "UPDATE book_requests SET status = 'Rejected' WHERE request_id = %s",
            (request_id,)
        )
        try:
            from backend.services.email_service import notify_request_status
            notify_request_status(req["name"], req["email"], req["title"], "Rejected")
        except:
            pass
        return "✅ Request Rejected"

    return "❌ Invalid Action"
