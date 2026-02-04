
import sys
import os

sys.path.append(os.getcwd())
from backend.app import create_app
from backend.repository.db_access import fetch_all

app = create_app()

def check_schema():
    with app.app_context():
        # Check columns
        cols = fetch_all("DESCRIBE chat_invitations")
        for c in cols:
            print(f"{c['Field']}: {c['Type']}")

if __name__ == "__main__":
    check_schema()
