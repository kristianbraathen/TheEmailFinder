import os
import sys
import logging
from datetime import datetime

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info(f"[{datetime.now()}] Starting WebJob execution...")
        logger.info(f"[{datetime.now()}] Current directory: {os.getcwd()}")
        
        # Add PyFiles to Python path
        pyfiles_path = os.path.join(os.getcwd(), 'src', 'PyFiles')
        sys.path.append(pyfiles_path)
        logger.info(f"[{datetime.now()}] PYTHONPATH: {os.environ.get('PYTHONPATH', '')}")
        
        logger.info(f"[{datetime.now()}] Running Python script...")
        
        # Import Flask app and create application context
        from src.PyFiles.app import app
        from src.PyFiles.SearchResultHandler import SearchResultHandler
        from src.PyFiles.KseApi import KseApi
        from src.PyFiles.Db import get_database_uri
        
        # Log database connection info (without password)
        db_uri = get_database_uri()
        safe_uri = db_uri.replace(db_uri.split('@')[0], '***')
        logger.info(f"[{datetime.now()}] Attempting database connection to: {safe_uri}")
        
        # Run the search process within application context
        with app.app_context():
            try:
                search_handler = SearchResultHandler()
                search_provider = KseApi()  # Initialize the search provider
                logger.info(f"[{datetime.now()}] Starting email search process...")
                search_handler.search_emails_and_display(search_provider=search_provider, batch_size=5, force_run=True)
                logger.info(f"[{datetime.now()}] Email search process completed")
            except Exception as e:
                logger.error(f"[{datetime.now()}] Error in search process: {str(e)}")
                logger.error("", exc_info=True)
                raise
            
        logger.info(f"[{datetime.now()}] Python script completed successfully")
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error in web job: {str(e)}")
        logger.error("", exc_info=True)
        raise

if __name__ == "__main__":
    main() 