import sys
import os
import datetime

# Change log file to be in the same directory as the script
LOG_FILE = os.path.join(os.path.dirname(__file__), "webjob.log")

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Kunne ikke skrive til loggfil: {e}")

# Log startup information
log("🔄 Starting WebJob initialization...")
log(f"Current working directory: {os.getcwd()}")
log(f"Python version: {sys.version}")
log(f"Python path: {sys.path}")

try:
    # Sett rotnivå på prosjektet
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
    log(f"Project root path: {project_root}")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        log(f"Added project root to Python path")
    
    log("Attempting to import required modules...")
    from src.PyFiles.GoogleKse import search_emails_and_display
    from src.PyFiles.app import app
    log("✅ Successfully imported required modules")

except Exception as e:
    log(f"❌ Error during initialization: {str(e)}")
    raise

if __name__ == "__main__":
    log("🚀 Starting main WebJob execution...")
    with app.app_context():
        try:
            success = search_emails_and_display(batch_size=5)
            if success:
                log("✅ Job completed successfully.")
            else:
                log("⚠️ Job completed with errors.")
        except Exception as e:
            log(f"❌ Error during execution: {str(e)}")
            raise
        finally:
            log("🛑 WebJob execution finished.")
