
from flask import Blueprint, render_template, jsonify
from backend.middleware.auth import admin_required
from backend.repository.db_access import fetch_all
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/admin/analytics')

@analytics_bp.route("/")
@admin_required
def analytics_dashboard():
    """Renders the main analytics dashboard."""
    return render_template("admin/analytics.html", active_page="admin_analytics")

@analytics_bp.route("/data")
@admin_required
def get_analytics_data():
    """Returns JSON data for charts."""
    
    # 1. Borrowing Trends (Last 30 Days)
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(29, -1, -1)]
    
    trend_query = """
        SELECT DATE(issue_date) as day, COUNT(*) as count 
        FROM issues 
        WHERE issue_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY day 
        ORDER BY day ASC
    """
    trend_results = fetch_all(trend_query)
    trend_dict = {str(r['day']): r['count'] for r in trend_results}
    trend_data = [trend_dict.get(d, 0) for d in dates]
    
    # 2. Category Popularity
    cat_query = """
        SELECT b.category, COUNT(*) as count 
        FROM issues i
        JOIN books b ON i.book_id = b.book_id
        GROUP BY b.category
        ORDER BY count DESC
    """
    cat_results = fetch_all(cat_query)
    cat_labels = [r['category'] for r in cat_results]
    cat_data = [r['count'] for r in cat_results]
    
    # 3. Monthly Status (Issued vs Returned)
    status_query = """
        SELECT 
            SUM(CASE WHEN return_date IS NULL THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN return_date IS NOT NULL THEN 1 ELSE 0 END) as returned
        FROM issues
    """
    status_res = fetch_all(status_query)[0]
    
    return jsonify({
        "trends": {
            "labels": dates,
            "values": trend_data
        },
        "categories": {
            "labels": cat_labels,
            "values": cat_data
        },
        "status": {
            "labels": ["Active", "Returned"],
            "values": [status_res['active'] or 0, status_res['returned'] or 0]
        }
    })
