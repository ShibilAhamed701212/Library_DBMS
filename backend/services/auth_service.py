"""
auth_service.py
----------------
Handles authentication logic.

Responsibilities:
- Validate user credentials
- Verify hashed passwords
- Return user details for session creation

This module:
- Contains NO Flask code
- Contains NO session handling
- Contains NO database connection logic
"""

# ===============================
# IMPORTS
# ===============================

from backend.repository.db_access import fetch_one
# fetch_one → retrieves a single record from the database (SELECT ... LIMIT 1)

from backend.utils.security import verify_password
# verify_password → compares plaintext password with hashed password (bcrypt)


# ===============================
# AUTHENTICATION FUNCTION
# ===============================

def authenticate_user(email: str, password: str):
    """
    Validates user credentials.

    Args:
        email (str): User email entered during login
        password (str): Plain-text password entered during login

    Returns:
        dict → user data if credentials are valid
        None → if authentication fails
    """

    # -----------------------------
    # BASIC INPUT VALIDATION
    # -----------------------------

    # Reject empty email or password
    if not email or not password:
        return None

    # -----------------------------
    # FETCH USER FROM DATABASE
    # -----------------------------

    # Query database for user record using email
    user = fetch_one(
        """
        SELECT
            user_id,               -- Unique user identifier
            name,                  -- Full name
            email,                 -- Email address
            password_hash,         -- Hashed password (bcrypt)
            role,                  -- User role (admin / member)
            must_change_password,   -- Flag for first-login password change
            profile_pic,
            bio
        FROM users
        WHERE email = %s
        """,
        (email,)
    )

    # -----------------------------
    # USER EXISTENCE CHECK
    # -----------------------------

    # If no user found with given email
    if not user:
        return None

    # -----------------------------
    # PASSWORD VERIFICATION
    # -----------------------------

    # Compare entered password with stored hashed password
    if not verify_password(password, user["password_hash"]):
        return None

    # -----------------------------
    # AUTHENTICATION SUCCESS
    # -----------------------------

    # Return user data for session creation
    return user

def get_user_by_id(user_id):
    """Fetch user details by ID."""
    return fetch_one(
        "SELECT user_id, name, email, role, profile_pic, bio FROM users WHERE user_id = %s",
        (user_id,)
    )
