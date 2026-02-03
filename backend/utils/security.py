"""
security.py
------------
Handles password hashing and verification.
Centralising this avoids bugs and inconsistencies.
"""

import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Hashes a plain-text password using bcrypt.

    Why bcrypt?
    - Salted automatically
    - Slow by design (prevents brute-force attacks)
    - Industry standard
    """

    # Convert string password to bytes (bcrypt requires bytes)
    password_bytes = plain_password.encode("utf-8")

    # Generate salt with cost factor 12 (secure & performant)
    salt = bcrypt.gensalt(rounds=12)

    # Hash password + salt
    hashed_password = bcrypt.hashpw(password_bytes, salt)

    # Return UTF-8 string representation suitable for VARCHAR storage
    return hashed_password.decode("utf-8")


def verify_password(plain_password: str, hashed_password) -> bool:
    """
    Verifies a plain password against a stored bcrypt hash.
    """

    # Convert plain password to bytes
    password_bytes = plain_password.encode("utf-8")

    # Support both str and bytes for the stored hash
    if isinstance(hashed_password, str):
        hashed_bytes = hashed_password.encode("utf-8")
    else:
        hashed_bytes = hashed_password

    try:
        # bcrypt safely checks hash
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        # Covers corrupted hashes or invalid formats
        return False
