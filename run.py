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
        
        # Run the search process within application context
        with app.app_context():
            search_handler = SearchResultHandler()
            search_handler.search_emails_and_display(batch_size=5, force_run=True)
            
        logger.info(f"[{datetime.now()}] Python script completed successfully")
        
    except Exception as e:
        logger.error(f"Error in web job: {str(e)}")
        logger.error("", exc_info=True)
        raise

if __name__ == "__main__":
    main() 