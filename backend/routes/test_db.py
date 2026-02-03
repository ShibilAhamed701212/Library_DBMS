from flask import Blueprint, jsonify
from backend.repository.db_access import fetch_all

test_bp = Blueprint('test', __name__)

@test_bp.route('/test/db-schema')
def test_db_schema():
    try:
        # Get table structure
        table_info = fetch_all("SHOW CREATE TABLE book_suggestions")
        
        # Get column details
        columns = fetch_all("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, 
                   COLUMN_DEFAULT, EXTRA, CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'book_suggestions'
            ORDER BY ORDINAL_POSITION
        """)
        
        # Get sample data (first 5 rows)
        sample_data = fetch_all("SELECT * FROM book_suggestions LIMIT 5")
        
        return jsonify({
            'create_table': table_info[0][1] if table_info else 'Table not found',
            'columns': columns,
            'sample_data': sample_data,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'hint': 'Make sure the book_suggestions table exists and is accessible'
        }), 500
