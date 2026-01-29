"""
db.py
------
This file is responsible ONLY for creating database connections.

Important design rules for this file:
- ❌ No SQL queries
- ❌ No business logic
- ❌ No application logic
- ✅ Only database connection creation

This keeps the project clean and modular.
"""

# ===============================
# IMPORTS
# ===============================

import os                    # Used to read environment variables
import mysql.connector       # MySQL database connector library
from dotenv import load_dotenv  # Loads variables from .env file

# ===============================
# LOAD ENVIRONMENT VARIABLES
# ===============================

# This reads the .env file and loads all key-value pairs
# into the system environment so os.getenv() can access them
load_dotenv()

# ===============================
# DATABASE CONNECTION FACTORY
# ===============================

def get_connection():
    """
    Creates and returns a MySQL database connection object.

    Purpose:
    - Central place to configure DB connection
    - Used by repository layer (db_access.py)
    - Ensures consistent DB access across the application

    Returns:
        mysql.connector.connection.MySQLConnection
    """

    # Create and return a MySQL connection using environment variables
    return mysql.connector.connect(

        # Database server address
        host=os.getenv("DB_HOST", "127.0.0.1"),

        # Database server port (default MySQL port = 3306)
        port=int(os.getenv("DB_PORT", 3306)),

        # Database username
        user=os.getenv("DB_USER", "app_user"),

        # Database password
        password=os.getenv("DB_PASSWORD", "App@123"),

        # Database name to connect to
        database=os.getenv("DB_NAME", "library_db"),

        # Disable autocommit to allow manual commit/rollback
        # This is critical for transactional safety
        autocommit=False,

        # Character set to support full Unicode (emojis, symbols, etc.)
        charset="utf8mb4",

        # REQUIRED FOR CLOUD (AIVEN):
        # Aiven and other cloud providers require SSL.
        # We enable it only if the host is NOT localhost.
        ssl_disabled=False if os.getenv("DB_HOST", "127.0.0.1") != "127.0.0.1" else True,

        # Authentication plugin used by MySQL
        # Required for compatibility with MySQL 8+
        auth_plugin="mysql_native_password"
    )
