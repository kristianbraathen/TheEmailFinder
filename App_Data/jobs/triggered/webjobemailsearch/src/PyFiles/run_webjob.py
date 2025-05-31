import logging
import sys
from datetime import datetime
from GoogleKse import search_emails_and_display

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("🚀 Starting main WebJob execution...")
        
        # Call with force_run=True to ignore process_running state
        result = search_emails_and_display(force_run=True)
        
        if result:
            logger.info("✅ Job completed successfully")
        else:
            logger.error("❌ Job failed")
            sys.exit(1)
            
        logger.info("🛑 WebJob execution finished")
        
    except Exception as e:
        logger.error(f"❌ Error in main execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 