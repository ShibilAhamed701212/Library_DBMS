"""
auth_routes.py
--------------
Handles authentication-related routes (session-based).

Responsibilities:
- Login (session-based)
- Logout
- Forced password change
- Role-based redirection (admin / member)
"""

# ===============================
# IMPORTS
# ===============================

from flask import Blueprint, render_template, request, redirect, session, flash
# Blueprint      → groups auth routes
# render_template→ renders HTML pages
# request        → reads form data (email/password)
# redirect       → redirects users after actions
# session        → stores logged-in user state
# flash          → shows temporary messages in UI

from backend.services.auth_service import authenticate_user
# authenticate_user → verifies email & password against DB

from backend.utils.decorators import login_required
# login_required → ensures user is logged in before accessing route

from backend.utils.security import hash_password
# hash_password → securely hashes passwords (bcrypt)

from backend.repository.db_access import execute
# execute → runs INSERT / UPDATE / DELETE queries


# ===============================
# BLUEPRINT SETUP
# ===============================

# Create authentication blueprint
auth_bp = Blueprint("auth", __name__)


# =====================================================
# LOGIN ROUTE
# =====================================================

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    """
    Login page handler.

    GET  → shows login page
    POST → validates credentials and creates session
    """

    # Debug: log request method
    print("🔥 LOGIN ROUTE HIT, METHOD =", request.method)

    # -----------------------------
    # HANDLE LOGIN SUBMISSION
    # -----------------------------
    if request.method == "POST":

        # Debug: print submitted form data
        print("🔥 POST DATA:", request.form)

        # Read email & password from login form
        email = request.form.get("email")
        password = request.form.get("password")

        # Debug: log email being processed
        print("🔥 EMAIL =", email)

        # Authenticate user credentials
        user = authenticate_user(email, password)

        # If authentication fails
        if not user:
            flash("❌ Invalid email or password", "error")
            return render_template("login.html")

        # -----------------------------
        # CREATE USER SESSION
        # -----------------------------

        # Clear any existing session data
        session.clear()

        # Store user identity in session
        session["user_id"] = user["user_id"]
        session["role"] = user["role"]
        session["name"] = user["name"]  # Store name for Dashboard Header

        # -----------------------------
        # FORCE PASSWORD CHANGE
        # -----------------------------

        # If user is logging in with default password
        if user.get("must_change_password"):
            return redirect("/change-password")

        # -----------------------------
        # ROLE-BASED REDIRECTION
        # -----------------------------

        # Admin users → admin dashboard
        if user["role"] == "admin":
            return redirect("/dashboard")

        # Member users → member dashboard
        else:
            return redirect("/member/dashboard")

    # -----------------------------
    # SHOW LOGIN PAGE (GET)
    # -----------------------------
    return render_template("login.html")


# =====================================================
# LOGOUT ROUTE
# =====================================================

@auth_bp.route("/logout")
def logout():
    """
    Logs user out by clearing session.
    """

    # Remove all session data
    session.clear()

    # Inform user
    flash("ℹ️ Logged out successfully", "info")

    # Redirect to login page
    return redirect("/")


# =====================================================
# CHANGE PASSWORD ROUTE
# =====================================================

@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Forces user to change password on first login.

    Accessible only if user is logged in.
    """

    # -----------------------------
    # HANDLE PASSWORD UPDATE
    # -----------------------------
    if request.method == "POST":

        # Read new password fields
        new_password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validate empty fields
        if not new_password or not confirm_password:
            flash("❌ All fields are required", "error")
            return redirect("/change-password")

        # Validate password match
        if new_password != confirm_password:
            flash("❌ Passwords do not match", "error")
            return redirect("/change-password")

        # Validate minimum length
        if len(new_password) < 8:
            flash("❌ Password must be at least 8 characters", "error")
            return redirect("/change-password")

        # -----------------------------
        # HASH PASSWORD
        # -----------------------------

        # Securely hash password using bcrypt
        password_hash = hash_password(new_password)

        # -----------------------------
        # UPDATE PASSWORD IN DATABASE
        # -----------------------------

        execute(
            """
            UPDATE users
            SET password_hash = %s,
                must_change_password = FALSE
            WHERE user_id = %s
            """,
            (password_hash, session["user_id"])
        )

        # Notify user
        flash("✅ Password updated successfully", "success")

        # -----------------------------
        # REDIRECT BASED ON ROLE
        # -----------------------------

        # Admin → admin dashboard
        if session.get("role") == "admin":
            return redirect("/dashboard")

        # Member → member dashboard
        else:
            return redirect("/member/dashboard")

    # -----------------------------
    # SHOW CHANGE PASSWORD PAGE
    # -----------------------------
    return render_template("change_password.html", active_page="settings")
