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
from sqlalchemy.sql import text
from .Db import db
from .SearchResultHandler import search_emails_and_display  # Import the main search function

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
        self.process_running = True
        self.logger = logging.getLogger(__name__)
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
        self.chrome_options.add_argument("--disable-software-rasterizer")
        self.chrome_options.add_argument("--lang=en-NO")
        self.chrome_options.add_argument("--enable-unsafe-swiftshader")
        self.chrome_options.add_argument("--disable-user-data-dir")
        self.chrome_options.add_argument("--disable-dev-tools")
        self.chrome_options.add_argument("--remote-debugging-port=0")
        self.chrome_options.add_argument("--log-level=3")
        self.chrome_options.add_argument("--disable-default-apps")
        self.chrome_options.add_argument("--disable-session-crashed-bubble")
        self.logger.info("[INIT] KseApi instance initialized with process_running=True")

    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
            _instance.logger.info("[INSTANCE] Created new KseApi instance")
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
            self.logger.info("🔴 Process stopped by user")
            return True
        return False

    def search_company(self, company_name):
        """Perform KSE-specific search for a company
        Args:
            company_name (str): Name of the company to search for
        Returns:
            list: List of found email addresses
        """
        try:
            self.logger.info(f"🔍 Searching for company: {company_name}")
            search_query = f'"{company_name}" "Norge"'
            search_results = google_custom_search(search_query)
            all_emails = []
            
            chrome_service = Service(chromedriver_autoinstaller.install())
            
            for url in search_results:
                if self.check_stop():
                    break
                self.logger.info(f"🌐 Extracting emails from URL: {url}")
                try:
                    driver = webdriver.Chrome(service=chrome_service, options=self.chrome_options)
                    driver.get(url)
                    page_source = driver.page_source
                    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
                    all_emails.extend(emails)
                    driver.quit()
                except Exception as e:
                    self.logger.error(f"❌ Error extracting emails from {url}: {str(e)}")

            unique_emails = list(set(all_emails))
            self.logger.info(f"📧 Found {len(unique_emails)} unique emails")
            return unique_emails
            
        except Exception as e:
            self.logger.error(f"❌ Error searching for company {company_name}: {str(e)}")
            return []

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
                    result = search_emails_and_display(search_provider=_instance, force_run=True)
                    
                    if result and _instance.process_running:
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

