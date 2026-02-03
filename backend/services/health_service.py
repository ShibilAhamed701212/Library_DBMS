
import os
import psutil
import time
from backend.repository.db_access import fetch_one

def get_system_health():
    """Aggregates all system health metrics into a single report."""
    return {
        "database": check_db_health(),
        "disk": check_disk_usage(),
        "memory": check_memory_usage(),
        "cpu": psutil.cpu_percent(interval=None),
        "status": "Healthy"
    }

def check_db_health():
    """Checks DB connectivity and basic latency."""
    start_time = time.time()
    try:
        # Simple query to check connectivity
        fetch_one("SELECT 1")
        latency = round((time.time() - start_time) * 1000, 2)
        return {"status": "Online", "latency_ms": latency}
    except Exception as e:
        return {"status": "Offline", "error": str(e)}

def check_disk_usage():
    """Checks disk space on the drive where the project is located."""
    path = os.getcwd()
    usage = psutil.disk_usage(path)
    return {
        "total_gb": round(usage.total / (1024**3), 2),
        "used_gb": round(usage.used / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "percent": usage.percent
    }

def check_memory_usage():
    """Checks system memory usage."""
    memory = psutil.virtual_memory()
    return {
        "total_mb": round(memory.total / (1024**2), 2),
        "used_mb": round(memory.used / (1024**2), 2),
        "percent": memory.percent
    }

def get_error_logs(limit=10):
    """Fetches recent error logs from the database (if an audit/logs table exists)."""
    # Assuming audit_logs table exists from previous features
    try:
        from backend.repository.db_access import fetch_all
        return fetch_all("SELECT * FROM audit_logs WHERE action_type LIKE '%%ERROR%%' ORDER BY timestamp DESC LIMIT %s", (limit,))
    except Exception:
        return []
