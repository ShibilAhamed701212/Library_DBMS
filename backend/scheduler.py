
from apscheduler.schedulers.background import BackgroundScheduler
from backend.services.issue_service import send_overdue_reminders
import atexit

def start_scheduler():
    """
    Initializes and starts the background scheduler.
    """
    scheduler = BackgroundScheduler()
    
    # Schedule overdue reminders every day at 10:00 AM
    scheduler.add_job(func=send_overdue_reminders, trigger="cron", hour=10, minute=0)
    
    # Schedule weekly performance report every Monday at 9:00 AM
    from backend.services.report_service import generate_weekly_report
    scheduler.add_job(func=generate_weekly_report, trigger="cron", day_of_week="mon", hour=9, minute=0)
    
    scheduler.start()
    print("⏰ Scheduler started. Automated emails will be sent daily at 10:00 AM.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
