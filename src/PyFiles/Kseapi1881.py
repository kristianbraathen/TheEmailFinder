import time
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint, request
from flask_cors import CORS
import re
from threading import Lock
import chromedriver_autoinstaller
import os
import threading

api5_blueprint = Blueprint('api5', __name__)
CORS(api5_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])
process_lock = Lock()
process_running = False
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

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

def search_emails_and_display(batch_size=5):
    global process_running
    try:
        print(f"🔵 process_running is {process_running}")
        print("🔵 search_emails_and_display() started.")
        
        last_id = 0
        
        while True:
            print(f"🟡 Fetching batch starting from last_id: {last_id}")
            
            # Bruker SQLAlchemy tekst-spørring med korrekt PostgreSQL-syntaks
            query = text(f"""
                SELECT id, Org_nr, Firmanavn
                FROM imported_table
                WHERE Status = 'aktiv selskap' AND E_post_1 IS NULL AND id > :last_id
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
                if not process_running:
                    print("🔴 Prosessen er stoppet av brukeren.")
                    break

                row_id, org_nr, company_name = row
                print(f"🔍 Processing org_nr: {org_nr}, company_name: {company_name}")

                search_query = f'"{company_name}" "Norge"'
                print(f"🔍 Søker med query: {search_query}")

                search_results = google_custom_search(search_query)
                all_emails = []
                for url in search_results:
                    if not process_running:
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
                            INSERT INTO email_results (Org_nr, company_name, email)
                            VALUES (:org_nr, :company_name, :email)
                        """)
                        db.session.execute(insert_query, {"org_nr": org_nr, "company_name": company_name, "email": email})
                    db.session.commit()
                    print(f"✅ Emails inserted into database for org_nr: {org_nr}")

                last_id = row_id

            if not process_running:
                print("🔴 Exiting loop as process_running is False.")
                break

        print("✅ search_emails_and_display() completed.")
        return True

    except Exception as e:
        print(f"❌ Feil i search_emails_and_display(): {str(e)}")
        db.session.rollback()
        return False

@api5_blueprint.route('/start_process', methods=['POST'])
def start_process_1881():
    global process_running
    with process_lock:
        if process_running:
            return jsonify({"status": "Process is already running"}), 400
        process_running = True
        print("Prosess starter...")
        def background_search():
            try:
                search_emails_and_display()
            except Exception as e:
                print(f"Feil ved prosessstart: {str(e)}")
            finally:
                global process_running
                with process_lock:
                    process_running = False
                print("Prosessen er ferdig, process_running satt tilbake til False.")
        threading.Thread(target=background_search, daemon=True).start()
    return jsonify({"status": "Process started and search running in background."}), 200

@api5_blueprint.route('/stop_process_1881', methods=['POST'])
def stop_process_1881():
    global process_running
    with process_lock:
        if not process_running:
            return jsonify({"status": "Process was not running (already stopped)."}), 200
        try:
            process_running = False
            print("Prosessen er stoppet.")
            return jsonify({"status": "Process stopped successfully."}), 200
        except Exception as e:
            process_running = True
            print(f"Feil ved stopp prosess: {str(e)}")
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500
