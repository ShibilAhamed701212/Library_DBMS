
from backend.repository.db_access import execute_query, fetch_all, fetch_one

def create_ticket(user_id, subject, message):
    try:
        from backend.config.db import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Create Ticket
        cursor.execute("INSERT INTO tickets (user_id, subject) VALUES (%s, %s)", (user_id, subject))
        conn.commit() # Commit to get ID
        ticket_id = cursor.lastrowid
        
        # 2. Add First Message as Reply
        cursor.execute("INSERT INTO ticket_replies (ticket_id, sender_id, message) VALUES (%s, %s, %s)", 
                       (ticket_id, user_id, message))
        conn.commit()
        cursor.close()
        conn.close()
        
        return "✅ Ticket created successfully"
    except Exception as e:
        return f"❌ Failed to create ticket: {str(e)}"

def add_reply(ticket_id, sender_id, message):
    try:
        execute_query("INSERT INTO ticket_replies (ticket_id, sender_id, message) VALUES (%s, %s, %s)",
                     (ticket_id, sender_id, message))
        
        # Notification Hook
        ticket = fetch_one("SELECT user_id FROM tickets WHERE ticket_id = %s", (ticket_id,))
        if ticket and ticket['user_id'] != int(sender_id):
             from backend.services.notification_service import add_notification
             add_notification(ticket['user_id'], f"🎫 New Reply on Ticket #{ticket_id}")

        return "✅ Reply added"
    except Exception as e:
        return f"❌ Reply failed: {str(e)}"

def close_ticket(ticket_id):
    execute_query("UPDATE tickets SET status = 'closed' WHERE ticket_id = %s", (ticket_id,))
    
    # Notification Hook
    ticket = fetch_one("SELECT user_id FROM tickets WHERE ticket_id = %s", (ticket_id,))
    if ticket:
         from backend.services.notification_service import add_notification
         add_notification(ticket['user_id'], f"🔒 Ticket #{ticket_id} has been closed.")

    return "✅ Ticket closed"

def get_user_tickets(user_id):
    return fetch_all("SELECT * FROM tickets WHERE user_id = %s ORDER BY created_at DESC", (user_id,))

def get_all_tickets():
    return fetch_all(
        """
        SELECT t.*, u.name as user_name, u.email 
        FROM tickets t
        JOIN users u ON t.user_id = u.user_id
        ORDER BY t.created_at DESC
        """
    )

def get_ticket_details(ticket_id):
    ticket = fetch_one(
        """
        SELECT t.*, u.name as user_name 
        FROM tickets t 
        JOIN users u ON t.user_id = u.user_id 
        WHERE t.ticket_id = %s
        """, 
        (ticket_id,)
    )
    
    if not ticket: return None
    
    replies = fetch_all(
        """
        SELECT r.*, u.name as sender_name, u.role as sender_role
        FROM ticket_replies r
        JOIN users u ON r.sender_id = u.user_id
        WHERE r.ticket_id = %s
        ORDER BY r.created_at ASC
        """,
        (ticket_id,)
    )
    
    return {"ticket": ticket, "replies": replies}
