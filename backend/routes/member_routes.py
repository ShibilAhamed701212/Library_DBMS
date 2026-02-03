# ===============================
# IMPORTS
# ===============================

from flask import Blueprint, session, render_template, request, redirect, url_for, flash, jsonify, current_app
from functools import wraps
import json
import os
from datetime import datetime, timedelta

# Import database access functions
from backend.repository.db_access import (
    execute_query,
    fetch_all,
    fetch_one
)

# Import authentication decorator
from backend.middleware.auth import member_required

# Blueprint for member routes
member_bp = Blueprint('member', __name__, url_prefix='/member')

def ensure_isbn_column_exists():
    """
    Ensure the book_suggestions table has an isbn column.
    If the column doesn't exist, it will be added.
    """
    try:
        # Check if the column exists
        result = fetch_one(
            """
            SELECT COUNT(*) AS count
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'book_suggestions' 
            AND COLUMN_NAME = 'isbn'
            """
        )
        
        if not result or result.get('count', 0) == 0:
            # Add the isbn column if it doesn't exist
            current_app.logger.info("Adding 'isbn' column to book_suggestions table")
            execute_query(
                """
                ALTER TABLE book_suggestions 
                ADD COLUMN isbn VARCHAR(20) NULL DEFAULT NULL 
                COMMENT 'ISBN number of the suggested book' AFTER author
                """
            )
            return True
        return False
    except Exception as e:
        current_app.logger.error(f"Error ensuring isbn column exists: {str(e)}")
        return False




@member_bp.route("/toggle_anon", methods=["POST"])
@member_required
def toggle_anon():
    """Toggles anonymous mode for the session."""
    data = request.get_json()
    is_anon = data.get('anon', False)
    session['is_anon'] = is_anon
    return jsonify({"success": True, "is_anon": is_anon})

# ===============================
# MEMBER DASHBOARD ROUTE
# ===============================

@member_bp.route("/goal/update", methods=["POST"])
@member_required
def member_update_goal_route():
    """Updates the user's annual reading goal target."""
    from backend.services.goal_service import update_goal_target
    user_id = session.get("user_id")
    target = request.form.get("target", type=int)
    
    if target and target > 0:
        result = update_goal_target(user_id, target)
        flash(result)
    else:
        flash("❌ Invalid goal target", "error")
        
    return redirect("/member/dashboard")


# ===============================
# MEMBER DASHBOARD (GET)
# ===============================

@member_bp.route("/dashboard")
@member_required
def member_dashboard():
    """
    Member dashboard – displays books currently issued to the member.
    """
    user_id = session["user_id"]

    # FETCH CURRENT ISSUES
    issues = fetch_all(
        """
        SELECT b.title, i.issue_date, i.return_date, i.fine
        FROM issues i
        JOIN books b ON i.book_id = b.book_id
        WHERE i.user_id = %s
        ORDER BY i.issue_date DESC
        """,
        (user_id,)
    )

    # FETCH ACTIVITIES
    from backend.services.activity_service import get_user_activities
    activities = get_user_activities(user_id)

    # FETCH RECOMMENDATIONS
    from backend.services.recommendation_service import get_smart_recommendations
    recommendations = get_smart_recommendations(user_id)

    # FETCH READING GOAL
    from backend.services.goal_service import get_or_create_goal
    reading_goal = get_or_create_goal(user_id)

    # FETCH GAMIFICATION STATS
    from backend.services.gamification_service import get_user_stats
    game_stats = get_user_stats(user_id)

    return render_template(
        "member/overview.html",
        active_page="member_overview",
        issues=issues,
        activities=activities,
        recommendations=recommendations,
        reading_goal=reading_goal,
        game_stats=game_stats
    )


@member_bp.route("/book/read/<int:book_id>")
@member_required
def member_read_book(book_id):
    """Renders the in-app digital reader for a specific book."""
    from backend.repository.db_access import fetch_one
    
    # Fetch book details
    book = fetch_one("SELECT * FROM books WHERE book_id = %s", (book_id,))
    
    if not book:
        flash("❌ Book not found", "error")
        return redirect("/member/dashboard")
        
    if not book.get("pdf_src"):
        flash("❌ Digital version not available for this book", "error")
        return redirect("/member/dashboard")
        
    return render_template("member/reader.html", book=book)


# ===============================
# BOOK CATALOG (GET)
# ===============================

@member_bp.route("/catalog")
@member_required
def member_catalog_view():
    """
    Renders the searchable Book Catalog with server-side pagination.
    """
    from flask import request
    from backend.services.book_service import view_books_paginated, get_all_authors, get_all_categories
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    author_id = request.args.get('author_id', type=int)
    category_filter = request.args.get('category', '')
    
    per_page = 12  # Grid looks better with 12 items
    
    pagination = view_books_paginated(page, 12, search_query, author_id, category_filter)
    
    authors = get_all_authors()
    categories = get_all_categories()

    return render_template(
        "member/catalog.html",
        active_page="member_catalog",
        books=pagination['books'],
        total=pagination['total'],
        current_page=pagination['page'],
        total_pages=pagination['total_pages'],
        q=search_query,
        selected_author_id=author_id,
        selected_category=category_filter,
        authors=authors,
        categories=categories
    )


@member_bp.route("/community")
@member_required
def member_community():
    """Renders the Community Hub (Client-side loaded)."""
    from backend.services.auth_service import get_user_by_id
    user = get_user_by_id(session["user_id"])
    
    # Sync session data in case it was missed during login or changed elsewhere
    if user:
        session["profile_pic"] = user.get("profile_pic")
        session["name"] = user.get("name")
    
    return render_template(
        "member/community.html",
        active_page="member_community",
        user=user,
        user_id=session["user_id"]
    )




@member_bp.route("/profile/privacy", methods=["POST"])
@member_required
def member_toggle_privacy():
    """Toggles user profile visibility."""
    from backend.services.social_service import toggle_profile_privacy
    is_public = request.form.get("is_public") == "on"
    result = toggle_profile_privacy(session["user_id"], is_public)
    flash(result)
    return redirect("/member/dashboard")

@member_bp.route("/review/like", methods=["POST"])
@member_required
def member_like_review():
    """Likes a book review."""
    from backend.services.social_service import like_review
    review_id = request.form.get("review_id", type=int)
    result = like_review(session["user_id"], review_id)
    return jsonify({"message": result})


@member_bp.route("/author/<int:author_id>")
@member_required
def member_author_view(author_id):
    """Shows author profile and their books."""
    from backend.services.author_service import get_author_details, get_author_books
    author = get_author_details(author_id)
    books = get_author_books(author_id)
    return render_template("member/author.html", author=author, books=books)

@member_bp.route("/series/<int:series_id>")
@member_required
def member_series_view(series_id):
    """Shows series details and ordered books."""
    from backend.services.author_service import get_series_details, get_series_books
    series = get_series_details(series_id)
    books = get_series_books(series_id)
    return render_template("member/series.html", series=series, books=books)


# ===============================
# REQUEST BOOK (POST)
# ===============================

@member_bp.route("/request", methods=["POST"])
@member_required
def member_request_book():
    """
    Handles book request submissions.
    """
    from flask import request, redirect, flash
    from backend.services.request_service import create_request

    user_id = session["user_id"]
    book_id = request.form.get("book_id")

    result = create_request(user_id, book_id)
    
    flash(result)
    return redirect("/member/catalog")


# ===============================
# SUGGEST A BOOK (GET & POST)
# ===============================

@member_bp.route("/suggest-book", methods=["GET", "POST"])
@member_required
def member_suggest_book():
    """
    GET: Displays the book suggestion form
    POST: Handles book suggestion submissions from members
    
    Robust implementation: dynamically detects schema variations.
    """
    from flask import request, redirect, flash, render_template, jsonify, current_app
    from backend.repository.db_access import execute_query, fetch_all
    from datetime import datetime
    
    # helper to get available columns
    def get_table_columns():
        try:
            # SHOW COLUMNS returns dict with 'Field' key when using dictionary cursor
            cols = fetch_all("SHOW COLUMNS FROM book_suggestions")
            return {c['Field'] for c in cols}
        except Exception:
            return set()
    
    available_columns = get_table_columns()
    
    # If table doesn't exist or we can't read it
    if not available_columns:
        flash("❌ System Error: Book suggestions table is missing or inaccessible.", "error")
        return redirect("/member/dashboard")

    # -----------------------------
    # GET REQUEST (View Suggestions)
    # -----------------------------
    if request.method == 'GET':
        try:
            user_id = session["user_id"]
            
            # Map correct column names based on what exists
            # We want: id, title, author, notes, date, status
            
            # 1. ID
            id_col = "suggestion_id" if "suggestion_id" in available_columns else "id"
            
            # 2. Notes / Reason
            notes_col = "notes"
            if "notes" not in available_columns and "reason" in available_columns:
                notes_col = "reason"
            
            # 3. Date - MUST alias to 'created_at' for template compatibility
            date_col = "created_at"
            if "created_at" not in available_columns and "suggestion_date" in available_columns:
                date_col = "suggestion_date"
                
            # 4. ISBN (optional for display)
            isbn_col = ", isbn" if "isbn" in available_columns else ""

            # Construct Query - Alias date_col to created_at
            query = f"""
                SELECT 
                    {id_col} as suggestion_id, 
                    title, 
                    author, 
                    {notes_col} as notes, 
                    {date_col} as created_at, 
                    status
                    {isbn_col}
                FROM book_suggestions 
                WHERE user_id = %s 
                ORDER BY {date_col} DESC
            """
            
            suggestions = fetch_all(query, (user_id,))
            
            return render_template(
                "member/suggest_book.html",
                active_page="suggest_book",
                suggestions=suggestions or []
            )
            
        except Exception as e:
            current_app.logger.error(f"Error in member_suggest_book (GET): {str(e)}")
            flash("❌ An error occurred while loading the page. Please ensure your database is updated.", "error")
            return redirect("/member/dashboard")
    
    # -----------------------------
    # POST REQUEST (Submit Suggestion)
    # -----------------------------
    
    user_id = session["user_id"]
    is_json_request = request.is_json or (request.content_type and 'application/json' in request.content_type)
    
    try:
        # Get Data
        if is_json_request:
            data = request.get_json(force=True, silent=True) or {}
            title = data.get("title", "").strip()
            author = data.get("author", "").strip()
            isbn = data.get("isbn", "").strip()
            notes = data.get("notes", "").strip()
        else:
            title = request.form.get("title", "").strip()
            author = request.form.get("author", "").strip()
            isbn = request.form.get("isbn", "").strip()
            notes = request.form.get("notes", "").strip()

        # Validation
        if not title or not author:
            msg = "❌ Title and Author are required."
            if is_json_request: return jsonify({"error": msg}), 400
            flash(msg, "error")
            return redirect(url_for("member.member_suggest_book"))

        # Build Dynamic INSERT
        insert_cols = ["user_id", "title", "author"]
        insert_vals = [user_id, title, author]
        
        # ISBN
        if "isbn" in available_columns and isbn:
            insert_cols.append("isbn")
            insert_vals.append(isbn)
            
        # Notes / Reason
        if "notes" in available_columns:
            insert_cols.append("notes")
            insert_vals.append(notes)
        elif "reason" in available_columns:
            insert_cols.append("reason")
            insert_vals.append(notes)
            
        # Date
        if "created_at" in available_columns:
            insert_cols.append("created_at")
            insert_vals.append(datetime.utcnow())
        elif "suggestion_date" in available_columns:
            insert_cols.append("suggestion_date")
            insert_vals.append(datetime.utcnow())
            
        # Status
        if "status" in available_columns:
            insert_cols.append("status")
            insert_vals.append("pending")
            
        # Execute
        ph = ", ".join(["%s"] * len(insert_vals))
        col_str = ", ".join(insert_cols)
        
        from backend.config.db import get_connection
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(f"INSERT INTO book_suggestions ({col_str}) VALUES ({ph})", insert_vals)
            conn.commit()
            new_id = cursor.lastrowid
            
            if is_json_request:
                return jsonify({"message": "Success!", "suggestion_id": new_id}), 200
        finally:
            cursor.close()
            conn.close()
            
        flash("✅ Suggestion submitted successfully!", "success")
        return redirect(url_for("member.member_suggest_book"))
        
    except Exception as e:
        current_app.logger.error(f"Error in member_suggest_book (POST): {str(e)}")
        msg = f"Error submitting suggestion: {str(e)}"
        if is_json_request: return jsonify({"error": msg}), 500
        flash(f"❌ {msg}", "error")
        return redirect(url_for("member.member_suggest_book"))


@member_bp.route("/delete-account", methods=["POST"])
@member_required
def member_delete_my_account():
    """
    Allows a member to delete their own account.
    """
    from flask import flash, redirect, session
    from backend.services.user_service import delete_user
    
    user_id = session.get("user_id")
    result = delete_user(user_id)
    
    if "✅" in result or "successfully" in result.lower():
        # Clear session after deletion
        session.clear()
        flash("Your account has been permanently deleted.")
        return redirect("/")
    else:
        flash(result, "error")
        return redirect("/member/dashboard")


@member_bp.route("/review/add", methods=["POST"])
@member_required
def member_submit_review():
    """
    Handles review submission.
    """
    from flask import request, redirect, flash, session
    from backend.services.review_service import add_review
    
    user_id = session.get("user_id")
    book_id = request.form.get("book_id")
    rating = request.form.get("rating")
    comment = request.form.get("comment")
    
    if not rating:
        flash("❌ Please provide a rating.", "error")
        return redirect(f"/member/catalog") # Ideally redirect to book details
        
    result = add_review(user_id, book_id, int(rating), comment)
    
    # Gamification Hook
    if "✅" in result:
        try:
            from backend.services.gamification_service import check_and_award_badges
            new_badges = check_and_award_badges(user_id, 'review')
            if new_badges:
                flash(f"🏆 You earned new badges: {', '.join(new_badges)}!", "success")
            
            from backend.services.activity_service import log_user_activity
            log_user_activity(user_id, "REVIEW", f"Reviewed book #{book_id}")
        except Exception as e:
            print(f"Gamification/Activity Error: {e}")
            
    flash(result)
    
    # Stay on catalog for now, or redirect to Referer
    return redirect(request.referrer or "/member/catalog")


@member_bp.route("/profile")
@member_required
def member_profile():
    """renders the profile page"""
    from backend.services.gamification_service import get_user_badges
    from backend.repository.db_access import fetch_one # Direct DB access to bypass stale service
    
    user_id = session["user_id"]
    
    # Direct Query to ensure we get the profile_pic (Bypassing potential stale user_service)
    user = fetch_one(
        "SELECT user_id, name, email, role, created_at, profile_pic FROM users WHERE user_id = %s",
        (user_id,)
    )
    
    badges = get_user_badges(user_id)
    
    # DEBUG: Check if profile_pic is present
    print(f"👤 Profile Page: User Data = {user}", flush=True)
    
    return render_template("member/profile.html", active_page="member_profile", profile_user=user, badges=badges)

@member_bp.route("/profile/upload", methods=["POST"])
@member_required
def upload_profile_pic():
    """Handles avatar upload"""
    from werkzeug.utils import secure_filename
    import os
    
    if 'avatar' not in request.files:
        flash("❌ No file selected", "error")
        return redirect("/member/profile")
        
    file = request.files['avatar']
    if file.filename == '':
        flash("❌ No file selected", "error")
        return redirect("/member/profile")
        
    if file:
        try:
            filename = secure_filename(f"user_{session['user_id']}_{int(datetime.now().timestamp())}.png")
            
            # Method 3: Absolute Path via Pathlib (Bulletproof)
            from pathlib import Path
            
            # This file is: .../backend/routes/member_routes.py
            # We want: .../static/uploads/avatars
            
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent # routes -> backend -> pythonProject
            upload_dir = project_root / "static" / "uploads" / "avatars"
            
            # Print for debug
            print(f"📂 Upload Target Path (Pathlib): {upload_dir}", flush=True)
            
            os.makedirs(upload_dir, exist_ok=True)
            
            save_path = os.path.join(upload_dir, filename)
            file.save(save_path)
            
            # Update DB
            # We store relative path 'uploads/avatars/...' so templating is easy
            db_path = f"uploads/avatars/{filename}"
            
            execute_query(
                "UPDATE users SET profile_pic = %s WHERE user_id = %s",
                (db_path, session["user_id"])
            )
            
            # Update session too so layout updates immediately
            session['profile_pic'] = db_path
            
            flash("✅ Profile picture updated!", "success")
        except Exception as e:
            flash(f"❌ Upload failed: {str(e)}", "error")
            
    return redirect("/member/profile")






@member_bp.route("/profile/update", methods=["POST"])
@member_required
def member_update_profile():
    """Updates basic profile info (name, bio)"""
    from backend.services.user_service import update_user_bio
    from backend.repository.db_access import execute
    
    user_id = session["user_id"]
    data = request.get_json() or {}
    
    bio = data.get("bio", "").strip()
    name = data.get("name", "").strip()
    
    try:
        if bio:
            update_user_bio(user_id, bio)
        
        if name:
            execute("UPDATE users SET name = %s WHERE user_id = %s", (name, user_id))
            session["name"] = name # Update session cache
            
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@member_bp.route("/ai-chat", methods=["GET", "POST"])
@member_required
def member_ai_chat():
    """
    Renders the AI Assistant Chat Interface.
    Handlers API requests for chat interaction.
    """
    from flask import render_template, request, jsonify, session
    from backend.brain.orchestrator import brain
    
    # API Handler
    if request.method == "POST":
        data = request.json
        user_message = data.get("message")
        history = data.get("history", []) # List of {role, content}
        
        if not user_message:
            return jsonify({"error": "Empty message"}), 400
            
        # Process with Brain (LLM + RAG)
        ai_response = brain.process_message(user_message, history)
        
        return jsonify({
            "response": ai_response,
            "timestamp": "Just now"
        })
    
    # Page Render
    return render_template(
        "member/ai_chat.html",
        active_page="ai_chat",
        user=session.get("user")
    )


@member_bp.route("/waitlist/join", methods=["POST"])
@member_required
def join_waitlist_route():
    from backend.services.reservation_service import join_waitlist
    
    user_id = session.get("user_id")
    book_id = request.form.get("book_id")
    
    result = join_waitlist(user_id, book_id)
    flash(result)
    return redirect("/member/catalog")


@member_bp.route("/wishlist")
@member_required
def member_wishlist():
    from backend.services.wishlist_service import get_user_wishlist
    books = get_user_wishlist(session["user_id"])
    return render_template("member/wishlist.html", active_page="member_wishlist", books=books)

@member_bp.route("/wishlist/add", methods=["POST"])
@member_required
def add_wishlist_route():
    from backend.services.wishlist_service import add_to_wishlist
    result = add_to_wishlist(session["user_id"], request.form.get("book_id"))
    flash(result)
    return redirect(request.referrer or "/member/catalog")

@member_bp.route("/wishlist/remove", methods=["POST"])
@member_required
def remove_wishlist_route():
    from backend.services.wishlist_service import remove_from_wishlist
    result = remove_from_wishlist(session["user_id"], request.form.get("book_id"))
    flash(result)
    return redirect("/member/wishlist")


@member_bp.route("/support", methods=["GET", "POST"])
@member_required
def member_support():
    from backend.services.support_service import create_ticket, get_user_tickets
    
    if request.method == "POST":
        subject = request.form.get("subject")
        message = request.form.get("message")
        result = create_ticket(session["user_id"], subject, message)
        flash(result)
        return redirect("/member/support")
        
    tickets = get_user_tickets(session["user_id"])
    return render_template("member/support.html", active_page="member_support", tickets=tickets)

@member_bp.route("/support/<int:ticket_id>", methods=["GET", "POST"])
@member_required
def member_ticket_view(ticket_id):
    from backend.services.support_service import get_ticket_details, add_reply
    
    if request.method == "POST":
        message = request.form.get("message")
        result = add_reply(ticket_id, session["user_id"], message)
        flash(result)
        return redirect(f"/member/support/{ticket_id}")
        
    data = get_ticket_details(ticket_id)
    if not data:
        flash("❌ Ticket not found", "error")
        return redirect("/member/support")
        
    return render_template("member/ticket_view.html", active_page="member_support", **data)


@member_bp.route("/api-keys", methods=["GET"])
@member_required
def member_api_keys_view():
    from backend.services.api_service import get_user_keys
    keys = get_user_keys(session["user_id"])
    return render_template("member/api_keys.html", active_page="member_api_keys", keys=keys)

@member_bp.route("/api-keys/generate", methods=["POST"])
@member_required
def generate_api_key_route():
    from backend.services.api_service import generate_key
    key = generate_key(session["user_id"])
    if key:
        flash(f"✅ New API Key Generated: {key}")
    else:
        flash("❌ Failed to generate key")
    return redirect("/member/api-keys")

@member_bp.route("/api-keys/delete/<int:key_id>", methods=["POST"])
@member_required
def delete_api_key_route(key_id):
    from backend.services.api_service import delete_key
    result = delete_key(key_id, session["user_id"])
    flash(result)
    return redirect("/member/api-keys")

@member_bp.route("/ai/chat", methods=["POST"])
@member_required
def ai_chat_route():
    """Endpoint for the floating AI librarian chatbot."""
    data = request.get_json()
    user_query = data.get("prompt", "")
    
    if not user_query:
        return jsonify({"response": "I didn't catch that. Could you repeat?"})
        
    from backend.services.ai_service import chat_with_librarian
    response = chat_with_librarian(user_query)
    
    return jsonify({"response": response})

@member_bp.route("/ai/discovery", methods=["GET", "POST"])
@member_required
def ai_discovery_route():
    """Renders the AI Discovery page and handles 'vibe' requests."""
    if request.method == "POST":
        data = request.get_json()
        vibe = data.get("vibe", "")
        if not vibe:
            return jsonify({"response": "Tell me a bit about your mood or what you're looking for!"})
            
        from backend.services.discovery_service import discover_by_vibe
        response = discover_by_vibe(vibe)
        return jsonify({"response": response})
        
    return render_template("member/discovery.html", active_page="member_discovery")

@member_bp.route("/search_users_json", methods=["GET"])
@member_required
def search_users_json():
    """Returns a JSON list of users matching the query."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify({"users": []})
        
    users = fetch_all("""
        SELECT user_id, name, profile_pic, role 
        FROM users 
        WHERE name LIKE %s OR role LIKE %s
        LIMIT 10
    """, (f"%{query}%", f"%{query}%"))
    
    return jsonify({"users": users})

@member_bp.app_template_filter('datetimeformat')
def datetimeformat(value, format='%Y-%m-%d %H:%M'):
    if value is None:
        return ""
    return value.strftime(format)
