"""
issue_service.py
-----------------
Handles issuing and returning books.

Key characteristics:
- Uses database transactions
- Ensures data consistency (atomic operations)
- Contains business rules for issuing & returning
"""

# ===============================
# IMPORTS
# ===============================

from datetime import date
# date → used to record issue_date and return_date

from backend.config.db import get_connection
# get_connection → provides raw DB connection for transactions


# =====================================================
# MEMBER ISSUE HISTORY
# =====================================================

def get_member_issues(user_id):
    """
    Returns all issued books for a specific member.

    Used by:
    - Member dashboard (Flask)
    - CLI (Member view)

    This function is READ-ONLY.
    """

    # Local import to avoid circular dependency
    from backend.repository.db_access import fetch_all

    # SQL query to fetch issue history for a user
    query = """
    SELECT
        b.title,        -- Book title
        i.issue_date,   -- Date book was issued
        i.return_date,  -- Date book was returned (NULL if active)
        i.fine          -- Fine amount (if any)
    FROM issues i
    JOIN books b ON i.book_id = b.book_id
    WHERE i.user_id = %s
    ORDER BY i.issue_date DESC
    """

    # Execute query and return results
    return fetch_all(query, (user_id,))


# ==============================
# BUSINESS RULES (CENTRALISED)
# ==============================

# Maximum number of books a user can hold at a time
MAX_BOOKS_PER_USER = 3

# Number of days allowed without fine
MAX_DAYS_ALLOWED = 7

# Fine amount charged per extra day
FINE_PER_DAY = 5


# =====================================================
# ISSUE BOOK
# =====================================================

def issue_book(user_id: int, book_id: int):
    """
    Issues a book to a user.

    Characteristics:
    - Atomic operation (all-or-nothing)
    - Uses database transactions
    - Enforces ALL business rules in one place
    - Used by BOTH Flask and CLI
    """

    # --------------------------------------------------
    # STEP 1: CREATE DATABASE CONNECTION
    # --------------------------------------------------
    # A direct connection is used here because issuing
    # a book involves MULTIPLE dependent queries that
    # must succeed or fail together (transaction).
    conn = get_connection()

    # Dictionary cursor allows access like row["column"]
    cursor = conn.cursor(dictionary=True)

    try:
        # --------------------------------------------------
        # STEP 2: FETCH USER ROLE (CRITICAL BUSINESS RULE)
        # --------------------------------------------------
        # We must know WHO the target user is before issuing.
        # Admins manage the system and are NOT allowed
        # to borrow books.
        cursor.execute(
            """
            SELECT name, email, role
            FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        # If user_id does not exist in DB
        if not user:
            return "❌ User not found"

        # Enforce rule: admins cannot issue books
        if user["role"] == "admin":
            return "❌ Admins cannot issue books"

        # --------------------------------------------------
        # NEW: FETCH MEMBERSHIP LIMITS
        # --------------------------------------------------
        from backend.services.membership_service import get_user_membership_config
        membership = get_user_membership_config(user_id)
        max_books = membership['max_books']
        loan_days = membership['loan_days']

        # --------------------------------------------------
        # STEP 3: CHECK ACTIVE ISSUE COUNT
        # --------------------------------------------------
        # Count how many books the user is CURRENTLY holding
        # (return_date IS NULL means book not yet returned)
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM issues
            WHERE user_id = %s
              AND return_date IS NULL
            """,
            (user_id,)
        )

        # Extract numeric count from result
        active_count = cursor.fetchone()["count"]

        # Enforce maximum books per user rule
        if active_count >= max_books:
            return f"❌ User has reached issue limit for {membership['tier']} tier ({max_books} books)"

        # --------------------------------------------------
        # STEP 4: CHECK BOOK AVAILABILITY
        # --------------------------------------------------
        # A book can only be issued if at least one copy
        # is available in inventory.
        cursor.execute(
            """
            SELECT title, available_copies
            FROM books
            WHERE book_id = %s
            """,
            (book_id,)
        )

        book = cursor.fetchone()

        # Book does not exist OR no copies left
        if not book or book["available_copies"] <= 0:
            return "❌ Book not available"

        # --------------------------------------------------
        # STEP 5: PREVENT DUPLICATE ACTIVE ISSUE
        # --------------------------------------------------
        # A user should NOT be able to issue the same book
        # multiple times without returning it first.
        cursor.execute(
            """
            SELECT issue_id
            FROM issues
            WHERE user_id = %s
              AND book_id = %s
              AND return_date IS NULL
            """,
            (user_id, book_id)
        )

        # If any active issue exists → block operation
        if cursor.fetchone():
            return "❌ Book already issued to user"

        # --------------------------------------------------
        # STEP 6: ISSUE TRANSACTION (ATOMIC OPERATION)
        # --------------------------------------------------
        # From this point onward, ALL operations must succeed
        # together or be rolled back.

        # Insert new issue record
        cursor.execute(
            """
            INSERT INTO issues (user_id, book_id, issue_date)
            VALUES (%s, %s, %s)
            """,
            (user_id, book_id, date.today())
        )

        # Reduce available copies by 1
        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE book_id = %s
            """,
            (book_id,)
        )

        # NEW: Clean up any active reservation/waitlist entry for this user
        cursor.execute(
            "DELETE FROM reservations WHERE user_id = %s AND book_id = %s",
            (user_id, book_id)
        )

        # Commit transaction — changes become permanent
        conn.commit()

        # --------------------------------------------------
        # NEW: GAMIFICATION HOOK
        # --------------------------------------------------
        try:
            from backend.services.gamification_service import award_xp
            award_xp(user_id, 20, "Borrowed a book")
        except Exception as game_err:
            print(f"⚠️ Gamification error: {game_err}")

        # --------------------------------------------------
        # STEP 7: NOTIFICATIONS & HOOKS
        # --------------------------------------------------
        try:
            from backend.services.email_service import notify_issue
            from datetime import timedelta
            due_date = (date.today() + timedelta(days=loan_days)).strftime('%Y-%m-%d')
            notify_issue(user["name"], user["email"], book["title"], due_date)
            
            # In-App Notification
            from backend.services.notification_service import add_notification
            add_notification(user_id, f"📖 Book Issued: '{book['title']}'. Due: {due_date} ({membership['tier']} Tier)")
        except Exception as e:
            print(f"⚠️ Notification failed: {e}")

        # Trigger Waitlist Notification
        try:
            from backend.services.reservation_service import notify_waitlist_user
            notify_waitlist_user(book_id, book['title'])
        except Exception as e:
            print(f"⚠️ Waitlist notification failed: {e}")
            
        # Trigger Reading Goal Progress
        try:
            from backend.services.goal_service import increment_goal_progress
            increment_goal_progress(user_id)
        except Exception as e:
            print(f"⚠️ Reading goal progress update failed: {e}")
            
        # Activity Log
        try:
            from backend.services.activity_service import log_user_activity
            log_user_activity(user_id, "BORROW", f"Borrowed '{book['title']}'")
        except Exception as e:
            print(f"⚠️ Activity log failed: {e}")

        return "✅ Book issued successfully"

    except Exception as e:
        # --------------------------------------------------
        # STEP 7: ERROR HANDLING
        # --------------------------------------------------
        # If ANY error occurs at ANY step above,
        # rollback ensures database consistency.
        conn.rollback()
        return f"❌ Issue failed: {str(e)}"

    finally:
        # --------------------------------------------------
        # STEP 8: CLEANUP (ALWAYS EXECUTED)
        # --------------------------------------------------
        # Prevents connection leaks
        cursor.close()
        conn.close()


# =====================================================
# RETURN BOOK
# =====================================================

def return_book(user_id: int, book_id: int):
    """
    Returns a previously issued book.

    Responsibilities:
    - Validate active issue
    - Calculate fine if overdue
    - Update issue & book tables atomically
    """

    # Create database connection
    conn = get_connection()

    # Dictionary cursor
    cursor = conn.cursor(dictionary=True)

    try:
        # ------------------------------
        # FETCH ACTIVE ISSUE
        # ------------------------------

        # Get issue record that is not yet returned
        cursor.execute(
            """
            SELECT issue_id, issue_date
            FROM issues
            WHERE user_id = %s
              AND book_id = %s
              AND return_date IS NULL
            """,
            (user_id, book_id)
        )

        issue = cursor.fetchone()

        # If no active issue exists
        if not issue:
            return "❌ No active issue found"

        # ------------------------------
        # FINE CALCULATION (DYNAMIC)
        # ------------------------------
        from backend.services.membership_service import get_user_membership_config
        membership = get_user_membership_config(user_id)
        loan_days = membership['loan_days']

        # Get book category and its fine rate
        cursor.execute("""
            SELECT b.category, COALESCE(cf.daily_rate, %s) as rate
            FROM books b
            LEFT JOIN category_fines cf ON b.category = cf.category
            WHERE b.book_id = %s
        """, (FINE_PER_DAY, book_id))
        
        fine_data = cursor.fetchone()
        rate = fine_data['rate'] if fine_data else FINE_PER_DAY

        # Calculate how many days book was kept
        days_kept = (date.today() - issue["issue_date"]).days

        # Default fine is zero
        fine = 0

        # Apply fine if overdue
        if days_kept > loan_days:
            fine = (days_kept - loan_days) * rate

        # ------------------------------
        # RETURN TRANSACTION (ATOMIC)
        # ------------------------------

        # Update issue record with return date & fine
        cursor.execute(
            """
            UPDATE issues
            SET return_date = %s,
                fine = %s
            WHERE issue_id = %s
            """,
            (date.today(), fine, issue["issue_id"])
        )

        # Increase available copies count
        cursor.execute(
            """
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE book_id = %s
            """,
            (book_id,)
        )

        # Commit transaction
        conn.commit()

        # --------------------------------------------------
        # NEW: GAMIFICATION HOOK (XP on Return)
        # --------------------------------------------------
        try:
            from backend.services.gamification_service import award_xp
            xp_reward = 50 if fine == 0 else 10
            award_xp(user_id, xp_reward, "Returned a book")
        except Exception as game_err:
            print(f"⚠️ Gamification return XP error: {game_err}")

        # --------------------------------------------------
        # STEP 4: NOTIFY WAITLIST
        # --------------------------------------------------
        try:
            from backend.services.reservation_service import notify_waitlist_user
            # We need title for the email
            cursor.execute("SELECT title FROM books WHERE book_id = %s", (book_id,))
            b_data = cursor.fetchone()
            if b_data:
                # Notify via Email
                notify_waitlist_user(book_id, b_data['title'])
                
                # Notify via App (We need to find who the waitlist user is, but the service handles it internally)
                # Actually notify_waitlist_user takes book_id, let's see reservation_service.
                # For now just leave email for waitlist or improve later.
                pass
        except Exception as ignored:
            print(f"Waitlist notification warning: {ignored}")

        # Notify Borrower of Return
        from backend.services.notification_service import add_notification
        add_notification(user_id, f"✅ Returned: '{book_id}' (Fine: ₹{fine})")
        
        # Activity Log
        from backend.services.activity_service import log_user_activity
        log_user_activity(user_id, "RETURN", f"Returned book {book_id}")

        return f"✅ Book returned | Fine: ₹{fine}"

    except Exception as e:
        # Rollback on failure
        conn.rollback()
        return f"❌ Return failed: {str(e)}"

    finally:
        # Always close DB resources
        cursor.close()
        conn.close()


def send_overdue_reminders():
    """
    Scans for all overdue books and sends email alerts.
    """
    from backend.repository.db_access import fetch_all
    from backend.services.email_service import notify_overdue
    
    # Fetch active issues that are overdue
    overdue_records = fetch_all(
        """
        SELECT 
            u.name, 
            u.email, 
            b.title, 
            i.issue_date,
            DATEDIFF(CURDATE(), i.issue_date) - %s AS days_overdue
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL
          AND DATEDIFF(CURDATE(), i.issue_date) > %s
        """,
        (MAX_DAYS_ALLOWED, MAX_DAYS_ALLOWED)
    )
    
    count = 0
    for rec in overdue_records:
        fine = rec["days_overdue"] * FINE_PER_DAY
        if notify_overdue(rec["name"], rec["email"], rec["title"], rec["days_overdue"], fine):
            count += 1
            
            
    return f"✅ Sent {count} overdue reminders successfully"


def pay_fine(issue_id: int):
    """
    Marks a fine as paid for a specific issue record.
    """
    from backend.repository.db_access import execute_query, fetch_one
    
    # Verify fine exists and is positive
    issue = fetch_one("SELECT fine, fine_paid FROM issues WHERE issue_id = %s", (issue_id,))
    
    if not issue:
        return "❌ Record not found"
        
    if issue['fine'] <= 0:
        return "⚠️ No fine to pay for this record."
        
    if issue['fine_paid']:
        return "⚠️ Fine already paid."
        
    try:
        execute_query("UPDATE issues SET fine_paid = TRUE WHERE issue_id = %s", (issue_id,))
        return f"✅ Fine of ₹{issue['fine']} collected successfully."
    except Exception as e:
        return f"❌ Error collecting fine: {str(e)}"
