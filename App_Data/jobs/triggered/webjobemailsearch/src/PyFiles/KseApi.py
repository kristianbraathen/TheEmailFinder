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

class KseApi:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.process_running = True
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
        
    def check_stop(self):
        if not self.process_running:
            self.logger.info("[STOP] Prosessen er stoppet av brukeren")
            return True
        return False

    def start(self):
        self.process_running = True
        self.logger.info("[START] Process started")

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
                    result = search_emails_and_display(kse_api)
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

