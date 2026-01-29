"""
run.py
------
Application entry point.

Purpose:
- This file is the MAIN executable for the Flask web application.
- It is the file you run using: `python run.py`
- It creates the Flask app and starts the development server.

IMPORTANT:
- No business logic should exist here.
- No routes should be defined here.
- This file ONLY boots the application.
"""

# Import the application factory function
# This function builds and configures the Flask app
from backend.app import create_app

0
# Call the factory to create a Flask application instance
# This sets up:
# - Flask object
# - Config (secret key, env vars)
# - Template & static folders
# - Registered blueprints (auth, admin, member)
app = create_app()


# Python entry-point guard
# This ensures the server starts ONLY when this file is executed directly
# and NOT when it is imported by another module (best practice)
if __name__ == "__main__":

    # Start the Flask development server
    # debug=True enables:
    # - Auto-reload on code changes
    # - Detailed error tracebacks
    # - Debugger PIN (development only)
    #
    # ⚠️ NEVER use debug=True in production
    app.run(debug=True)
