import sys
import os
import datetime

# Sett rotnivå på prosjektet (antatt at run_email_search.py ligger i App_Data/jobs/triggered/webjobemailsearch/)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.PyFiles.GoogleKse import search_emails_and_display
from src.PyFiles.app import app

LOG_FILE = "/home/LogFiles/webjob.log"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Kunne ikke skrive til loggfil: {e}")

if __name__ == "__main__":
    with app.app_context():
        log("🚀 Starter WebJob...")
        try:
            success = search_emails_and_display(batch_size=5)
            if success:
                log("✅ Jobb ferdig uten feil.")
            else:
                log("⚠️ Jobb avsluttet med feil.")
        except Exception as e:
            log(f"❌ Feil under kjøring: {str(e)}")
        log("🛑 WebJob avsluttet.")
