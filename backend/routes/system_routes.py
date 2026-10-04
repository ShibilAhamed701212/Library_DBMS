from flask import Blueprint, request, current_app, abort
import hmac
import os
from database.init_db import run_schema
from database.seed_data import main as run_seed

system_bp = Blueprint('system', __name__)

@system_bp.route('/system/initialize-db-cloud-sync')
def initialize_db():
    """
    Hidden route to initialize the database from the cloud server.
    Bypasses local network port 3306 restrictions.
    """
    # This route truncates users and books, so it is disabled unless a
    # dedicated DB_INIT_TOKEN is configured (there is no default token).
    expected_token = os.getenv('DB_INIT_TOKEN')
    if not expected_token:
        abort(404)

    token = request.args.get('token', '')
    if not hmac.compare_digest(token.encode(), expected_token.encode()):
        return "❌ Unauthorized: Invalid initialization token.", 403

    output = []
    output.append("🏗️ --- STARTING CLOUD INITIALIZATION ---")
    
    # 1. Run Schema
    msg_schema, success_schema = run_schema()
    output.append(msg_schema)
    
    if not success_schema:
        return "<pre>" + "\n".join(output) + "\n❌ FAILED during schema creation.</pre>", 500
        
    # 2. Run Seeding
    # Note: seed_data.main prints to stdout, we might want to capture or refactor it
    # For now, let's just trigger it.
    output.append("\n🌱 --- STARTING DATA SEEDING ---")
    try:
        run_seed() # This will seed users and 30 books
        output.append("✅ Seeding triggered successfully.")
    except Exception as e:
        output.append(f"❌ Seeding Error: {e}")
        
    output.append("\n🎉 --- CLOUD INITIALIZATION COMPLETE ---")
    output.append("You can now log in as admin@library.com with SEED_ADMIN_PASSWORD (or the generated password printed in the server log).")
    
    return "<pre>" + "\n".join(output) + "</pre>"
