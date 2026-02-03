
from flask import Blueprint, session, redirect, request, jsonify, flash

common_bp = Blueprint('common_bp', __name__)

@common_bp.route("/notifications/read/<int:notif_id>")
def mark_read(notif_id):
    if 'user_id' not in session: return redirect("/")
    
    from backend.services.notification_service import mark_notification_read
    mark_notification_read(notif_id, session['user_id'])
    return redirect(request.referrer or "/")

@common_bp.route("/notifications/read/all")
def mark_all_read_route():
    if 'user_id' not in session: return redirect("/")
    
    from backend.services.notification_service import mark_all_read
    mark_all_read(session['user_id'])
    return redirect(request.referrer or "/")

@common_bp.route("/api/notifications/unread")
def api_get_unread():
    if 'user_id' not in session: return jsonify([])
    
    from backend.services.notification_service import get_unread_notifications
    notifs = get_unread_notifications(session['user_id'])
    return jsonify(notifs)

@common_bp.route("/api/external/catalog")
def external_api_catalog():
    from backend.services.api_service import validate_key
    from backend.services.book_service import view_books
    
    key = request.headers.get("X-API-Key")
    if not key:
        return jsonify({"error": "Missing API Key"}), 401
        
    user_id = validate_key(key)
    if not user_id:
        return jsonify({"error": "Invalid API Key"}), 401
        
    books = view_books()
    return jsonify(books)
@common_bp.route("/api/book/get/<int:book_id>")
def common_get_book_json(book_id):
    """Returns book details for admin/member modals."""
    from backend.services.book_service import get_book
    from flask import jsonify
    
    # We allow this for everyone (maintenance bypass), 
    # but the service only returns what's safe.
    # However, let's keep it restricted to logged in for basic security
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
        
    try:
        book = get_book(book_id)
        if not book:
            return jsonify({"error": "Book not found", "success": False}), 404
        return jsonify({"success": True, "data": book})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
