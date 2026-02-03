"""
email_service.py
----------------
Handles automated email notifications for the Library System.

Features:
- Book Issue Confirmation
- Overdue Reminders
- System Alerts

Note: Requires SMTP configuration in .env
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

# SMTP Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")

from email.mime.application import MIMEApplication

def send_email(to_email: str, subject: str, body: str, attachment_path: str = None):
    """
    Direct SMTP email sender.
    If no credentials found, it logs to console (Simulation Mode).
    """
    if not SMTP_USER or not SMTP_PASS:
        print(f"📧 [SIMULATION] Email to {to_email}")
        print(f"Subject: {subject}")
        if attachment_path:
            print(f"Attachment: {attachment_path}")
        print(f"Body: {body}\n")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Email Error: {e}")
        return False

def notify_issue(user_name: str, user_email: str, book_title: str, due_date: str):
    """Sends a confirmation email when a book is issued."""
    subject = f"📚 Book Issued: {book_title}"
    body = f"""Hi {user_name},

Happy reading! You have successfully issued '{book_title}' from LibManage.

📅 Due Date: {due_date}

Please return the book on or before the due date to avoid late fees.

Best regards,
Library Management Team
"""
    return send_email(user_email, subject, body)

def notify_overdue(user_name: str, user_email: str, book_title: str, days: int, fine: int):
    """Sends an alert for overdue books."""
    subject = f"⚠️ Overdue Notice: {book_title}"
    body = f"""Hi {user_name},

This is a reminder that '{book_title}' is overdue by {days} days.

💰 Current Fine: ₹{fine}

Please return the book as soon as possible to prevent further fines.

Best regards,
Library Management Team
"""
    return send_email(user_email, subject, body)


def notify_request_status(user_name: str, user_email: str, book_title: str, status: str):
    """Notifies user if their request was Rejected."""
    if status.lower() != 'rejected':
        return  # Approval is handled via notify_issue

    subject = f"📝 Request Update: {book_title}"
    body = f"""Hi {user_name},

We regret to inform you that your request for '{book_title}' has been {status}.

This may be due to high demand or library policy. You can browse the catalog for other available books.

Best regards,
Library Management Team
"""
    return send_email(user_email, subject, body)
