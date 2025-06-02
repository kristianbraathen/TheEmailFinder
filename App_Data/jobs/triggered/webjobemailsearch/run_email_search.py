import os
import sys
import logging
from datetime import datetime

# Configure paths for both WebJob and main app sources
current_dir = os.path.dirname(os.path.abspath(__file__))
webjob_src_path = os.path.join(current_dir, "src", "PyFiles")
app_src_path = "/app/src/PyFiles"

# Add both paths to Python path
for path in [webjob_src_path, app_src_path]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Configure logging
LOG_FILE = os.path.join(current_dir, "webjob.log")
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Starting WebJob...")
        logger.info(f"Current directory: {current_dir}")
        logger.info(f"WebJob src path: {webjob_src_path}")
        logger.info(f"App src path: {app_src_path}")
        logger.info(f"Python path: {sys.path}")
        
        # Import required modules
        from app import app
        from Db import db
        from GoogleKse import GoogleKse
        from SearchResultHandler import search_emails_and_display
        logger.info("✅ Modules imported")
        
        # Initialize database and run search
        with app.app_context():
            # Initialize database
            db.init_app(app)
            logger.info("✅ Database initialized")
            
            # Get and start provider
            provider = GoogleKse.get_instance()
            provider.process_running = True
            logger.info("✅ Provider initialized")
            
            # Run search
            logger.info("🔍 Starting search...")
            success = search_emails_and_display(
                search_provider=provider,
                batch_size=5,
                force_run=True
            )
            
            if success:
                logger.info("✅ Search completed successfully")
                return 0
            else:
                logger.info("⚠️ Search completed with warnings")
                return 1
                
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
