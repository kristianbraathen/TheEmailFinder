import time
import requests
import re
from flask import Blueprint, jsonify, request, current_app
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from sqlalchemy.sql import text
from threading import Lock
import threading
import chromedriver_autoinstaller
import os
from src.PyFiles.Db import db # for SQLAlchemy session
import logging

# Flask blueprint og CORS
api6_blueprint = Blueprint('api6', __name__)
CORS(api6_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

process_lock = Lock()
_instance = None  # Singleton instance

connection_string = os.getenv('DATABASE_CONNECTION_STRING')

# ChromeDriver setup
try:
    driver_path = os.getenv('CHROMEDRIVER_PATH') or chromedriver_autoinstaller.install()
except Exception as e:
    print(f"Feil under installasjon av ChromeDriver: {e}")
    # Som fallback: prøv å bruke manuelt path basert på versjon
    version = chromedriver_autoinstaller.utils.get_chrome_version().split('.')[0]
    chromedriver_dir = os.path.join(os.path.dirname(chromedriver_autoinstaller.__file__), version)
    driver_path = os.path.join(chromedriver_dir, "chromedriver")

chrome_service = Service(executable_path=driver_path)
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--lang=en-NO")
chrome_options.add_argument("--enable-unsafe-swiftshader")
chrome_options.add_argument("--disable-user-data-dir")
chrome_options.add_argument("--disable-dev-tools")
chrome_options.add_argument("--remote-debugging-port=0")
chrome_options.add_argument("--log-level=3")
chrome_options.add_argument("--disable-default-apps")
chrome_options.add_argument("--disable-session-crashed-bubble")

API_KEY = "AIzaSyDX42Nl71H81zGkm8_4WDzkLv26N9Vpn_E"
CSE_ID = "879ff228f5bff4ed9"

def google_custom_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CSE_ID}&gl=no&lr=lang:no&num=3"
    response = requests.get(url)
    if response.status_code == 200:
        search_results = response.json()
        results = [item["link"] for item in search_results.get("items", [])]
        return results
    else:
        print(f"Feil ved Google API: {response.status_code} - {response.text}")
        return []

def extract_email_selenium(url):
    try:
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(url)

        # Vent til body-elementet er lastet i opp til 10 sekunder
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        page_source = driver.page_source
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
        driver.quit()
        return list(emails)
    except Exception as e:
        print(f"Feil ved uthenting av e-post fra {url}: {e}")
        return []

STOP_FLAG_FILE = "/app/stop_webjob.flag"

class GoogleKse:
    def __init__(self):
        self.process_running = True
        self.logger = logging.getLogger(__name__)
        self.logger.info("[INIT] GoogleKse instance initialized with process_running=True")

    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
            _instance.logger.info("[INSTANCE] Created new GoogleKse instance")
        return _instance
        
    def start(self):
        self.process_running = True
        self.logger.info("[START] Process started")
        
    def stop(self):
        self.process_running = False
        self.logger.info("[STOP] Process stopped")
        
    def check_stop(self, force_run=False):
        """Check if process should stop
        Args:
            force_run (bool): If True, ignore process_running state
        Returns:
            bool: True if should stop, False otherwise
        """
        # Always check stop flag first
        if os.path.exists(STOP_FLAG_FILE):
            self.logger.info("[STOP] Stop flag detected, stopping process")
            self.process_running = False
            try:
                os.remove(STOP_FLAG_FILE)
                self.logger.info("[STOP] Stop flag removed")
            except Exception as e:
                self.logger.warning(f"[STOP] Could not remove stop flag: {e}")
            return True
            
        # Only check process_running if not force_run
        if not force_run and not self.process_running:
            self.logger.info("[STOP] Process stopped by user")
            return True
        return False

def search_emails_and_display(batch_size=5, force_run=False):
    instance = GoogleKse.get_instance()
    
    try:
        # Ensure process is started and log initial state
        instance.start()  # This sets process_running to True
        instance.logger.info(f"🔵 Initial process_running state: {instance.process_running}")
        instance.logger.info("🔵 search_emails_and_display() started.")
        
        last_id = 0  # Initialize last_id
        chrome_service = Service(chromedriver_autoinstaller.install())
        
        while instance.process_running or force_run:  # Check process state at loop start
            instance.logger.info(f"🟡 Current process state - running: {instance.process_running}, force_run: {force_run}")
            
            # Get batch of records to process
            query = text("""
                SELECT id, "Org_nr", "Firmanavn"
                FROM imported_table
                WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL AND id > :last_id
                ORDER BY id ASC
                LIMIT :limit
            """)
            
            try:
                result = db.session.execute(query, {"last_id": last_id, "limit": batch_size})
                rows = result.fetchall()
                
                if not rows:
                    instance.logger.info("✅ No more records to process. Exiting loop.")
                    break
                
                instance.logger.info(f"🟡 Processing batch of {len(rows)} records (starting from last_id: {last_id})")
                
                for row in rows:
                    if not (instance.process_running or force_run):
                        instance.logger.info("🔴 Process stop requested, breaking batch processing")
                        break
                        
                    row_id, org_nr, company_name = row
                    instance.logger.info(f"🔍 Processing record {row_id} - org_nr: {org_nr}, company_name: {company_name}")
                    
                    search_query = f'"{company_name}" "Norge"'
                    search_results = google_custom_search(search_query)
                    all_emails = []
                    
                    for url in search_results:
                        if not (instance.process_running or force_run):
                            break
                        instance.logger.info(f"🌐 Extracting emails from URL: {url}")
                        emails = extract_email_selenium(url)
                        all_emails.extend(emails)
                    
                    unique_emails = set(all_emails)
                    email_list = list(unique_emails)
                    
                    if email_list:
                        instance.logger.info(f"📧 Found {len(email_list)} unique emails for org_nr {org_nr}")
                        for email in email_list:
                            insert_query = text("""
                                INSERT INTO search_results ("Org_nr", company_name, email)
                                VALUES (:org_nr, :company_name, :email)
                            """)
                            db.session.execute(insert_query, {
                                "org_nr": org_nr,
                                "company_name": company_name,
                                "email": email
                            })
                        db.session.commit()
                        instance.logger.info(f"✅ Emails saved for org_nr: {org_nr}")
                    
                    last_id = row_id  # Update last_id after successful processing
                    instance.logger.info(f"🔄 Updated last_id to: {last_id}")
                
                if not (instance.process_running or force_run):
                    instance.logger.info("🔴 Process stop requested, exiting main loop")
                    break
                    
            except Exception as batch_error:
                instance.logger.error(f"❌ Error processing batch: {str(batch_error)}")
                db.session.rollback()
                break
        
        instance.logger.info(f"✅ search_emails_and_display() completed. Final last_id: {last_id}")
        return True
        
    except Exception as e:
        instance.logger.error(f"❌ Error in search_emails_and_display(): {str(e)}")
        return False
    finally:
        if not force_run:  # Only stop if not force_run
            instance.stop()
        instance.logger.info(f"🔄 Final process state - running: {instance.process_running}, force_run: {force_run}")

@api6_blueprint.route('/start_process_google', methods=['POST'])
def start_process_google():
    global _instance
    
    with process_lock:
        if _instance is None:
            _instance = GoogleKse()
        elif _instance.process_running:
            return jsonify({"status": "Process is already running"}), 400

        _instance.start()
        
        def background_search():
            try:
                with current_app.app_context():
                    _instance.logger.info("[START] Background search started")
                    result = search_emails_and_display(force_run=True)
                    
                    if result and _instance.process_running:  # Only consider success if process completed normally
                        _instance.logger.info("[SUCCESS] Background search completed successfully")
                    else:
                        status = "stopped early" if not _instance.process_running else "encountered an error"
                        _instance.logger.warning(f"[WARNING] Background search {status}")
                        
            except Exception as e:
                _instance.logger.error(f"[ERROR] Error in background search: {str(e)}")
            finally:
                with process_lock:
                    was_running = _instance.process_running
                    _instance.stop()
                    _instance.logger.info(f"[STOP] Background search finished. Was running: {was_running}")

        threading.Thread(target=background_search, daemon=True).start()
        return jsonify({"status": "Process started and running in background"}), 200

@api6_blueprint.route('/stop_process_google', methods=['POST'])
def stop_process_google():
    global _instance
    
    with process_lock:
        if _instance is None or not _instance.process_running:
            return jsonify({"status": "Process was not running"}), 200

        try:
            _instance.stop()
            return jsonify({"status": "Process stopped"}), 200
        except Exception as e:
            _instance.logger.error(f"[ERROR] Error stopping process: {str(e)}")
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500
