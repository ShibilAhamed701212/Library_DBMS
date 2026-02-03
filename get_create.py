
import os
import sys
sys.path.append(os.getcwd())
from backend.repository.db_access import fetch_one

try:
    res = fetch_one("SHOW CREATE TABLE chat_messages")
    with open('table_structure.txt', 'w') as f:
        f.write(res['Create Table'])
    print("Saved to table_structure.txt")
except Exception as e:
    print(e)
