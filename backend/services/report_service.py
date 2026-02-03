
import os
from fpdf import FPDF
from datetime import datetime
from backend.repository.db_access import fetch_one, fetch_all
from backend.services.email_service import send_email

def generate_weekly_report():
    """Generates a PDF report of library performance and emails it to admins."""
    print("Generating report...")
    
    # 1. Gather Data
    book_count = fetch_one("SELECT COUNT(*) as cnt FROM books")['cnt']
    user_count = fetch_one("SELECT COUNT(*) as cnt FROM users WHERE role='member'")['cnt']
    active_issues = fetch_one("SELECT COUNT(*) as cnt FROM issues WHERE return_date IS NULL")['cnt']
    
    top_books = most_issued_books()

    # 2. Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, 'Weekly Library Performance Report', ln=True, align='C')
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', ln=True, align='C')
    pdf.ln(10)

    # Stats Summary
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, 'General Statistics:', ln=True)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, f'- Total Books in Catalog: {book_count}', ln=True)
    pdf.cell(0, 10, f'- Total Registered Members: {user_count}', ln=True)
    pdf.cell(0, 10, f'- Current Active Borrowings: {active_issues}', ln=True)
    pdf.ln(10)

    # Most Popular Books
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, 'Most Popular Books this Week:', ln=True)
    pdf.set_font("helvetica", size=12)
    for i, book in enumerate(top_books[:5], 1):
        pdf.cell(0, 10, f'{i}. {book["title"]} ({book["count"]} borrows)', ln=True)

    # 3. Save PDF
    report_dir = "reports"
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
        
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(report_dir, filename)
    pdf.output(filepath)
    print(f"✅ Report saved: {filepath}")

    # 4. Email to Admins
    admins = fetch_all("SELECT email FROM users WHERE role='admin'")
    for admin in admins:
        send_email(
            admin['email'], 
            f"📊 Weekly Library Report - {datetime.now().strftime('%Y-%m-%d')}",
            "Please find the attached weekly library performance report.",
            filepath
        )
    
    return filepath

# --- RESTORED ANALYTICS FUNCTIONS ---

def most_issued_books():
    """Returns top 10 most borrowed books."""
    return fetch_all("""
        SELECT b.title, COUNT(*) as issue_count 
        FROM issues i 
        JOIN books b ON i.book_id = b.book_id 
        GROUP BY b.book_id 
        ORDER BY issue_count DESC LIMIT 10
    """)

def most_active_users():
    """Returns top 10 members with most borrowings."""
    return fetch_all("""
        SELECT u.name, COUNT(*) as total_issues 
        FROM issues i 
        JOIN users u ON i.user_id = u.user_id 
        WHERE u.role = 'member'
        GROUP BY u.user_id 
        ORDER BY total_issues DESC LIMIT 10
    """)

def monthly_issue_count():
    """Returns issue count per month for the last 12 months."""
    return fetch_all("""
        SELECT DATE_FORMAT(issue_date, '%Y-%m') as month, COUNT(*) as total_issues 
        FROM issues 
        GROUP BY month 
        ORDER BY month DESC LIMIT 12
    """)

def book_category_distribution():
    """Returns book count per category."""
    return fetch_all("SELECT category, COUNT(*) as book_count FROM books GROUP BY category")

def export_report(data, filename):
    """Exports data to CSV and returns success message."""
    import csv
    if not os.path.exists("exports"):
        os.makedirs("exports")
    
    filepath = f"exports/{filename}_{datetime.now().strftime('%Y%m%d')}.csv"
    if data:
        keys = data[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)
        return f"✅ Report exported successfully to {filepath}"
    return "⚠️ No data found to export."
