import os
import sys
import time
from datetime import datetime
from src.PyFiles.email_search import EmailSearch
import logging

# Setup logging with plain text indicators instead of emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webjob.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def check_stop_flag():
    stop_flag = os.path.join(os.path.dirname(__file__), "stop_webjob.flag")
    if os.path.exists(stop_flag):
        logging.info("[STOP] Stop flag detected, cleaning up...")
        try:
            os.remove(stop_flag)
            logging.info("[STOP] Stop flag removed")
        except Exception as e:
            logging.error(f"[ERROR] Error removing stop flag: {e}")
        return True
    return False

def main():
    try:
        start_time = datetime.now()
        logging.info("[START] WebJob started at %s", start_time)
        
        email_search = EmailSearch()
        
        while True:
            if check_stop_flag():
                logging.info("[STOP] Stopping WebJob due to stop flag")
                break
                
            try:
                email_search.process_next_batch()
            except Exception as e:
                logging.error(f"[ERROR] Error processing batch: {e}")
                
            # Sleep for a short time to prevent hammering the database
            time.sleep(5)
            
            # Log heartbeat every 5 minutes
            if (datetime.now() - start_time).seconds % 300 < 5:
                logging.info("[INFO] WebJob still running - heartbeat")
                
    except Exception as e:
        logging.error(f"[ERROR] Critical error in WebJob: {e}")
        raise
    finally:
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"[END] WebJob ended at {end_time}. Total duration: {duration}")

if __name__ == "__main__":
    main() 