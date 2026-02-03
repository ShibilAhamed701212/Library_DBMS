from functools import wraps
from flask import redirect, url_for, session, flash, jsonify

def login_required(f):
    """
    Decorator to ensure the user is logged in.
    Redirects to the login page if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def member_required(f):
    """
    Decorator to ensure the user is a member.
    Redirects to the appropriate page if not a member.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
            
        if session.get('role') != 'member':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('member.member_dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorator to ensure the user is an admin.
    Redirects to the appropriate page if not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
            
        if session.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('member.member_dashboard'))
            
        return f(*args, **kwargs)
    return decorated_function

def api_login_required(f):
    """
    API version of login_required that returns a 401 if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'redirect': url_for('auth.login')
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def api_member_required(f):
    """
    API version of member_required that returns a 403 if not a member.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'redirect': url_for('auth.login')
            }), 401
            
        if session.get('role') != 'member':
            return jsonify({
                'status': 'error',
                'message': 'Insufficient permissions',
                'redirect': url_for('member.member_dashboard')
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def api_admin_required(f):
    """
    API version of admin_required that returns a 403 if not an admin.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'redirect': url_for('auth.login')
            }), 401
            
        if session.get('role') != 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Insufficient permissions',
                'redirect': url_for('member.member_dashboard')
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function
