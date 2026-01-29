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
    """Renders the Admin Overview with statistics."""
    total_users = fetch_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_books = fetch_one("SELECT COUNT(*) AS c FROM books")["c"]
    total_issues = fetch_one("SELECT COUNT(*) AS c FROM issues WHERE return_date IS NULL")["c"]

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
        total_users=total_users,
        total_books=total_books,
        total_issues=total_issues,
        recent_issues=recent_issues
    )


# =====================================================
# BOOK MANAGEMENT (GET)
# =====================================================

@admin_bp.route("/admin/books")
@admin_required
def admin_books_view():
    """Renders the Books Management page with pagination."""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '')
    
    pagination = view_books_paginated(page, 10, search_query)
    
    return render_template(
        "admin/books.html",
        active_page="admin_books",
        books=pagination['books'],
        total=pagination['total'],
        current_page=pagination['page'],
        total_pages=pagination['total_pages'],
        q=search_query
    )


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
        SELECT i.issue_id, u.name AS user_name, b.title AS book_title, i.issue_date, i.return_date, i.fine
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
# REPORTS & ANALYTICS (GET)
# =====================================================

@admin_bp.route("/reports")
@admin_required
def admin_reports():
    """
    Renders the Library Analytics page.
    """
    from collections import namedtuple
    ReportData = namedtuple('ReportData', ['most_issued', 'active_users', 'monthly', 'categories'])
    
    data = ReportData(
        most_issued=most_issued_books(),
        active_users=most_active_users(),
        monthly=monthly_issue_count(),
        categories=book_category_distribution()
    )

    return render_template(
        "reports.html",
        active_page="admin_reports",
        data=data
    )


@admin_bp.route("/admin/notify-overdue", methods=["POST"])
@admin_required
def send_overdue_reminders_route():
    """Triggers mass email notifications for overdue books."""
    from flask import flash
    result = send_overdue_reminders()
    flash(result, "success")
    return redirect(url_for("admin.admin_reports"))


# =====================================================
# REPORT EXPORTS (GET)
# =====================================================

@admin_bp.route("/reports/export/<report_type>")
@admin_required
def admin_export_report(report_type):
    """
    Triggers CSV export for a specific report.
    """
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


# =====================================================
# REQUEST MANAGEMENT (POST)
# =====================================================

@admin_bp.route("/admin/request/approve", methods=["POST"])
@admin_required
def approve_request_route():
    request_id = request.form.get("request_id")
    result = process_request(request_id, "approve")
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
    flash(result)
    return redirect("/admin/users")

