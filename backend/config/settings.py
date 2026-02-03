"""
settings.py
------------
Centralised application configuration file.

Purpose:
- Load environment variables once
- Expose clean Python constants
- Avoid calling os.getenv() everywhere
- Keep configuration separate from logic

This file is imported wherever configuration is needed.
"""

# ===============================
# IMPORTS
# ===============================

import os                      # Used to read environment variables
from dotenv import load_dotenv  # Loads variables from .env file into environment

# ===============================
# LOAD ENV FILE
# ===============================

# Reads the .env file and makes variables available via os.getenv()
# This should be done ONCE at application startup
load_dotenv()

# ===============================
# DATABASE SETTINGS
# ===============================

# Database host (IP or hostname)
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")

# Database port (converted to int because env vars are strings)
DB_PORT = int(os.getenv("DB_PORT", 3306))

# Database name
DB_NAME = os.getenv("DB_NAME", "library_db")

# Database username
DB_USER = os.getenv("DB_USER", "app_user")

# Database password
# WARNING: Default password is for development only.
# Always set DB_PASSWORD in production via environment variables.
DB_PASSWORD = os.getenv("DB_PASSWORD", "App@123")

# ===============================
# FLASK SETTINGS
# ===============================

# Secret key used by Flask for:
# - Sessions
# - Flash messages
# - CSRF protection (if enabled)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret")

# ===============================
# BUSINESS RULES (CENTRALISED)
# ===============================

# Maximum number of books a user can issue at once
MAX_BOOKS_PER_USER = 3

# Maximum number of days a book can be kept without fine
MAX_DAYS_ALLOWED = 7

# Fine charged per extra day (currency unit decided by system)
FINE_PER_DAY = 5
