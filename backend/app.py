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
from backend.routes.system_routes import system_bp  # Cloud initialization

# Import test routes (for debugging)
from backend.routes.test_auth import test_auth_bp   # Test authentication routes

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
    
    # Initialize SocketIO
    from backend import socketio
    socketio.init_app(app, async_mode='threading')
    
    # Register Socket Events
    import backend.socket_events
    import backend.chat.socket_service # Load Chat Handlers



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

    # Register main application blueprints
    app.register_blueprint(auth_bp)     # /
    app.register_blueprint(admin_bp)    # /dashboard
    app.register_blueprint(member_bp)   # /member/dashboard
    app.register_blueprint(system_bp)   # /system
    
    from backend.routes.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/chat')
    
    from backend.routes.analytics_routes import analytics_bp
    app.register_blueprint(analytics_bp) # /admin/analytics
    
    # Register test blueprints (for debugging)
    # Register test blueprints (for debugging)
    app.register_blueprint(test_auth_bp, url_prefix='/test')  # /test/auth/...

    from backend.routes.common_routes import common_bp
    app.register_blueprint(common_bp)

    # Context Processor for Notifications
    from flask import session
    # Context Processor for Notifications & Settings
    from flask import session
    @app.context_processor
    def inject_global_data():
        data = {
            'unread_notifications': [],
            'unread_count': 0,
            'system_settings': {
                'library_name': 'LibManage',
                'library_tagline': 'Professional Library Management System',
                'branding_emoji': '📚',
                'currency_symbol': '₹',
                'library_email': 'support@libmanage.com',
                'library_phone': '+91 98765 43210',
                'library_address': 'Central Library, MG Road, Tech City',
                'max_books_per_user': '3',
                'default_issue_days': '14',
                'max_renewals': '2',
                'reservation_expiry_days': '3',
                'max_pending_requests': '5',
                'daily_fine_rate': '5',
                'fine_grace_period': '0',
                'fine_cap': '500',
                'default_theme': 'auto',
                'pagination_size': '12',
                'show_cover_images': 'true',
                'sidebar_style': 'full',
                'accent_color': '#4e73df',
                'registration_mode': 'open',
                'allow_suggestions': 'true'
            }
        }
        
        # Inject Notifications
        if 'user_id' in session:
            try:
                from backend.services.notification_service import get_unread_notifications
                notifs = get_unread_notifications(session['user_id'])
                data['unread_notifications'] = notifs
                data['unread_count'] = len(notifs)
            except:
                pass
        
        # Inject Settings
        try:
            from backend.services.settings_service import get_all_settings
            settings = get_all_settings()
            if settings:
                data['system_settings'].update(settings)
        except:
            pass
            
        return data

    # Maintenance Mode Hook
    from flask import request, render_template
    from backend.services.settings_service import is_maintenance_mode

    @app.before_request
    def check_maintenance():
        # Exclude static files, auth routes, and system setup
        if request.path.startswith('/static') or \
           request.path.startswith('/auth') or \
           request.path == '/' or \
           request.path.startswith('/admin') or \
           request.path.startswith('/api/book') or \
           request.path.startswith('/system'):
            return None

        # Check maintenance status
        if is_maintenance_mode():
            # If logged in as admin, allow through
            if session.get('role') == 'admin':
                return None
            
            # Everyone else gets maintenance page
            return render_template("maintenance.html"), 503

    # -------------------------------
    # RETURN CONFIGURED APP
    # -------------------------------
    return app
