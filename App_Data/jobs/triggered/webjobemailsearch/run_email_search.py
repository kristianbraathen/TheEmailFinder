import sys
import os
import datetime
import traceback

# Change log file to be in the same directory as the script
LOG_FILE = os.path.join(os.path.dirname(__file__), "webjob.log")

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"Could not write to log file: {e}")
        print(f"Current directory: {os.getcwd()}")
        print(f"Log file path: {LOG_FILE}")

try:
    log("🔄 Starting WebJob initialization...")
    log(f"Python version: {sys.version}")
    log(f"Current directory: {os.getcwd()}")
    log(f"Directory contents: {os.listdir('.')}")
    
    # Check if requirements are installed
    try:
        import flask
        import sqlalchemy
        import selenium
        log("✅ Core dependencies are available")
    except ImportError as e:
        log(f"❌ Missing dependency: {e}")
        log("⚙️ Attempting to install requirements...")
        os.system(f"pip install -r {os.path.join(os.path.dirname(__file__), 'requirements.txt')}")
        log("📦 Requirements installation attempted")

    # Set up Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    log(f"Project root: {project_root}")
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        log(f"Added {project_root} to Python path")
    log(f"Python path: {sys.path}")
    
    # Check src directory
    src_path = os.path.join(project_root, 'src', 'PyFiles')
    log(f"Checking src directory: {src_path}")
    if os.path.exists(src_path):
        log(f"src/PyFiles contents: {os.listdir(src_path)}")
    else:
        log("❌ src/PyFiles directory not found!")

    # Try imports
    log("Attempting to import required modules...")
    from src.PyFiles.GoogleKse import search_emails_and_display
    from src.PyFiles.app import app
    log("✅ Successfully imported required modules")

except Exception as e:
    log(f"❌ Initialization error: {str(e)}")
    log(f"Traceback: {traceback.format_exc()}")
    raise

if __name__ == "__main__":
    try:
        log("🚀 Starting main WebJob execution...")
        with app.app_context():
            try:
                success = search_emails_and_display(batch_size=5)
                if success:
                    log("✅ Job completed successfully")
                else:
                    log("⚠️ Job completed with errors")
            except Exception as e:
                log(f"❌ Error during execution: {str(e)}")
                log(f"Traceback: {traceback.format_exc()}")
                raise
    except Exception as e:
        log(f"❌ Fatal error: {str(e)}")
        log(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        log("🛑 WebJob execution finished")
