
from backend.repository.db_access import execute_query

def setup_tickets():
    print("Setting up Support Tickets...")
    q1 = """
    CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        subject VARCHAR(255) NOT NULL,
        status ENUM('open', 'closed') DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_ticket_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(q1)

    q2 = """
    CREATE TABLE IF NOT EXISTS ticket_replies (
        reply_id INT AUTO_INCREMENT PRIMARY KEY,
        ticket_id INT NOT NULL,
        sender_id INT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_reply_ticket FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id) ON DELETE CASCADE,
        CONSTRAINT fk_reply_sender FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """
    execute_query(q2)
    print("✅ Support Ticket tables set up.")

if __name__ == "__main__":
    setup_tickets()
