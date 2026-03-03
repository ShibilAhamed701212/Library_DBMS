# =========================================================
# PythonAnywhere WSGI File
# =========================================================
# This file is what PythonAnywhere uses to load your application.
# It replaces run.py in production.

import sys
import os

# 1. Provide the absolute path to your project folder
# Replace 'yourusername' with your actual PythonAnywhere username!
project_home = '/home/yourusername/LDBMS/pythonProject'

if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# 2. Load environment variables (PythonAnywhere doesn't load .env automatically)
from dotenv import load_dotenv
env_path = os.path.join(project_home, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

# 3. Import the Flask app object
from backend.app import create_app

# 4. pythonanywhere looks for an object called "application"
application = create_app()

# Start the background scheduler if needed (Warning: PA limits background tasks in free tier)
try:
    from backend.scheduler import start_scheduler
    start_scheduler()
except Exception as e:
    print(f"Skipping scheduler in WSGI: {e}")
