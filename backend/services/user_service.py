"""
user_service.py
----------------
Handles user-related operations:
- add user
- view users
- delete user
- role checks
"""

from backend.repository.db_access import fetch_all, fetch_one, execute
from backend.utils.security import hash_password


def add_user(name: str, email: str, role: str, password: str = "Lib@123"):
    """
    Adds a new user to the system.
    Default password is forced to be changed on first login.
    """

    # Check if user already exists
    existing_user = fetch_one(
        "SELECT user_id FROM users WHERE email = %s",
        (email,)
    )

    if existing_user:
        return "❌ User with this email already exists"

    # Hash password securely
    password_hash = hash_password(password)

    # Insert user record
    execute(
        """
        INSERT INTO users
            (name, email, password_hash, role, must_change_password)
        VALUES
            (%s, %s, %s, %s, TRUE)
        """,
        (name, email, password_hash, role)
    )

    return "✅ User added successfully"


def view_users():
    """
    Returns a list of all users (admin use).
    """

    return fetch_all(
        """
        SELECT
            user_id,
            name,
            email,
            role,
            created_at
        FROM users
        ORDER BY user_id ASC
        """
    )


def delete_user(user_id: int):
    """
    Deletes a user by ID.
    """

    affected = execute(
        "DELETE FROM users WHERE user_id = %s",
        (user_id,)
    )

    if affected == 0:
        return "❌ User not found"

    return "🗑️ User deleted successfully"


def is_admin(user_id: int) -> bool:
    """
    Checks if a given user is an admin.
    """

    user = fetch_one(
        "SELECT role FROM users WHERE user_id = %s",
        (user_id,)
    )

    return bool(user and user["role"] == "admin")
