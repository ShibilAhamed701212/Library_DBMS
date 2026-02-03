from flask import Blueprint, jsonify
from backend.repository.db_access import fetch_all, fetch_one

test_auth_bp = Blueprint('test_auth', __name__)

@test_auth_bp.route('/test/auth/check-users')
def check_users():
    try:
        # Check if users table exists
        table_exists = fetch_one("SHOW TABLES LIKE 'users'")
        if not table_exists:
            return jsonify({
                'status': 'error',
                'message': 'Users table does not exist',
                'solution': 'Run database migrations to create the users table'
            })
        
        # Get all users (for debugging only!)
        users = fetch_all("SELECT user_id, email, name, role FROM users")
        
        return jsonify({
            'status': 'success',
            'table_exists': True,
            'user_count': len(users),
            'users': users
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
