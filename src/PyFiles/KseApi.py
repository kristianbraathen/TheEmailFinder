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

api3_blueprint = Blueprint('api3', __name__)
CORS(api3_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

process_lock = Lock()
process_running = False
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

# Selenium config
chrome_options = Options()
if os.path.exists("/usr/bin/google-chrome"):
    chrome_options.binary_location = "/usr/bin/google-chrome"
else:
    chrome_options.binary_location = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--remote-debugging-port=9222")
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
CSE_ID = "05572ab81b7254d58"

def google_custom_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CSE_ID}&gl=no&lr=lang:no&num=3"
    response = requests.get(url)
    if response.status_code == 200:
        search_results = response.json()
        return [item["link"] for item in search_results.get("items", [])]
    else:
        print(f"Feil ved Google API: {response.status_code} - {response.text}")
        return []

def extract_email_selenium(url):
    try:
        chromedriver_autoinstaller.install()
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        time.sleep(5)
        page_source = driver.page_source
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
        driver.quit()
        return list(emails)
    except Exception as e:
        print(f"Feil ved uthenting av e-post fra {url}: {e}")
        return []

def search_emails_and_display(batch_size=5):
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            last_id = 0
            global process_running

            while True:
                query = f"""
                    SELECT "id", "Org_nr", "Firmanavn"
                    FROM imported_table
                    WHERE "Status" = 'aktiv selskap' AND "E_post_1" IS NULL AND "id" > {last_id}
                    ORDER BY "id" ASC
                    LIMIT {batch_size}
                """
                cursor.execute(query)
                rows = cursor.fetchall()
                if not rows:
                    print("Ingen flere rader å behandle.")
                    break

                print(f"🟡 Behandler batch med {len(rows)} rader (last_id: {last_id}).")
                for row in rows:
                    if not process_running:
                        print("Prosessen er stoppet.")
                        break
                    row_id, org_nr, company_name = row
                    search_query = f'"{company_name}" "Norge"'
                    print(f"Søker med query: {search_query}")
                    search_results = google_custom_search(search_query)
                    all_emails = []
                    for url in search_results:
                        if not process_running:
                            print("Prosessen er stoppet.")
                            break
                        emails = extract_email_selenium(url)
                        all_emails.extend(emails)
                    unique_emails = set(all_emails)
                    for email in unique_emails:
                        insert_query = """
                        INSERT INTO [dbo].[email_results] ([Org_nr], [company_name], [email])
                        VALUES (?, ?, ?)
                        """
                        cursor.execute(insert_query, (org_nr, company_name, email))
                    conn.commit()
                    last_id = row_id
                if not process_running:
                    break
        return True
    except Exception as e:
        print(f"Feil: {e}")
        return False

@api3_blueprint.route('/start_process_kse', methods=['POST'])
def start_process_kse():
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

@api3_blueprint.route('/stop_process_kse', methods=['POST'])
def stop_process_kse():
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
