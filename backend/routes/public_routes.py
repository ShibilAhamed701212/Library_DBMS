"""
public_routes.py
----------------
Handles public-facing routes accessible WITHOUT login.

Responsibilities:
- Public landing page with book catalog
- Account request submission with OTP email verification
"""

import re
import hmac
import hashlib
import secrets
import threading
import time
from flask import Blueprint, render_template, request, redirect, flash, session, current_app
from backend.repository.db_access import execute_query, fetch_all, fetch_one

public_bp = Blueprint("public", __name__)


# =====================================================
# ENSURE TABLES
# =====================================================

def ensure_account_requests_table():
    """Create the account_requests table if it doesn't exist."""
    try:
        execute_query("""
            CREATE TABLE IF NOT EXISTS account_requests (
                request_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL,
                reason TEXT,
                status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    except Exception:
        pass


# =====================================================
# OTP HELPERS
# =====================================================
# The Flask session is a signed but readable cookie, so the OTP itself is
# never stored in it: only an HMAC keyed with the app secret, which the
# client cannot reverse. Failed attempts are counted server-side per email
# because a client could replay an older cookie to reset a cookie counter.

OTP_TTL_SECONDS = 10 * 60
OTP_MAX_ATTEMPTS = 5
_otp_failures = {}
_otp_failures_lock = threading.Lock()


def _otp_digest(email, otp):
    key = current_app.secret_key
    if isinstance(key, str):
        key = key.encode()
    return hmac.new(key, f"{email}:{otp}".encode(), hashlib.sha256).hexdigest()


def _otp_failure_count(email):
    with _otp_failures_lock:
        return _otp_failures.get(email, 0)


def _record_otp_failure(email):
    with _otp_failures_lock:
        _otp_failures[email] = _otp_failures.get(email, 0) + 1


def _clear_otp_failures(email):
    with _otp_failures_lock:
        _otp_failures.pop(email, None)


def _clear_signup_session():
    for k in ('signup_otp_hash', 'signup_otp_expires', 'signup_name', 'signup_email', 'signup_reason'):
        session.pop(k, None)


# =====================================================
# PUBLIC LANDING PAGE
# =====================================================

@public_bp.route("/")
def landing():
    """Public landing page showing the book catalog."""
    # If user is already logged in, redirect to dashboard
    if session.get("user_id"):
        if session.get("role") == "admin":
            return redirect("/dashboard")
        return redirect("/member/dashboard")

    # Fetch books for public display
    books = fetch_all("""
        SELECT b.book_id, b.title, b.author AS author_name, b.category,
               b.total_copies, b.available_copies
        FROM books b
        ORDER BY b.title ASC
        LIMIT 50
    """) or []

    # Fetch system settings for branding
    try:
        settings = fetch_one("SELECT * FROM system_settings LIMIT 1")
    except Exception:
        settings = None

    return render_template(
        "public_landing.html",
        books=books,
        system_settings=settings,
        total=len(books)
    )


# =====================================================
# ACCOUNT REQUEST — STEP 1: Send OTP
# =====================================================

@public_bp.route("/request-account", methods=["POST"])
def request_account():
    """Step 1: Validate email and send OTP verification code."""
    ensure_account_requests_table()

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    reason = request.form.get("reason", "").strip()

    if not name or not email:
        flash("Please provide your name and email.", "error")
        return redirect("/login")

    # Validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        flash("Please enter a valid email address.", "error")
        return redirect("/login")

    # Check if the email domain exists (has MX records)
    try:
        import dns.resolver
        domain = email.split('@')[1]
        dns.resolver.resolve(domain, 'MX')
    except Exception:
        flash("This email domain does not exist. Please use a valid email address.", "error")
        return redirect("/login")

    # Check if email already has an account
    existing_user = fetch_one("SELECT user_id FROM users WHERE email = %s", (email,))
    if existing_user:
        flash("An account with this email already exists. Please login.", "error")
        return redirect("/login")

    # Check for duplicate pending request
    existing_req = fetch_one(
        "SELECT request_id FROM account_requests WHERE email = %s AND status = 'pending'",
        (email,)
    )
    if existing_req:
        flash("You already have a pending account request. Please wait for admin approval.", "error")
        return redirect("/login")

    # Generate 6-digit OTP
    otp = f"{secrets.randbelow(1000000):06d}"

    # Store only a keyed hash of the OTP in the (client-readable) session
    _clear_otp_failures(email)
    session['signup_otp_hash'] = _otp_digest(email, otp)
    session['signup_otp_expires'] = int(time.time()) + OTP_TTL_SECONDS
    session['signup_name'] = name
    session['signup_email'] = email
    session['signup_reason'] = reason

    # Send OTP via email
    try:
        from backend.services.email_service import send_email
        subject = "🔐 Verify Your Email — Library Account Request"
        body = f"""Hi {name},

You requested an account at the library. Please use the verification code below to confirm your email:

━━━━━━━━━━━━━━━━━━━━━━━━
📧 Your OTP Code: {otp}
━━━━━━━━━━━━━━━━━━━━━━━━

This code expires in 10 minutes.

If you did not request this, please ignore this email.

Best regards,
Library Management Team
"""
        sent = send_email(email, subject, body)
        if not sent:
            flash("Could not send verification email. Please try again.", "error")
            return redirect("/login")
    except Exception as e:
        print(f"❌ OTP email error: {e}")
        flash("Could not send verification email. Please try again.", "error")
        return redirect("/login")

    flash(f"📧 A verification code has been sent to {email}. Please check your inbox.", "success")
    return redirect("/verify-email")


# =====================================================
# ACCOUNT REQUEST — STEP 2: Verify OTP
# =====================================================

@public_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    """Step 2: Show OTP form and verify the code."""
    # Check session has pending signup
    if 'signup_otp_hash' not in session or 'signup_email' not in session:
        flash("No pending verification. Please submit your request first.", "error")
        return redirect("/login")

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        email = session['signup_email']

        if time.time() > session.get('signup_otp_expires', 0) or \
                _otp_failure_count(email) >= OTP_MAX_ATTEMPTS:
            _clear_signup_session()
            flash("Your verification code has expired. Please submit your request again.", "error")
            return redirect("/login")

        if hmac.compare_digest(_otp_digest(email, entered_otp), session['signup_otp_hash']):
            # OTP correct — create the account request
            ensure_account_requests_table()
            name = session.get('signup_name')
            reason = session.get('signup_reason', '')
            _clear_signup_session()
            # Burn this code so a replayed cookie cannot submit it again.
            with _otp_failures_lock:
                _otp_failures[email] = OTP_MAX_ATTEMPTS

            execute_query(
                "INSERT INTO account_requests (name, email, reason) VALUES (%s, %s, %s)",
                (name, email, reason)
            )

            flash("✅ Email verified! Your account request has been submitted. You'll receive your credentials once approved.", "success")
            return redirect("/login")
        else:
            _record_otp_failure(email)
            flash("❌ Invalid verification code. Please try again.", "error")
            return redirect("/verify-email")

    # GET — show the verification page
    return render_template("verify_email.html", email=session.get('signup_email', ''))
