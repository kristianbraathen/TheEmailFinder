import sys
import os
import logging
from datetime import datetime

# Set up logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'job.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    logging.info("Starting WebJob")
    print("Hello World")
    logging.info("Successfully printed Hello World")
    sys.exit(0)
except Exception as e:
    logging.error(f"Error occurred: {str(e)}")
    sys.exit(1) 