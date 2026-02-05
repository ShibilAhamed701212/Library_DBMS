from backend.repository.db_access import fetch_all, fetch_one
import json
from datetime import datetime, date

def default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return str(obj)

try:
    cols = fetch_all('DESCRIBE books')
    sample = fetch_one('SELECT * FROM books LIMIT 1')
    
    with open('diag_output.txt', 'w', encoding='utf-8') as f:
        f.write("COLUMNS:\n")
        for c in cols:
            f.write(f"{c['Field']} - {c['Type']}\n")
        f.write("\nSAMPLE ROW:\n")
        f.write(json.dumps(sample, default=default, indent=2))
except Exception as e:
    with open('diag_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"ERROR: {str(e)}")
