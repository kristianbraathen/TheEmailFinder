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
kse_api = None  # Will hold our singleton instance

STOP_FLAG_FILE = "/app/stop_webjob.flag"

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
            
            # Process batch here...
            # Your existing batch processing code would go here
            
            # Example of how to use check_stop in a loop:
            for item in items:
                if kse_api.check_stop(force_run):
                    break
                # Process item...
            
        kse_api.logger.info("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        kse_api.logger.error(f"❌ Error in search_emails_and_display(): {str(e)}")
        return False

@api3_blueprint.route('/start_process_kse', methods=['POST'])
def start_process_kse():
    global kse_api
    
    with process_lock:
        if kse_api is None:
            kse_api = KseApi()
        elif kse_api.process_running:
            return jsonify({"status": "Process is already running"}), 400

        kse_api.start()
        
        def background_search():
            try:
                with current_app.app_context():
                    kse_api.logger.info("[START] Background search started")
                    result = search_emails_and_display(kse_api, force_run=True)  # Added force_run=True
                    if result:
                        kse_api.logger.info("[SUCCESS] Background search completed successfully")
                    else:
                        kse_api.logger.warning("[WARNING] Background search encountered an issue")
            except Exception as e:
                kse_api.logger.error(f"[ERROR] Error in background search: {str(e)}")
            finally:
                with process_lock:
                    kse_api.stop()

        threading.Thread(target=background_search, daemon=True).start()
        return jsonify({"status": "Process started and running in background"}), 200

@api3_blueprint.route('/stop_process_kse', methods=['POST'])
def stop_process_kse():
    global kse_api
    
    with process_lock:
        if kse_api is None or not kse_api.process_running:
            return jsonify({"status": "Process was not running"}), 200

        try:
            kse_api.stop()
            return jsonify({"status": "Process stopped"}), 200
        except Exception as e:
            kse_api.logger.error(f"[ERROR] Error stopping process: {str(e)}")
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500

