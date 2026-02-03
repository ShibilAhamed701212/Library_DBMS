import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.repository.db_access import fetch_all, execute_query
from backend.config.db import get_connection

if __name__ == "__main__":
    try:
        print("=== 1. CONNECTING ===")
        conn = get_connection()
        print("   ✅ Connected.")
        
        print("\n=== 2. INSPECTING COLUMNS ===")
        # Get raw columns
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW COLUMNS FROM book_suggestions")
        cols = cursor.fetchall()
        available_columns = {c['Field'] for c in cols}
        print(f"   Available Columns: {available_columns}")
        
        print("\n=== 3. PROBING LOGIC ===")
        # user_id = session["user_id"] -> simulate with 1
        user_id = 1
        
        # 1. ID
        id_col = "suggestion_id" if "suggestion_id" in available_columns else "id"
        print(f"   id_col: {id_col}")
        
        # 2. Notes / Reason
        notes_col = "notes"
        if "notes" not in available_columns and "reason" in available_columns:
            notes_col = "reason"
        print(f"   notes_col: {notes_col}")
        
        # 3. Date
        date_col = "created_at"
        if "created_at" not in available_columns and "suggestion_date" in available_columns:
            date_col = "suggestion_date"
        print(f"   date_col: {date_col}")
            
        # 4. ISBN (optional for display)
        isbn_col = ", isbn" if "isbn" in available_columns else ""
        print(f"   isbn_col: '{isbn_col}'")

        # Construct Query
        query = f"""
            SELECT 
                {id_col} as suggestion_id, 
                title, 
                author, 
                {notes_col} as notes, 
                {date_col} as suggestion_date, 
                status
                {isbn_col}
            FROM book_suggestions 
            WHERE user_id = %s 
            ORDER BY {date_col} DESC
        """
        print(f"\n=== 4. GENERATED QUERY ===\n{query}")
        
        print("\n=== 5. EXECUTING QUERY ===")
        cursor.execute(query, (user_id,))
        rows = cursor.fetchall()
        print(f"   ✅ Query Success! Found {len(rows)} rows.")
        for r in rows:
            print(f"   - {r}")
            
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: {repr(e)}")
        import traceback
        traceback.print_exc()
