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

api5_blueprint = Blueprint('api5', __name__)
CORS(api5_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])
process_lock = Lock()
_instance = None  # Singleton instance
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

class Kseapi1881:
    def __init__(self):
        self.process_running = True
        self.logger = logging.getLogger(__name__)
        
    @classmethod
    def get_instance(cls):
        global _instance
        if _instance is None:
            _instance = cls()
        return _instance
        
    def start(self):
        self.process_running = True
        self.logger.info("[START] Process started")
        
    def stop(self):
        self.process_running = False
        self.logger.info("[STOP] Process stopped by user")
        
    def check_stop(self, force_run=False):
        if os.path.exists(STOP_FLAG_FILE):
            self.logger.info("[STOP] Stop flag detected, stopping process")
            self.process_running = False
            return True
            
        if not force_run and not self.process_running:
            self.logger.info("[STOP] Process stopped by user")
            return True
        return False

# Initialize Chrome options
chromedriver_autoinstaller.install()
driver_path = os.getenv('CHROMEDRIVER_PATH') or chromedriver_autoinstaller.install()
chrome_service = Service(driver_path)
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

API_KEY = "AIzaSyAykkpA2kR9UWYz5TkjjTdLzgr4ek3HDLQ"
CSE_ID = "432c6f0a821194e10"

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

def search_emails_and_display(batch_size=5, force_run=False):
    instance = Kseapi1881.get_instance()
    try:
        print(f"🔵 process_running is {instance.process_running}")
        print("🔵 search_emails_and_display() started.")
        
        last_id = 0
        
        while True:
            if instance.check_stop(force_run):
                print("🔴 Process stopped, exiting...")
                break

            print(f"🟡 Fetching batch starting from last_id: {last_id}")
            
            # Bruker SQLAlchemy tekst-spørring med korrekt PostgreSQL-syntaks
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
        print(f"❌ Error in search_emails_and_display(): {str(e)}")
        db.session.rollback()
        return False

@api5_blueprint.route('/start_process', methods=['POST'])
def start_process_1881():
    instance = Kseapi1881.get_instance()

    with process_lock:
        if instance.process_running:
            return jsonify({"status": "Prosess kjører allerede"}), 400

        instance.start()
        print(f"🔵 process_running is {instance.process_running}")
        print("Prosess starter...")

        def background_search():
            from src.PyFiles.app import app
            try:
                with app.app_context(): 
                    print("🔵 Bakgrunnssøk startet.")
                    result = search_emails_and_display(force_run=True)
                    if result:
                        print("✅ Bakgrunnssøk fullført.")
                    else:
                        print("⚠️ Bakgrunnssøk møtte et problem.")
            except Exception as e:
                print(f"❌ Feil ved prosessstart i bakgrunnssøk: {str(e)}")
            finally:
                with process_lock:
                    instance.stop()
                print("🔴 Bakgrunnssøk avsluttet. process_running satt til False.")

        threading.Thread(target=background_search, daemon=True).start()

    return jsonify({"status": "Prosess startet og kjører i bakgrunnen."}), 200

@api5_blueprint.route('/stop_process_1881', methods=['POST'])
def stop_process_1881():
    instance = Kseapi1881.get_instance()
    
    with process_lock:
        if not instance.process_running:
            return jsonify({"status": "Prosessen var ikke i gang (allerede stoppet)."}), 200
        try:
            instance.stop()
            print("Prosessen er stoppet.")
            return jsonify({"status": "Prosessen er stoppet."}), 200
        except Exception as e:
            print(f"Feil ved stopp prosess: {str(e)}")
            return jsonify({"status": f"Feil ved stopp av prosess: {str(e)}"}), 500
