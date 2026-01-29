# ===============================
# IMPORTS
# ===============================

from flask import Blueprint, render_template, session
# Blueprint        → groups member-related routes
# render_template → renders HTML templates
# session         → accesses logged-in user session data

from backend.repository.db_access import fetch_all
# fetch_all → executes SELECT queries and returns multiple rows

from backend.utils.decorators import member_required
# member_required → ensures only logged-in members can access this route


# ===============================
# BLUEPRINT SETUP
# ===============================

# Create a Blueprint for member-related routes
member_bp = Blueprint("member", __name__)


# ===============================
# MEMBER DASHBOARD ROUTE
# ===============================

# ===============================
# MEMBER DASHBOARD (GET)
# ===============================

@member_bp.route("/member/dashboard")
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

    return render_template(
        "member/overview.html",
        active_page="member_overview",
        issues=issues
    )


# ===============================
# BOOK CATALOG (GET)
# ===============================

@member_bp.route("/member/catalog")
@member_required
def member_catalog_view():
    """
    Renders the searchable Book Catalog with server-side pagination.
    """
    from flask import request
    from backend.services.book_service import view_books_paginated
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    per_page = 12  # Grid looks better with 12 items
    
    pagination = view_books_paginated(page, per_page, search_query)

    return render_template(
        "member/catalog.html",
        active_page="member_catalog",
        books=pagination['books'],
        total=pagination['total'],
        current_page=pagination['page'],
        total_pages=pagination['total_pages'],
        q=search_query
    )


# ===============================
# REQUEST BOOK (POST)
# ===============================

@member_bp.route("/member/request", methods=["POST"])
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

