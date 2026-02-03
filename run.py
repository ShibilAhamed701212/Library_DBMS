"""
run.py
------
Application entry point with integrated ngrok tunneling.
"""

from backend.app import create_app
import os
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = create_app()

def cleanup_before_start():
    """Kill any existing ngrok processes and free port 5000."""
    try:
        # Kill all ngrok processes
        subprocess.run(['taskkill', '/F', '/IM', 'ngrok.exe'], 
                      capture_output=True, shell=True)
    except:
        pass
    
    try:
        # Find and kill process using port 5000
        result = subprocess.run(
            'netstat -ano | findstr :5000 | findstr LISTENING',
            capture_output=True, text=True, shell=True
        )
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    subprocess.run(['taskkill', '/F', '/PID', pid], 
                                 capture_output=True, shell=True)
    except:
        pass

def start_ngrok():
    """Start ngrok tunnel and return public URL."""
    ngrok_token = os.getenv('NGROK_AUTHTOKEN')
    if ngrok_token and ngrok_token != 'YOUR_TOKEN_HERE':
        try:
            from pyngrok import ngrok
            ngrok.set_auth_token(ngrok_token)
            tunnel = ngrok.connect("127.0.0.1:5000")
            return tunnel.public_url
        except Exception as e:
            print(f"⚠️ Ngrok error: {e}")
    return None

if __name__ == "__main__":
    
    # Silence pyngrok and other noisy loggers
    import logging
    # logging.getLogger("pyngrok").setLevel(logging.WARNING)
    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # -----------------------------
    # MAIN PROCESS ONLY (Pre-Reload)
    # -----------------------------
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Clean up ONLY in the main process before anything else
        cleanup_before_start()
        
        import time
        time.sleep(2)  # Wait for processes to fully terminate
    
    # -----------------------------
    # CHILD PROCESS ONLY (Reloader)
    # -----------------------------
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        from backend.scheduler import start_scheduler
        start_scheduler()
    
    # Start ngrok (Only in main/parent process to persist across reloads)
    public_url = None
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        public_url = start_ngrok()
        
        # Display startup info
        print("\n" + "="*60)
        print("🚀 LDBMS IS STARTING UP!")
        print(f"👉 Local URL:   http://127.0.0.1:5000")
        if public_url:
            print(f"🌐 Public URL:  {public_url}")
        else:
            print(f"🌐 Public URL:  Not available")
        print("="*60 + "\n")
    
    from backend import socketio
    socketio.run(app, debug=True, host='0.0.0.0', use_reloader=True, log_output=True)
