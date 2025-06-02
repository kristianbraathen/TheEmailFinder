import sys
import os
import datetime
import traceback
import signal
import time
import logging

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

def run_search_module(search_fn, name, batch_size=5):
    """Run a specific search module
    Args:
        search_fn: The search function to use (not used anymore)
        name: Name of the search module for logging
        batch_size: Number of records to process per batch
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import and get provider instance
        if name == "Google CSE":
            from src.PyFiles.GoogleKse import GoogleKse
            provider = GoogleKse.get_instance()
        elif name == "1881 CSE":
            from src.PyFiles.Kseapi1881 import Kseapi1881
            provider = Kseapi1881.get_instance()
        elif name == "KSE CSE":
            from src.PyFiles.KseApi import KseApi
            provider = KseApi.get_instance()
        else:
            log(f"❌ Unknown provider for {name}")
            return False

        # Start the provider
        provider.start()  # This will set process_running to True
        log(f"✅ Provider started with process_running = {provider.process_running}")
        
        # Run the search with the provider
        from src.PyFiles.SearchResultHandler import search_emails_and_display
        success = search_emails_and_display(search_provider=provider, batch_size=batch_size, force_run=True)
            
        if not success:
            log(f"⚠️ {name} search returned False")
            return False
            
        log(f"✅ {name} search completed successfully")
        return True
    except Exception as e:
        log(f"❌ Error in {name} search: {str(e)}")
        traceback.print_exc()
        return False

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
        project_root, src_path = setup_environment()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(LOG_FILE)
            ]
        )
        
        # Import and initialize required modules
        log("Attempting to import required modules...")
        from src.PyFiles.app import app
        from src.PyFiles.Db import db
        
        # Initialize database
        with app.app_context():
            db.init_app(app)
            log("✅ Database initialized")
        
        # Get the search module type from environment variable
        search_type = os.getenv('SEARCH_TYPE', 'google')
        log(f"🔍 Running search type: {search_type}")
        
        # Map search types to module configurations
        search_configs = {
            'google': ('src.PyFiles.GoogleKse', "Google CSE"),
            '1881': ('src.PyFiles.Kseapi1881', "1881 CSE"),
            'kse': ('src.PyFiles.KseApi', "KSE CSE")
        }
        
        if search_type not in search_configs:
            log(f"❌ Unknown search type: {search_type}")
            raise ValueError(f"Unknown search type: {search_type}")
            
        module_path, module_name = search_configs[search_type]
        log(f"🔄 Using search module: {module_path} ({module_name})")
        
        # Main execution
        log("🚀 Starting main WebJob execution...")
        
        # Run the search module within app context
        with app.app_context():
            success = run_search_module(None, module_name, batch_size=5)
        
        if success:
            log("✅ Job completed successfully")
            return 0
        else:
            log("⚠️ Job completed with warnings")
            return 1
            
    except Exception as e:
        log(f"❌ Error in main execution: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()
