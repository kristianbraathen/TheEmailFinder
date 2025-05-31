import time
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint, request, current_app
from flask_cors import CORS
import re
from threading import Lock
import chromedriver_autoinstaller
import os
import threading
import logging

api3_blueprint = Blueprint('api3', __name__)
CORS(api3_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

process_lock = Lock()
_instance = None  # Singleton instance

STOP_FLAG_FILE = "/app/stop_webjob.flag"

# CSE Configuration
API_KEY = "AIzaSyDX42Nl71H81zGkm8_4WDzkLv26N9Vpn_E"
CSE_ID = "05572ab81b7254d58"

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

class KseApi:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process_running = True  # Initialize as True by default
        self.chrome_options = Options()
        if os.path.exists("/usr/bin/google-chrome"):
            self.chrome_options.binary_location = "/usr/bin/google-chrome"
        else:
            self.chrome_options.binary_location = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

        self.chrome_options.add_argument("--headless=new")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        
    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance
        
    def stop(self):
        self.process_running = False
        self.logger.info("[STOP] Prosessen er stoppet av brukeren")
        
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
            return True
            
        # Only check process_running if not force_run
        if not force_run and not self.process_running:
            self.logger.info("[STOP] Process stopped by user")
            return True
        return False

    def start(self):
        self.process_running = True
        self.logger.info("[START] Process started")

def search_emails_and_display(kse_api, batch_size=5, force_run=False):
    try:
        kse_api.logger.info(f"🔵 process_running is {kse_api.process_running}")
        kse_api.logger.info("🔵 search_emails_and_display() started.")
        
        last_id = 0
        
        while True:
            if kse_api.check_stop(force_run):
                kse_api.logger.info("🔴 Process stopped, exiting...")
                break

            kse_api.logger.info(f"🟡 Fetching batch starting from last_id: {last_id}")
            
            # Get batch of records to process
            query = text(f"""
                SELECT id, "Org_nr", "Firmanavn"
                FROM imported_table
                WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL AND id > :last_id
                ORDER BY id ASC
                LIMIT :limit
            """)
            result = db.session.execute(query, {"last_id": last_id, "limit": batch_size})
            rows = result.fetchall()

            if not rows:
                kse_api.logger.info("✅ No more records to process. Exiting loop.")
                break

            kse_api.logger.info(f"🟡 Processing batch of {len(rows)} records (last_id: {last_id}).")

            for row in rows:
                if kse_api.check_stop(force_run):
                    break

                row_id, org_nr, company_name = row
                kse_api.logger.info(f"🔍 Processing org_nr: {org_nr}, company_name: {company_name}")

                search_query = f'"{company_name}" "Norge"'
                kse_api.logger.info(f"🔍 Searching with query: {search_query}")

                search_results = google_custom_search(search_query)
                all_emails = []
                
                for url in search_results:
                    if kse_api.check_stop(force_run):
                        break
                    kse_api.logger.info(f"🌐 Extracting emails from URL: {url}")
                    try:
                        driver = webdriver.Chrome(service=chrome_service, options=kse_api.chrome_options)
                        driver.get(url)
                        page_source = driver.page_source
                        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
                        all_emails.extend(emails)
                        driver.quit()
                    except Exception as e:
                        kse_api.logger.error(f"❌ Error extracting emails from {url}: {str(e)}")

                unique_emails = set(all_emails)
                email_list = list(unique_emails)

                if email_list:
                    kse_api.logger.info(f"📧 Found emails: {email_list}")
                    for email in email_list:
                        insert_query = text("""
                            INSERT INTO search_results ("Org_nr", company_name, email)
                            VALUES (:org_nr, :company_name, :email)
                        """)
                        db.session.execute(insert_query, {"org_nr": org_nr, "company_name": company_name, "email": email})
                    db.session.commit()
                    kse_api.logger.info(f"✅ Emails inserted into database for org_nr: {org_nr}")

                last_id = row_id

        kse_api.logger.info("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        kse_api.logger.error(f"❌ Error in search_emails_and_display(): {str(e)}")
        return False

@api3_blueprint.route('/start_process_kse', methods=['POST'])
def start_process_kse():
    global _instance
    
    with process_lock:
        if _instance is None:
            _instance = KseApi()
        elif _instance.process_running:
            return jsonify({"status": "Process is already running"}), 400

        _instance.start()
        
        def background_search():
            try:
                with current_app.app_context():
                    _instance.logger.info("[START] Background search started")
                    result = search_emails_and_display(_instance, force_run=True)  # Added force_run=True
                    if result:
                        _instance.logger.info("[SUCCESS] Background search completed successfully")
                    else:
                        _instance.logger.warning("[WARNING] Background search encountered an issue")
            except Exception as e:
                _instance.logger.error(f"[ERROR] Error in background search: {str(e)}")
            finally:
                with process_lock:
                    _instance.stop()

        threading.Thread(target=background_search, daemon=True).start()
        return jsonify({"status": "Process started and running in background"}), 200

@api3_blueprint.route('/stop_process_kse', methods=['POST'])
def stop_process_kse():
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

