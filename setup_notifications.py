
from backend.repository.db_access import execute_query

def setup_notifications():
    print("Setting up Notifications...")
    query = """
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        message TEXT NOT NULL,
        is_read BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_notif_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(query)
    print("✅ Notifications table set up.")

if __name__ == "__main__":
    setup_notifications()
