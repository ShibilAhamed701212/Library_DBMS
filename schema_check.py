
import os
import sys
sys.path.append(os.getcwd())
from backend.repository.db_access import fetch_all

try:
    cols = fetch_all("DESCRIBE dm_participants")
    for col in cols:
        print(f"{col['Field']}: {col['Type']}")
except Exception as e:
    print(f"Error: {e}")
