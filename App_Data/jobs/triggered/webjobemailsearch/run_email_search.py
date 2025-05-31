import sys
import os
import datetime
import traceback
import signal
import time

# Change log file to be in the same directory as the script
LOG_FILE = os.path.join(os.path.dirname(__file__), "webjob.log")
STOP_FLAG_FILE = os.path.join(os.path.dirname(__file__), "stop_webjob.flag")

# Global flag for graceful shutdown
should_exit = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global should_exit
    log(f"🛑 Received signal {signum}, initiating graceful shutdown...")
    should_exit = True

def check_stop_flag():
    """Check if the stop flag file exists"""
    if os.path.exists(STOP_FLAG_FILE):
        log("🛑 Stop flag detected, initiating graceful shutdown...")
        try:
            os.remove(STOP_FLAG_FILE)
            log("✅ Stop flag removed")
        except Exception as e:
            log(f"⚠️ Could not remove stop flag: {e}")
        return True
    return False

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

def check_dependencies():
    """Check and install required dependencies"""
    required_packages = {
        'flask': 'Flask',
        'sqlalchemy': 'SQLAlchemy',
        'selenium': 'selenium',
        'requests': 'requests',
        'psycopg2': 'psycopg2-binary'
    }
    
    missing_packages = []
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            log(f"✅ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            log(f"❌ {package_name} is missing")
    
    if missing_packages:
        log("⚙️ Installing missing dependencies...")
        for package in missing_packages:
            try:
                os.system(f"pip install {package} --no-cache-dir")
                log(f"📦 Installed {package}")
            except Exception as e:
                log(f"❌ Failed to install {package}: {e}")
                raise

def setup_environment():
    """Set up the Python environment and paths"""
    project_root = os.path.abspath(os.path.dirname(__file__))
    src_path = os.path.join(project_root, 'src', 'PyFiles')
    
    # Add paths to Python path if not already there
    for path in [project_root, src_path]:
        if path not in sys.path:
            sys.path.insert(0, path)
            log(f"✅ Added {path} to Python path")
    
    # Verify src directory structure
    if not os.path.exists(src_path):
        log("❌ src/PyFiles directory not found!")
        raise FileNotFoundError(f"Required directory not found: {src_path}")
    
    log(f"📂 src/PyFiles contents: {os.listdir(src_path)}")
    return project_root, src_path

def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        log("🔄 Starting WebJob initialization...")
        log(f"🐍 Python version: {sys.version}")
        log(f"📂 Current directory: {os.getcwd()}")
        
        # Check and install dependencies
        check_dependencies()
        
        # Set up environment
        setup_environment()
        
        # Import required modules
        log("📥 Importing required modules...")
        from src.PyFiles.GoogleKse import search_emails_and_display
        from src.PyFiles.app import app
        log("✅ Successfully imported required modules")
        
        # Main execution
        log("🚀 Starting main WebJob execution...")
        with app.app_context():
            batch_size = 5
            while not should_exit and not check_stop_flag():
                try:
                    success = search_emails_and_display(batch_size=batch_size)
                    if not success:
                        log("⚠️ Batch processing returned False, stopping...")
                        break
                    
                    # Small delay between batches
                    time.sleep(1)
                    
                except Exception as e:
                    log(f"❌ Error processing batch: {str(e)}")
                    log(f"Traceback: {traceback.format_exc()}")
                    raise
                
            log("✅ Job completed successfully")
            
    except Exception as e:
        log(f"❌ Fatal error: {str(e)}")
        log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        log("🛑 WebJob execution finished")

if __name__ == "__main__":
    main()
