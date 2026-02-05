from backend.repository.db_access import execute

def update_schema():
    print("Updating database schema...")
    
    # 1. Add allow_requests
    try:
        execute("ALTER TABLE users ADD COLUMN allow_requests TINYINT(1) DEFAULT 1")
        print("✅ Added allow_requests column")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ️ allow_requests column already exists")
        else:
            print(f"❌ Error adding allow_requests: {e}")

    # 2. Add show_activity
    try:
        execute("ALTER TABLE users ADD COLUMN show_activity TINYINT(1) DEFAULT 1")
        print("✅ Added show_activity column")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("ℹ️ show_activity column already exists")
        else:
            print(f"❌ Error adding show_activity: {e}")

if __name__ == "__main__":
    update_schema()
