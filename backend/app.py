# backend/app.py
# ----------------
# Flask application factory.
# Responsible for:
# - Creating the Flask app instance
# - Configuring templates & static paths
# - Loading environment variables
# - Registering all route blueprints
#
# This file does NOT contain business logic.
# This file does NOT contain database code.
# This file is the central app bootstrap.

import os                          # Used for filesystem path operations
from flask import Flask            # Core Flask class
from dotenv import load_dotenv     # Loads environment variables from .env file

# -------------------------------
# IMPORT BLUEPRINTS (ROUTES)
# -------------------------------
# Each blueprint handles a separate domain of the app

from backend.routes.auth_routes import auth_bp      # Login, logout, password change
from backend.routes.admin_routes import admin_bp    # Admin dashboard & admin actions
from backend.routes.member_routes import member_bp  # Member dashboard

# -------------------------------
# LOAD ENVIRONMENT VARIABLES
# -------------------------------
# Reads values from .env into os.environ
# Example: FLASK_SECRET_KEY
load_dotenv()


def create_app():
    """
    Application factory function.

    Purpose:
    - Creates and configures the Flask app
    - Allows scalability (testing, prod, dev configs)
    - Industry-standard Flask pattern

    Returns:
        Flask app instance
    """

    # -------------------------------
    # BASE DIRECTORY RESOLUTION
    # -------------------------------
    # Computes project root directory
    # backend/app.py → ../ (project root)
    BASE_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    # -------------------------------
    # FLASK APP INITIALIZATION
    # -------------------------------
    # Explicitly define:
    # - template folder (HTML files)
    # - static folder (CSS, JS, images)
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )

    # -------------------------------
    # SECURITY CONFIGURATION
    # -------------------------------
    # Secret key used for:
    # - Sessions
    # - Flash messages
    # - CSRF protection (if enabled)
    #
    # Pulled from environment for security
    app.secret_key = os.getenv(
        "FLASK_SECRET_KEY",
        "dev-secret"   # fallback ONLY for development
    )

    # -------------------------------
    # REGISTER BLUEPRINTS
    # -------------------------------
    # Connects route modules to the app
    # Keeps routes modular and clean

    app.register_blueprint(auth_bp)     # /
    app.register_blueprint(admin_bp)    # /dashboard
    app.register_blueprint(member_bp)   # /member/dashboard

    # -------------------------------
    # RETURN CONFIGURED APP
    # -------------------------------
    return app
