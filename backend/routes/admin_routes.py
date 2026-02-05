"""
admin_routes.py
----------------
Defines ALL Flask routes that are accessible ONLY to ADMIN users.

DESIGN PRINCIPLES FOLLOWED:
- Routes handle HTTP only (request / response)
- Business logic is delegated to SERVICE layer
- No direct DB mutations in routes
- Clean separation of concerns (MVC / Clean Architecture)
"""

# =====================================================
# FLASK CORE IMPORTS
# =====================================================

from flask import (
    Blueprint,          # Groups admin-related routes
    render_template,    # Renders Jinja2 HTML templates
    session,            # Stores logged-in user info
    redirect,           # Redirects browser to another URL
    request,            # Reads POSTed form data
    flash,              # Sends messages to UI
    url_for             # Generates URLs for routes
)

# =====================================================
# INTERNAL PROJECT IMPORTS
# =====================================================

# DB read helper (single-row SELECT)
from backend.repository.db_access import fetch_one, fetch_all

# Access control decorator
from backend.utils.decorators import admin_required

# Service-layer functions (business logic)
from backend.services.user_service import view_users, add_user
from backend.services.book_service import view_books_paginated, view_books
from backend.services.issue_service import issue_book, return_book, send_overdue_reminders
from backend.services.request_service import get_pending_requests, process_request
from backend.services.report_service import most_issued_books, most_active_users, monthly_issue_count, export_report, book_category_distribution

# =====================================================
# BLUEPRINT DEFINITION
# =====================================================


# All admin routes will be registered under this blueprint
admin_bp = Blueprint("admin", __name__)


# =====================================================
# ADMIN DASHBOARD (GET)
# =====================================================

# =====================================================
# ADMIN OVERVIEW (DASHBOARD)
# =====================================================

@admin_bp.route("/dashboard")
@admin_bp.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    """Renders the Admin Overview with statistics and analytics."""
    from backend.services.analytics_service import get_monthly_borrowing_stats, get_category_stats, get_user_engagement_stats, get_quick_stats
    
    quick_stats = get_quick_stats()
    monthly_stats = get_monthly_borrowing_stats()
    category_stats = get_category_stats()
    user_stats = get_user_engagement_stats()

    # Recent activity for overview
    recent_issues = fetch_all(
        """
        SELECT i.issue_id, u.name AS user_name, b.title AS book_title, i.issue_date
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        ORDER BY i.issue_date DESC LIMIT 5
        """
    )

    return render_template(
        "admin/overview.html",
        active_page="admin_overview",
        quick_stats=quick_stats,
        monthly_stats=monthly_stats,
        category_stats=category_stats,
        user_stats=user_stats,
        recent_issues=recent_issues
    )


# =====================================================
# BOOK MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/admin/books")
@admin_required
def admin_books_view():
    """Renders the Books Management page with pagination and metadata."""
    from backend.services.author_service import get_all_authors, get_all_series
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    pagination = view_books_paginated(page, 10, search_query)
    authors = get_all_authors()
    series_list = get_all_series()
    
    return render_template(
        "admin/books.html",
        active_page="admin_books",
        books=pagination['books'],
        total=pagination['total'],
        current_page=pagination['page'],
        total_pages=pagination['total_pages'],
        q=search_query,
        authors=authors,
        series_list=series_list
    )


@admin_bp.route("/admin/books/get/<int:book_id>")
@admin_required
def admin_get_book_json(book_id):
    """Securely returns book details for the Edit Modal."""
    from backend.services.book_service import get_book
    from flask import jsonify
    try:
        book = get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found", "success": False}), 404
        return jsonify({"success": True, "data": book})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@admin_bp.route("/admin/book/add", methods=["POST"])
@admin_required
def admin_add_book_route():
    """Adds a new book with relational author/series support."""
    from backend.services.book_service import add_book
    from werkzeug.utils import secure_filename
    import os
    from datetime import datetime
    
    title = request.form.get("title")
    author_id = request.form.get("author_id", type=int)
    series_id = request.form.get("series_id", type=int) or None
    series_order = request.form.get("series_order", type=int) or None
    category = request.form.get("category")
    copies = request.form.get("copies", type=int)
    
    if not all([title, author_id, category, copies]):
        flash("❌ All required fields must be filled", "error")
        return redirect("/admin/books")
        
    p_src = None
    if 'pdf_file' in request.files:
        file = request.files['pdf_file']
        if file and file.filename != '':
            filename = secure_filename(f"ebook_{int(datetime.now().timestamp())}_{file.filename}")
            save_path = os.path.join("static", "uploads", "ebooks", filename)
            file.save(save_path)
            pdf_src = f"uploads/ebooks/{filename}"
            
    # MANUAL PIVOT: Handle New Author/Series Creation
    from backend.repository.db_access import fetch_one, execute
    
    # 1. Handle Author (ID or New Name)
    final_author_id = author_id
    new_author_name = request.form.get("new_author_name")
    if new_author_name and new_author_name.strip():
        # Check if exists
        existing_auth = fetch_one("SELECT author_id FROM authors WHERE name = %s", (new_author_name.strip(),))
        if existing_auth:
             final_author_id = existing_auth['author_id']
        else:
             execute("INSERT INTO authors (name) VALUES (%s)", (new_author_name.strip(),))
             final_author_id = fetch_one("SELECT author_id FROM authors WHERE name = %s", (new_author_name.strip(),))['author_id']
    
    # 2. Handle Series (ID or New Name)
    final_series_id = series_id
    new_series_name = request.form.get("new_series_name")
    if new_series_name and new_series_name.strip():
        existing_series = fetch_one("SELECT series_id FROM series WHERE name = %s", (new_series_name.strip(),))
        if existing_series:
            final_series_id = existing_series['series_id']
        else:
            execute("INSERT INTO series (name) VALUES (%s)", (new_series_name.strip(),))
            final_series_id = fetch_one("SELECT series_id FROM series WHERE name = %s", (new_series_name.strip(),))['series_id']

    # Add Book
    book_id = add_book(title, final_author_id, category, copies, pdf_src, final_series_id, series_order)
    
    # AI ENRICHMENT (Restored via Open Source)
    from backend.services.enrichment_service import enrich_book_metadata
    enrich_result = enrich_book_metadata(book_id)
    
    if isinstance(book_id, int):
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "ADD_BOOK", f"Title: {title}")
        flash(f"✅ Book added successfully! {enrich_result}")
    else:
        flash(book_id) # Error message

    return redirect("/admin/books")


@admin_bp.route("/admin/book/edit/<int:book_id>", methods=["POST"])
@admin_required
def admin_edit_book_route(book_id):
    """Updates book details."""
    from backend.services.book_service import update_book
    
    title = request.form.get("title")
    author_id = request.form.get("author_id", type=int)
    series_id = request.form.get("series_id", type=int) or None
    series_order = request.form.get("series_order", type=int) or None
    category = request.form.get("category")
    total_copies = request.form.get("copies", type=int)
    
    # MANUAL PIVOT: Handle New Author/Series Creation
    from backend.repository.db_access import fetch_one, execute
    
    # 1. Handle Author
    final_author_id = author_id
    new_author_name = request.form.get("new_author_name")
    if new_author_name and new_author_name.strip():
        existing_auth = fetch_one("SELECT author_id FROM authors WHERE name = %s", (new_author_name.strip(),))
        if existing_auth:
             final_author_id = existing_auth['author_id']
        else:
             execute("INSERT INTO authors (name) VALUES (%s)", (new_author_name.strip(),))
             final_author_id = fetch_one("SELECT author_id FROM authors WHERE name = %s", (new_author_name.strip(),))['author_id']
    
    # 2. Handle Series
    final_series_id = series_id
    new_series_name = request.form.get("new_series_name")
    if new_series_name and new_series_name.strip():
        existing_series = fetch_one("SELECT series_id FROM series WHERE name = %s", (new_series_name.strip(),))
        if existing_series:
            final_series_id = existing_series['series_id']
        else:
            execute("INSERT INTO series (name) VALUES (%s)", (new_series_name.strip(),))
            final_series_id = fetch_one("SELECT series_id FROM series WHERE name = %s", (new_series_name.strip(),))['series_id']

    if not all([title, author_id, category, total_copies]):
        flash("❌ Required fields are missing", "error")
        return redirect("/admin/books")

    result = update_book(book_id, title, final_author_id, category, total_copies, final_series_id, series_order)
    
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "EDIT_BOOK", f"Book ID: {book_id}, Title: {title}")

    flash(result)
    return redirect("/admin/books")

@admin_bp.route("/admin/book/fetch-metadata", methods=["POST"])
@admin_required
def admin_fetch_metadata():
    """Fetches book details by ISBN from external APIs."""
    from backend.services.metadata_service import process_metadata_for_form
    data = request.get_json()
    isbn = data.get("isbn")
    
    if not isbn:
        return jsonify({"error": "ISBN is required"}), 400
        
    metadata = process_metadata_for_form(isbn)
    if not metadata:
        return jsonify({"error": "No data found for this ISBN"}), 404
        
    return jsonify(metadata)


@admin_bp.route("/admin/books/import", methods=["POST"])
@admin_required
def admin_import_books_route():
    """Bulk imports books from CSV and enriches them with AI."""
    from backend.services.book_service import add_book
    from backend.services.enrichment_service import enrich_book_metadata
    import pandas as pd
    
    if 'csv_file' not in request.files:
        flash("❌ No file selected", "error")
        return redirect("/admin/books")
        
    file = request.files['csv_file']
    if not file or file.filename == '':
        flash("❌ No file selected", "error")
        return redirect("/admin/books")
        
    try:
        # Load and normalize headers
        df = pd.read_csv(file)
        df.columns = [c.strip().lower() for c in df.columns]
        
        success_count = 0
        for _, row in df.iterrows():
            try:
                # Find or Create Author
                author_name = str(row['author']).strip()
                from backend.repository.db_access import fetch_one, execute
                author = fetch_one("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                if not author:
                    execute("INSERT INTO authors (name) VALUES (%s)", (author_name,))
                    author = fetch_one("SELECT author_id FROM authors WHERE name = %s", (author_name,))
                
                # Add Book Record
                b_id = add_book(
                    str(row['title']).strip(), 
                    author['author_id'], 
                    str(row['category']).strip(), 
                    int(row['copies'])
                )
                
                # Trigger Background Intelligence enrichment
                if isinstance(b_id, int):
                    enrich_book_metadata(b_id)
                    success_count += 1
            except Exception as row_err:
                print(f"⚠️ Skipping import row: {row_err}")
                continue
                
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "IMPORT_BOOKS", f"Bulk Import: {success_count} books enriched via AI.")
        flash(f"✅ Successfully imported and enriched {success_count} books.")
    except Exception as e:
        flash(f"❌ Import failed: {str(e)}", "error")
            
    return redirect("/admin/books")


# =====================================================
# MODERN BOOKS MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/books-management")
@admin_required
def books_management():
    """Renders the modern Books Management page with add/delete functionality."""
    books = view_books()
    return render_template(
        "books_management.html",
        active_page="books_management",
        books=books
    )


@admin_bp.route("/admin/books/export")
@admin_required
def admin_export_books():
    """Generates and downloads book catalog as CSV."""
    from backend.services.bulk_service import export_books_csv
    from flask import Response
    
    csv_data = export_books_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=library_catalog_export.csv"}
    )

# Duplicate import route removed to resolve conflict and IndentationError. 
# Replaced by admin_import_books_route which includes AI background enrichment.


# =====================================================
# USER MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/admin/users")
@admin_required
def admin_users_view():
    """Renders the User Management page."""
    users = view_users()
    return render_template(
        "admin/users.html",
        active_page="admin_users",
        users=users
    )

@admin_bp.route("/admin/user/tier", methods=["POST"])
@admin_required
def admin_update_user_tier_route():
    """Updates a user's membership tier."""
    from backend.services.membership_service import update_user_tier
    user_id = request.form.get("user_id", type=int)
    new_tier = request.form.get("tier")
    
    if not all([user_id, new_tier]):
        flash("❌ Missing data", "error")
        return redirect("/admin/users")
        
    result = update_user_tier(user_id, new_tier)
    flash(result)
    
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "UPDATE_TIER", f"User: {user_id}, Tier: {new_tier}")
        
    return redirect("/admin/users")


# =====================================================
# BOOK MANAGEMENT (ADD/DELETE)
# =====================================================

@admin_bp.route("/admin/book/delete/<int:book_id>", methods=["POST"])
@admin_required
def admin_delete_book(book_id):
    """Deletes a book from the inventory."""
    from backend.repository.db_access import execute
    try:
        execute("DELETE FROM books WHERE book_id = %s", (book_id,))
        flash("✅ Book deleted successfully!")
    except Exception as e:
        flash(f"❌ Error deleting book: {e}", "error")
    return redirect("/admin/books")


# =====================================================
# ISSUE/RETURN MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/admin/issues")
@admin_required
def admin_issues_view():
    """Renders the Issue/Return Management page."""
    users = view_users()
    books = view_books()
    active_issues = fetch_all(
        """
        SELECT i.issue_id, u.name AS user_name, b.title AS book_title, i.issue_date
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        WHERE i.return_date IS NULL
        ORDER BY i.issue_date DESC
        """
    )
    past_issues = fetch_all(
        """
        SELECT i.issue_id, u.name AS user_name, b.title AS book_title, i.issue_date, i.return_date, i.fine, i.fine_paid
        FROM issues i
        JOIN users u ON i.user_id = u.user_id
        JOIN books b ON i.book_id = b.book_id
        WHERE i.return_date IS NOT NULL
        ORDER BY i.return_date DESC
        """
    )

    return render_template(
        "admin/issues.html",
        active_page="admin_issues",
        users=users,
        books=books,
        active_issues=active_issues,
        past_issues=past_issues
    )


# =====================================================
# REQUEST MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/admin/requests")
@admin_required
def admin_requests_view():
    """Renders the Pending Requests page."""
    pending_requests = get_pending_requests()
    if pending_requests is None:
        flash("⚠️ Database Error: 'book_requests' table missing.", "error")
        pending_requests = []
    
    return render_template(
        "admin/requests.html",
        active_page="admin_requests",
        pending_requests=pending_requests
    )


# =====================================================
# BOOK SUGGESTIONS (GET)
# =====================================================

@admin_bp.route("/admin/suggestions")
@admin_required
def admin_suggestions_view():
    """Renders the Book Suggestions page with member recommendations."""
    try:
        # Helper to get available columns
        try:
            cols = fetch_all("SHOW COLUMNS FROM book_suggestions")
            available_columns = {c['Field'] for c in cols}
        except:
            available_columns = set()

        if not available_columns:
            flash("⚠️ Database Error: 'book_suggestions' table not found.", "error")
            suggestions = []
        else:
            # 1. Notes / Reason
            notes_col = "notes"
            if "notes" not in available_columns and "reason" in available_columns:
                notes_col = "reason"
            
            # 2. Date
            date_col = "created_at"
            if "created_at" not in available_columns and "suggestion_date" in available_columns:
                date_col = "suggestion_date"

            # Construct Query with aliases for template compatibility
            # Template likely expects: suggestion_id, user_name, email, title, author, reason (or notes), suggestion_date, status
            query = f"""
            SELECT 
                bs.suggestion_id, 
                bs.user_id, 
                u.name AS user_name, 
                u.email, 
                bs.title, 
                bs.author, 
                bs.{notes_col} AS reason, 
                bs.{date_col} AS suggestion_date, 
                bs.status
            FROM book_suggestions bs
            JOIN users u ON bs.user_id = u.user_id
            ORDER BY bs.{date_col} DESC
            """
            
            suggestions = fetch_all(query)
            
            if suggestions is None:
                suggestions = []
                
    except Exception as e:
        flash(f"⚠️ Error loading suggestions: {str(e)}", "error")
        suggestions = []
    
    return render_template(
        "admin/suggestions.html",
        active_page="admin_suggestions",
        suggestions=suggestions
    )


# =====================================================
# APPROVE BOOK SUGGESTION (POST)
# =====================================================

@admin_bp.route("/admin/suggestion/approve/<int:suggestion_id>", methods=["POST"])
@admin_required
def admin_approve_suggestion(suggestion_id):
    """Approves a book suggestion and moves it to the Purchase List."""
    try:
        from backend.repository.db_access import execute_query
        execute_query(
            "UPDATE book_suggestions SET status = %s WHERE suggestion_id = %s",
            ("approved", suggestion_id)
        )
        flash("✅ Suggestion approved! Book moved to Purchase List.", "success")
    except Exception as e:
        flash(f"❌ Error approving suggestion: {str(e)}", "error")
    
    return redirect("/admin/suggestions")


# =====================================================
# REJECT BOOK SUGGESTION (POST)
# =====================================================

@admin_bp.route("/admin/suggestion/reject/<int:suggestion_id>", methods=["POST"])
@admin_required
def admin_reject_suggestion(suggestion_id):
    """Rejects a book suggestion."""
    try:
        from backend.repository.db_access import execute_query
        execute_query(
            "UPDATE book_suggestions SET status = %s WHERE suggestion_id = %s",
            ("rejected", suggestion_id)
        )
        flash("✅ Suggestion rejected.", "success")
    except Exception as e:
        flash(f"❌ Error rejecting suggestion: {str(e)}", "error")
    
    return redirect("/admin/suggestions")


# =====================================================
# PURCHASE LIST MANAGEMENT
# =====================================================

@admin_bp.route("/admin/purchase-list")
@admin_required
def admin_purchase_list_view():
    """Renders the Purchase List (Approved Suggestions)."""
    try:
        # Helper to get available columns
        try:
            cols = fetch_all("SHOW COLUMNS FROM book_suggestions")
            available_columns = {c['Field'] for c in cols}
        except:
            available_columns = set()

        if not available_columns:
            flash("⚠️ Database Error: 'book_suggestions' table missing.", "error")
            pending_purchases = []
        else:
            # 1. Notes / Reason
            notes_col = "notes"
            if "notes" not in available_columns and "reason" in available_columns:
                notes_col = "reason"
            
            # 2. Date
            date_col = "created_at"
            if "created_at" not in available_columns and "suggestion_date" in available_columns:
                date_col = "suggestion_date"

            # Construct Query (LEFT JOIN to include admin-added entries with NULL user_id)
            query = f"""
            SELECT 
                bs.suggestion_id, 
                bs.user_id, 
                COALESCE(u.name, 'Admin') AS user_name,
                bs.title, 
                bs.author, 
                bs.{notes_col} AS reason, 
                bs.{date_col} AS suggestion_date, 
                bs.status
            FROM book_suggestions bs
            LEFT JOIN users u ON bs.user_id = u.user_id
            WHERE bs.status = 'approved'
            ORDER BY bs.{date_col} DESC
            """
            
            pending_purchases = fetch_all(query)
            if pending_purchases is None:
                pending_purchases = []
                
    except Exception as e:
        flash(f"⚠️ Error loading purchase list: {str(e)}", "error")
        pending_purchases = []
    
    return render_template(
        "admin/purchase_list.html",
        active_page="admin_purchase_list",
        pending_purchases=pending_purchases
    )


@admin_bp.route("/admin/purchase-list/add/<int:suggestion_id>", methods=["POST"])
@admin_required
def admin_add_purchased_book(suggestion_id):
    """
    Finalizes purchase:
    1. Adds book to inventory
    2. Marks suggestion as 'completed'
    """
    try:
        from backend.repository.db_access import execute_query, fetch_all, fetch_one
        from backend.services.book_service import add_book
        
        # 1. Fetch details
        try:
            cols = fetch_all("SHOW COLUMNS FROM book_suggestions")
            available_columns = {c['Field'] for c in cols}
        except:
            available_columns = set()
            
        title_col = "title"
        author_col = "author"
        category_col = "category" if "category" in available_columns else None
        
        select_cols = f"{title_col}, {author_col}"
        if category_col:
            select_cols += f", {category_col}"
            
        suggestion = fetch_one(f"SELECT {select_cols} FROM book_suggestions WHERE suggestion_id = %s", (suggestion_id,))
        
        if not suggestion:
            flash("❌ Order not found.", "error")
            return redirect("/admin/purchase-list")
            
        # 2. Add to Library
        title = suggestion.get('title')
        author = suggestion.get('author')
        category = suggestion.get('category', 'General')
        
        result = add_book(title, author, category, 1) # Add 1 copy
        
        if "❌" in result:
            flash(result, "error")
            return redirect("/admin/purchase-list")
            
        # 3. Mark as Completed (HANDLING ENUM ISSUE properly)
        try:
            execute_query(
                "UPDATE book_suggestions SET status = %s WHERE suggestion_id = %s",
                ("completed", suggestion_id)
            )
        except Exception as e:
            # If ENUM error, try to expand it (Only works if user has permissions, but worth a try)
            # OR fallback to deleting the suggestion since it's now a real book
            if "Data truncated" in str(e) or "Review your MySQL error" in str(e):
                try:
                    execute_query("ALTER TABLE book_suggestions MODIFY COLUMN status ENUM('pending','approved','rejected','completed')")
                    execute_query(
                        "UPDATE book_suggestions SET status = %s WHERE suggestion_id = %s",
                        ("completed", suggestion_id)
                    )
                except:
                    # Fallback: Just delete it if we can't mark it completed
                    # This prevents it from staying in the list forever
                    execute_query("DELETE FROM book_suggestions WHERE suggestion_id = %s", (suggestion_id,))
                    flash(f"✅ Book added! (Order removed from list)", "success")
                    return redirect("/admin/purchase-list")
                    
        flash(f"✅ Book purchased and added to library: {title}", "success")
        
    except Exception as e:
        flash(f"❌ Error processing purchase: {str(e)}", "error")
        
    return redirect("/admin/purchase-list")


@admin_bp.route("/admin/purchase-list/remove/<int:suggestion_id>", methods=["POST"])
@admin_required
def admin_remove_purchase(suggestion_id):
    """
    Removes a book from the purchase list (sets status to 'rejected').
    """
    try:
        from backend.repository.db_access import execute_query
        execute_query(
            "UPDATE book_suggestions SET status = %s WHERE suggestion_id = %s",
            ("rejected", suggestion_id)
        )
        flash("✅ Item removed from purchase list.", "success")
    except Exception as e:
        flash(f"❌ Error removing item: {str(e)}", "error")
    
    return redirect("/admin/purchase-list")


@admin_bp.route("/admin/purchase/add-manual", methods=["POST"])
@admin_required
def admin_add_manual_purchase():
    """
    Adds a book to the purchase list manually (not from member suggestion).
    """
    try:
        from backend.repository.db_access import execute_query
        
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        notes = request.form.get("notes", "").strip()
        
        if not title or not author:
            flash("❌ Title and Author are required.", "error")
            return redirect("/admin/purchase-list")
        
        # Insert into book_suggestions with NULL user_id (indicates admin-added)
        # and status = 'approved' so it appears in purchase list
        execute_query(
            """
            INSERT INTO book_suggestions (user_id, title, author, reason, status, created_at)
            VALUES (NULL, %s, %s, %s, 'approved', NOW())
            """,
            (title, author, notes if notes else "Admin added")
        )
        
        flash(f"✅ Added to purchase list: {title} by {author}", "success")
        
    except Exception as e:
        flash(f"❌ Error adding to purchase list: {str(e)}", "error")
    
    return redirect("/admin/purchase-list")


# =====================================================
# REPORTS & ANALYTICS (GET)
# =====================================================

@admin_bp.route("/reports")
@admin_required
def admin_reports():
    """
    Renders the Library Insights page with 10 analytics widgets.
    """
    from collections import namedtuple
    from backend.services.report_service import (
        most_issued_books, most_active_users, 
        monthly_issue_count, book_category_distribution
    )
    from backend.repository.db_access import fetch_one
    
    ReportData = namedtuple('ReportData', ['most_issued', 'active_users', 'monthly', 'categories'])
    
    # Fetch data from services
    most_issued = most_issued_books()
    active_users = most_active_users()
    monthly = monthly_issue_count()
    categories = book_category_distribution()
    
    # Fetch quick stats
    total_books = fetch_one("SELECT COUNT(*) as cnt FROM books")
    total_members = fetch_one("SELECT COUNT(*) as cnt FROM users WHERE role = 'member'")
    active_issues = fetch_one("SELECT COUNT(*) as cnt FROM issues WHERE return_date IS NULL")
    
    # Use fine > 0 as proxy for overdue since we don't have due_date column
    overdue_books = fetch_one("""
        SELECT COUNT(*) as cnt FROM issues 
        WHERE return_date IS NULL AND fine > 0
    """)
    
    # Check if created_at column exists in books, otherwise skip
    try:
        new_books_month = fetch_one("""
            SELECT COUNT(*) as cnt FROM books 
            WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        """)
    except:
        new_books_month = {'cnt': 0}
        
    total_fines = fetch_one("SELECT COALESCE(SUM(fine), 0) as total FROM issues WHERE fine > 0")
    pending_fines = fetch_one("""
        SELECT COALESCE(SUM(fine), 0) as total FROM issues 
        WHERE fine > 0 AND return_date IS NULL
    """)
    returned_issues = fetch_one("SELECT COUNT(*) as cnt FROM issues WHERE return_date IS NOT NULL")
    
    quick_stats = {
        "total_books": total_books['cnt'] if total_books else 0,
        "total_members": total_members['cnt'] if total_members else 0,
        "active_issues": active_issues['cnt'] if active_issues else 0,
        "overdue_books": overdue_books['cnt'] if overdue_books else 0,
        "new_books_month": new_books_month['cnt'] if new_books_month else 0,
        "total_fines": float(total_fines['total']) if total_fines else 0,
        "pending_fines": float(pending_fines['total']) if pending_fines else 0,
    }

    # Prepare data for charts (frontend expects lists of values)
    chart_data = {
        "monthlyLabels": [r['month'] for r in monthly],
        "monthlyValues": [r['total_issues'] for r in monthly],
        "categoryLabels": [r['category'] for r in categories],
        "categoryValues": [r['book_count'] for r in categories],
        "activeIssues": quick_stats['active_issues'],
        "returnedIssues": returned_issues['cnt'] if returned_issues else 0,
        "statusValues": [quick_stats['active_issues'], returned_issues['cnt'] if returned_issues else 0]
    }
    
    data = ReportData(
        most_issued=most_issued,
        active_users=active_users,
        monthly=monthly,
        categories=categories
    )

    return render_template(
        "reports.html",
        active_page="admin_reports",
        data=data,
        chart_data=chart_data,
        quick_stats=quick_stats
    )


# =====================================================
# COMMUNITY HUB (GET/POST)
# =====================================================

@admin_bp.route("/admin/community")
@admin_required
def admin_community_hub():
    """Renders the Community Hub dashboard."""
    return render_template(
        "admin/community_hub.html",
        active_page="admin_community"
    )

@admin_bp.route("/admin/api/logs")
@admin_required
def admin_get_logs_api():
    """Returns system audit logs."""
    from backend.repository.db_access import fetch_all
    try:
        # Get logs with user names
        logs = fetch_all("""
            SELECT l.*, u.name as user_name, u.profile_pic, c.name as channel_name 
            FROM audit_logs l
            LEFT JOIN users u ON l.user_id = u.user_id
            LEFT JOIN channels c ON l.channel_id = c.channel_id
            ORDER BY l.timestamp DESC LIMIT 100
        """)
        
        # Format for JSON
        formatted = []
        for l in logs:
            formatted.append({
                'id': l['log_id'],
                'user': l['user_name'] or 'Unknown',
                'user_pic': l['profile_pic'],
                'action': l['action_type'],
                'details': l['details'],
                'channel': l['channel_name'] or 'General',
                'time': l['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if l['timestamp'] else ''
            })
            
        return {"success": True, "logs": formatted}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@admin_bp.route("/admin/api/chats")
@admin_required
def admin_get_chats_api():
    """Returns active chat groups."""
    from backend.repository.db_access import fetch_all
    try:
        # Get all channels except Global Chat (ID 1) typically
        # But user asked for list showing chat database which implies everything or groups
        chats = fetch_all("""
            SELECT c.channel_id, c.name, c.type, c.created_at, u.name as owner_name,
            (SELECT COUNT(*) FROM chat_messages WHERE channel_id = c.channel_id) as msg_count
            FROM channels c
            LEFT JOIN users u ON c.created_by = u.user_id
            ORDER BY msg_count DESC
        """)
        
        return {"success": True, "chats": chats}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@admin_bp.route("/admin/api/chat/delete/<int:channel_id>", methods=["POST"])
@admin_required
def admin_delete_chat(channel_id):
    """Deletes a specific chat channel."""
    from backend.repository.db_access import execute
    
    if channel_id == 1:
        return {"success": False, "error": "Cannot delete Global Community"}, 403
        
    try:
        execute("DELETE FROM chat_messages WHERE channel_id = %s", (channel_id,))
        execute("DELETE FROM dm_participants WHERE channel_id = %s", (channel_id,))
        execute("DELETE FROM chat_invitations WHERE target_channel_id = %s", (channel_id,))
        execute("DELETE FROM channels WHERE channel_id = %s", (channel_id,))
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500

@admin_bp.route("/admin/api/chat/wipe", methods=["POST"])
@admin_required
def admin_wipe_chats():
    """
    DANGER: Wipes all chat data except Global Community (ID 1).
    """
    from backend.repository.db_access import execute
    try:
        # 1. Delete messages from non-global channels
        execute("DELETE FROM chat_messages WHERE channel_id != 1")
        
        # 2. Delete invitations
        execute("DELETE FROM chat_invitations")
        
        # 3. Delete participants from non-global channels
        execute("DELETE FROM dm_participants WHERE channel_id != 1")
        
        # 4. Delete channels (except ID 1)
        execute("DELETE FROM channels WHERE channel_id != 1")
        
        # 5. Optionally clear logs if requested, but usually separate. 
        # User said "clean wipe all chat dataset and only keep global community"
        
        # Log this administrative action
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "WIPE_CHATS", "Administrator wiped all non-global chat data.")
        
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500




@admin_bp.route("/admin/system/health")
@admin_required
def admin_health_view():
    """Renders the System Health Monitoring page."""
    from backend.services.health_service import get_system_health, get_error_logs
    health_data = get_system_health()
    error_logs = get_error_logs()
    
    return render_template(
        "admin/health.html",
        active_page="admin_health",
        health=health_data,
        logs=error_logs
    )

# Legacy author/series routes removed to resolve duplicated endpoint conflict.
# Consolidated logic resides at the end of this file with AI background support.

@admin_bp.route("/admin/overdue-reminders", methods=["POST"])
@admin_required
def send_overdue_reminders_route():
    """Triggers mass email notifications for overdue books."""
    from backend.services.issue_service import send_overdue_reminders
    result = send_overdue_reminders()
    flash(result)
    return redirect("/reports")


# =====================================================
# REPORT EXPORTS (GET)
# =====================================================

@admin_bp.route("/reports/export/<report_type>")
@admin_required
def admin_export_report(report_type):
    """
    Triggers CSV export for a specific report.
    """
    from backend.services.report_service import (
        most_issued_books, most_active_users, 
        monthly_issue_count, export_report
    )

    if report_type == "most_issued":
        df = most_issued_books()
        filename = "most_issued_books"
    elif report_type == "active_users":
        df = most_active_users()
        filename = "active_users"
    elif report_type == "monthly":
        df = monthly_issue_count()
        filename = "monthly_issues"
    else:
        flash("❌ Invalid report type", "error")
        return redirect("/reports")

    result = export_report(df, filename)
    flash(result)
    return redirect("/reports")



# =====================================================
# ISSUE BOOK (POST)
# =====================================================

@admin_bp.route("/admin/issue", methods=["POST"])
@admin_required
def admin_issue_book():
    """
    Issues a book to a user.

    Triggered when admin submits:
    - Issue Book form

    URL:
        POST /admin/issue
    """

    # -------------------------------------------------
    # STEP 1: READ FORM DATA
    # -------------------------------------------------
    user_id = request.form.get("user_id")
    book_id = request.form.get("book_id")

    # -------------------------------------------------
    # STEP 2: VALIDATE INPUT
    # -------------------------------------------------
    if not user_id or not book_id:
        flash("❌ User ID and Book ID are required", "error")
        return redirect("/admin/issues")

    # -------------------------------------------------
    # STEP 3: SERVICE LAYER CALL
    # -------------------------------------------------
    try:
        # Convert inputs to integers (SAFE)
        uid = int(user_id)
        bid = int(book_id)

        # Business rules, limits, transactions are handled
        # inside issue_service.issue_book()
        result = issue_book(uid, bid)

    except ValueError:
        result = "❌ Invalid User ID or Book ID (Must be numeric)"

    # -------------------------------------------------
    # STEP 4: FEEDBACK + REDIRECT
    # -------------------------------------------------
    flash(result)
    return redirect("/admin/issues")


# =====================================================
# RETURN BOOK (POST)
# =====================================================

@admin_bp.route("/admin/return", methods=["POST"])
@admin_required
def admin_return_book():
    """
    Returns a previously issued book.

    Triggered when admin submits:
    - Return Book form

    URL:
        POST /admin/return
    """

    # -------------------------------------------------
    # STEP 1: READ FORM DATA
    # -------------------------------------------------
    user_id = request.form.get("user_id")
    book_id = request.form.get("book_id")

    # -------------------------------------------------
    # STEP 2: VALIDATE INPUT
    # -------------------------------------------------
    if not user_id or not book_id:
        flash("❌ User ID and Book ID are required", "error")
        return redirect("/admin/issues")

    # -------------------------------------------------
    # STEP 3: SERVICE LAYER CALL
    # -------------------------------------------------
    try:
        # Convert inputs to integers (SAFE)
        uid = int(user_id)
        bid = int(book_id)

        # Handles:
        # - Finding active issue
        # - Fine calculation
        # - Transaction safety
        result = return_book(uid, bid)

    except ValueError:
        result = "❌ Invalid User ID or Book ID (Must be numeric)"

    # -------------------------------------------------
    # STEP 4: FEEDBACK + REDIRECT
    # -------------------------------------------------
    flash(result)
    return redirect("/admin/issues")



@admin_bp.route("/admin/fine/pay/<int:issue_id>", methods=["POST"])
@admin_required
def admin_pay_fine_route(issue_id):
    """
    Marks a fine as paid.
    """
    from backend.services.issue_service import pay_fine
    result = pay_fine(issue_id)
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "PAY_FINE", f"Issue ID: {issue_id}")
    flash(result)
    return redirect("/admin/issues")


# =====================================================
# REQUEST MANAGEMENT (POST)
# =====================================================

@admin_bp.route("/admin/request/approve", methods=["POST"])
@admin_required
def approve_request_route():
    request_id = request.form.get("request_id")
    result = process_request(request_id, "approve")
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "APPROVE_REQUEST", f"Request ID: {request_id}")
    flash(result)
    return redirect("/admin/requests")

@admin_bp.route("/admin/request/reject", methods=["POST"])
@admin_required
def reject_request_route():
    request_id = request.form.get("request_id")
    result = process_request(request_id, "reject")
    flash(result)
    return redirect("/admin/requests")


# =====================================================
# USER MANAGEMENT (POST)
# =====================================================

@admin_bp.route("/admin/user/add", methods=["POST"])
@admin_required
def admin_add_user():
    """
    Creates a new user account.
    """
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    role = request.form.get("role")

    if not name or not email or not password or not role:
        flash("❌ All fields are required", "error")
        return redirect("/admin/users")

    result = add_user(name, email, role, password)
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "ADD_USER", f"Email: {email}")
    flash(result)
    return redirect("/admin/users")


@admin_bp.route("/admin/user/delete/<int:user_id>", methods=["POST"])
@admin_required
def admin_delete_user(user_id):
    """
    Deletes a user account.
    """
    from backend.services.user_service import delete_user
    
    # Prevent admin from deleting themselves
    if user_id == session.get("user_id"):
        flash("❌ You cannot delete your own admin account while logged in.", "error")
        return redirect("/admin/users")

    result = delete_user(user_id)
    if "✅" in result:
        from backend.services.audit_service import log_action
        log_action(session.get('user_id'), "DELETE_USER", f"Deleted User ID: {user_id}")
    flash(result)
    return redirect("/admin/users")


@admin_bp.route("/admin/audit-logs")
@admin_required
def admin_audit_logs_route():
    """Renders the Audit Logs page."""
    from backend.services.audit_service import get_audit_logs
    logs = get_audit_logs(100)
    return render_template("admin/audit_logs.html", active_page="admin_audit", logs=logs)


@admin_bp.route("/admin/scanner")
@admin_required
def admin_scanner_route():
    """Renders the QR/Barcode Scanner."""
    return render_template("admin/scanner.html", active_page="admin_scanner")


@admin_bp.route("/admin/support")
@admin_required
def admin_support_route():
    from backend.services.support_service import get_all_tickets
    tickets = get_all_tickets()
    return render_template("admin/support.html", active_page="admin_support", tickets=tickets)

@admin_bp.route("/admin/support/<int:ticket_id>", methods=["GET", "POST"])
@admin_required
def admin_ticket_view(ticket_id):
    from backend.services.support_service import get_ticket_details, add_reply, close_ticket
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "reply":
            msg = request.form.get("message")
            result = add_reply(ticket_id, session["user_id"], msg)
            flash(result)
        elif action == "close":
            result = close_ticket(ticket_id)
            flash(result)
        return redirect(f"/admin/support/{ticket_id}")
        
    data = get_ticket_details(ticket_id)
    return render_template("admin/ticket_view.html", active_page="admin_support", **data)


@admin_bp.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings_route():
    from backend.services.settings_service import (
        is_maintenance_mode, set_maintenance_mode, 
        get_category_fines, update_category_fine, delete_category_fine,
        get_all_settings, update_settings
    )
    
    if request.method == "POST":
        from backend.services.audit_service import log_action
        action = request.form.get("action")
        if action == "maintenance":
            status = request.form.get("maintenance_mode") == "true"
            result = set_maintenance_mode(status)
            log_action(session["user_id"], "SET_MAINTENANCE", f"Status: {status}")
            flash(result)
        elif action == "update_fine":
            cat = request.form.get("category")
            rate = request.form.get("rate")
            result = update_category_fine(cat, rate)
            log_action(session["user_id"], "UPDATE_FINE", f"Category: {cat}, Rate: {rate}")
            flash(result)
        elif action == "delete_fine":
            cat = request.form.get("category")
            result = delete_category_fine(cat)
            log_action(session["user_id"], "DELETE_FINE", f"Category: {cat}")
            flash(result)
        elif action == "update_general":
            # List of all possible keys to capture from form
            keys = [
                "library_name", "library_tagline", "branding_emoji", 
                "library_email", "library_phone", "library_address",
                "max_books_per_user", "default_issue_days", "max_renewals",
                "reservation_expiry_days", "max_pending_requests",
                "currency_symbol", "daily_fine_rate", "fine_grace_period", "fine_cap",
                "default_theme", "pagination_size", "show_cover_images",
                "sidebar_style", "accent_color", "registration_mode", "allow_suggestions"
            ]
            new_settings = {k: request.form.get(k) for k in keys if request.form.get(k) is not None}
            result = update_settings(new_settings)
            log_action(session["user_id"], "UPDATE_GENERAL_SETTINGS", "Updated comprehensive library config")
            flash(result)
        return redirect("/admin/settings")
        
    m_mode = is_maintenance_mode()
    fines = get_category_fines()
    all_settings = get_all_settings()
    return render_template("admin/settings.html", 
        active_page="admin_settings", 
        maintenance_mode=m_mode, 
        category_fines=fines,
        settings=all_settings
    )

@admin_bp.route("/admin/authors")
@admin_required
def admin_authors_view():
    """Renders the Authors Management page."""
    from backend.repository.db_access import fetch_all
    authors = fetch_all("SELECT * FROM authors ORDER BY name ASC")
    return render_template("admin/authors.html", active_page="admin_authors", authors=authors)

@admin_bp.route("/admin/authors/edit/<int:author_id>", methods=["POST"])
@admin_required
def admin_edit_author(author_id):
    """Updates author biography and metadata."""
    from backend.repository.db_access import execute
    bio = request.form.get("bio")
    nationality = request.form.get("nationality")
    execute("UPDATE authors SET bio = %s, nationality = %s WHERE author_id = %s", (bio, nationality, author_id))
    flash("✅ Author updated successfully")
    return redirect("/admin/authors")

@admin_bp.route("/admin/series")
@admin_required
def admin_series_view():
    """Renders the Series Management page."""
    from backend.services.author_service import get_all_series
    series_list = get_all_series()
    return render_template("admin/series.html", active_page="admin_series", series_list=series_list)

@admin_bp.route("/admin/series/<int:series_id>")
@admin_required
def admin_series_details(series_id):
    """View details and books within a specific series."""
    from backend.services.author_service import get_series_details, get_series_books
    series = get_series_details(series_id)
    books = get_series_books(series_id)
    return render_template("admin/series_details.html", active_page="admin_series", series=series, books=books)

@admin_bp.route("/admin/series/delete/<int:series_id>", methods=["POST"])
@admin_required
def admin_delete_series(series_id):
    """Deletes a series. Books are not deleted, just unlinked."""
    from backend.repository.db_access import execute
    try:
        # Unlink books first
        execute("UPDATE books SET series_id = NULL, series_order = NULL WHERE series_id = %s", (series_id,))
        # Delete series
        execute("DELETE FROM series WHERE series_id = %s", (series_id,))
        flash("✅ Series deleted successfully.")
    except Exception as e:
        flash(f"❌ Error deleting series: {e}", "error")
    return redirect("/admin/series")



@admin_bp.route("/admin/series/create", methods=["POST"])
@admin_required
def admin_create_series():
    """Manually creates a new series."""
    from backend.repository.db_access import execute
    name = request.form.get("name")
    description = request.form.get("description")
    
    if name:
        execute("INSERT INTO series (name, description) VALUES (%s, %s)", (name, description))
        flash("✅ Series created successfully!")
    else:
        flash("❌ Series name is required", "error")
    return redirect("/admin/series")

@admin_bp.route("/admin/series/add-book", methods=["POST"])
@admin_required
def admin_series_add_book():
    """Adds a book to a series manually."""
    from backend.repository.db_access import execute
    series_id = request.form.get("series_id")
    book_id = request.form.get("book_id")
    order = request.form.get("order")
    
    if series_id and book_id:
        execute("UPDATE books SET series_id = %s, series_order = %s WHERE book_id = %s", (series_id, order, book_id))
        flash("✅ Book added to series!")
    else:
        flash("❌ Invalid selection", "error")
    return redirect(f"/admin/series/{series_id}")

@admin_bp.route("/admin/series/rename", methods=["POST"])
@admin_required
def admin_rename_series():
    """Renames an existing series."""
    from backend.repository.db_access import execute
    series_id = request.form.get("series_id")
    new_name = request.form.get("new_name")
    
    if series_id and new_name:
        execute("UPDATE series SET name = %s WHERE series_id = %s", (new_name, series_id))
        flash("✅ Series renamed successfully.")
    else:
        flash("❌ Missing data", "error")
    return redirect("/admin/books")

@admin_bp.route("/api/books/search")
@admin_required
def api_search_books():
    """JSON API to search books for manual linking."""
    from backend.repository.db_access import fetch_all
    q = request.args.get('q', '')
    if len(q) < 2: return jsonify([])
    
    books = fetch_all("SELECT book_id, title FROM books WHERE title LIKE %s LIMIT 10", (f"%{q}%",))
    return jsonify(books)

@admin_bp.route("/api/series/<int:series_id>/books")
@admin_required
def api_get_series_books(series_id):
    """JSON API to get books in a series."""
    from flask import jsonify
    from backend.services.author_service import get_series_books
    books = get_series_books(series_id)
    return jsonify(books)


@admin_bp.route("/api/admin/settings/ai-suggest", methods=["POST"])
@admin_required
def admin_settings_ai_suggest():
    """Returns AI-suggested settings based on description."""
    from flask import jsonify
    data = request.get_json()
    description = data.get("description", "")
    if not description:
        return jsonify({"error": "Please provide a description."}), 400
        
    from backend.services.ai_service import suggest_settings
    suggestions = suggest_settings(description)
    return jsonify(suggestions)


# =====================================================
# API: GET BORROWED BOOKS FOR A USER
# =====================================================

@admin_bp.route("/api/user/<int:user_id>/borrowed-books")
@admin_required
def api_get_user_borrowed_books(user_id):
    """
    Returns a JSON list of books currently borrowed by a specific user.
    Used for dynamic filtering in Return Book form.
    """
    from flask import jsonify
    
    borrowed_books = fetch_all(
        """
        SELECT b.book_id, b.title
        FROM issues i
        JOIN books b ON i.book_id = b.book_id
        WHERE i.user_id = %s AND i.return_date IS NULL
        ORDER BY b.title
        """,
        (user_id,)
    )
    
    return jsonify(borrowed_books)
