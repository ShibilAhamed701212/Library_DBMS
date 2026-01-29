"""
user.py
--------
Domain model for User.

Purpose:
- Represents a user entity in the system
- Pure data structure (NO database logic)
- Used across authentication, services, and analytics
"""

# ===============================
# IMPORTS
# ===============================

# dataclass removes boilerplate by auto-generating:
# __init__, __repr__, __eq__, etc.
from dataclasses import dataclass

# datetime is used to store user creation timestamp
from datetime import datetime


# ===============================
# DOMAIN MODEL
# ===============================

@dataclass
class User:
    """
    User domain object.

    This class represents one user record from the `users` table.
    It is a clean, structured representation of user data.

    This class:
    - Does NOT handle login
    - Does NOT hash passwords
    - Does NOT access the database
    - Only holds user-related data
    """

    # Unique identifier for the user (Primary Key)
    user_id: int

    # Full name of the user
    name: str

    # Email address (used for login & identification)
    email: str

    # Role of the user (e.g., "admin", "member")
    role: str

    # Flag to enforce password change on first login
    must_change_password: bool

    # Timestamp when the user account was created
    created_at: datetime
