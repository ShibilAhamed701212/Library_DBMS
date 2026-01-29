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

    # Base configuration
    config = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "app_user"),
        "password": os.getenv("DB_PASSWORD", "App@123"),
        "database": os.getenv("DB_NAME", "library_db"),
        "autocommit": False,
        "charset": "utf8mb4",
        "auth_plugin": "mysql_native_password"
    }

    # REQUIRED FOR CLOUD (AIVEN):
    # Only enable SSL parameters if we are NOT on localhost
    if config["host"] != "127.0.0.1":
        config["ssl_disabled"] = False
    
    # Create and return a MySQL connection
    return mysql.connector.connect(**config)
