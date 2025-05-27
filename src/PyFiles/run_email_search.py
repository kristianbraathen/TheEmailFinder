import datetime
from src.PyFiles.GoogleKse import search_emails_and_display
from src.PyFiles.app import app

LOG_FILE = "/home/LogFiles/webjob.log"  # Azure WebJobs standard logområde

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")  # Vis også i live WebJob logg

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
