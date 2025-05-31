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
process_running = True  # Changed to True by default
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

    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance

def search_emails_and_display(batch_size=5, force_run=False):
    global process_running
    instance = GoogleKse.get_instance()
    instance.process_running = True  # Ensure it's True at start
    
    try:
        print(f"🔵 process_running is {instance.process_running}")
        print("🔵 search_emails_and_display() started.")
        
        last_id = 0
        
        while True:
            # Only check process_running if not force_run
            if not force_run and not instance.process_running:
                print("🔴 Prosessen er stoppet av brukeren.")
                break

            # Always check stop flag, regardless of force_run
            if os.path.exists(STOP_FLAG_FILE):
                print("🔴 Stoppflagg oppdaget på disk. Avslutter prosess.")
                instance.process_running = False
                break

            print(f"🟡 Fetching batch starting from last_id: {last_id}")
            
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
                print("✅ Ingen flere rader å behandle. Exiting loop.")
                break

            print(f"🟡 Behandler batch med {len(rows)} rader (last_id: {last_id}).")

            for row in rows:
                # Always check stop flag
                if os.path.exists(STOP_FLAG_FILE):
                    print("🔴 Stoppflagg oppdaget under batch-prosessering. Avslutter prosess.")
                    instance.process_running = False
                    break

                # Only check process_running if not force_run
                if not force_run and not instance.process_running:
                    print("🔴 Prosessen er stoppet av brukeren.")
                    break

                row_id, org_nr, company_name = row
                print(f"🔍 Processing org_nr: {org_nr}, company_name: {company_name}")

                search_query = f'"{company_name}" "Norge"'
                print(f"🔍 Søker med query: {search_query}")

                search_results = google_custom_search(search_query)
                all_emails = []
                for url in search_results:
                    # Always check stop flag
                    if os.path.exists(STOP_FLAG_FILE):
                        print("🔴 Stoppflagg oppdaget under url-prosessering. Avslutter prosess.")
                        instance.process_running = False
                        break
                    # Only check process_running if not force_run
                    if not force_run and not instance.process_running:
                        print("🔴 Prosessen er stoppet av brukeren.")
                        break
                    print(f"🌐 Extracting emails from URL: {url}")
                    emails = extract_email_selenium(url)
                    all_emails.extend(emails)

                unique_emails = set(all_emails)
                email_list = list(unique_emails)

                if email_list:
                    print(f"📧 Found emails: {email_list}")
                    for email in email_list:
                        insert_query = text("""
                            INSERT INTO search_results ("Org_nr", company_name, email)
                            VALUES (:org_nr, :company_name, :email)
                        """)
                        db.session.execute(insert_query, {"org_nr": org_nr, "company_name": company_name, "email": email})
                    db.session.commit()
                    print(f"✅ Emails inserted into database for org_nr: {org_nr}")

                last_id = row_id

            # Only check process_running if not force_run
            if not force_run and not instance.process_running:
                print("🔴 Exiting loop as process_running is False.")
                break

        print("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        print(f"❌ Feil i search_emails_and_display(): {str(e)}")
        db.session.rollback()
        return False

@api6_blueprint.route('/start_process_google', methods=['POST'])
def start_process_google():
    instance = GoogleKse.get_instance()

    with process_lock:
        if instance.process_running:
            return jsonify({"status": "Prosess kjører allerede"}), 400

        instance.process_running = True
        print(f"🔵 process_running is {instance.process_running}")
        print("Prosess starter...")

        def background_search():
            from src.PyFiles.app import app  # Pass på at dette ikke skaper sirkulær import!
            try:
                with app.app_context(): 
                    print("🔵 background_search() started.")
                    result = search_emails_and_display(force_run=True)  # Added force_run=True
                    if result:
                        print("✅ background_search() completed successfully.")
                    else:
                        print("⚠️ background_search() encountered an issue.")
            except Exception as e:
                print(f"❌ Feil ved prosessstart i background_search(): {str(e)}")
            finally:
                with process_lock:
                    instance.process_running = False
                print("🔴 background_search() finished. process_running set to False.")

        threading.Thread(target=background_search, daemon=True).start()

    return jsonify({"status": "Prosess startet og kjører i bakgrunnen."}), 200

@api6_blueprint.route('/stop_process_google', methods=['POST'])
def stop_process_google():
    instance = GoogleKse.get_instance()
    
    with process_lock:
        if not instance.process_running:
            return jsonify({"status": "Process was not running"}), 200
        try:
            instance.process_running = False
            print("Prosessen er stoppet.")
            return jsonify({"status": "Process stopped"}), 200
        except Exception as e:
            instance.process_running = True
            print(f"Feil ved stopp prosess: {str(e)}")
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500
