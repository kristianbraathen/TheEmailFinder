import time
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint, request, current_app
from flask_cors import CORS
import re
from urllib.parse import unquote
from threading import Lock
from .Db import db, get_db_connection
import chromedriver_autoinstaller
import os
import tempfile
from sqlalchemy.sql import text
import threading

# Flask-app
api6_blueprint = Blueprint('api6', __name__)
CORS(api6_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])
process_lock = Lock()
process_running = False  # Global flag to track the process state

# Install ChromeDriver automatically if not set
connection_string = os.getenv('DATABASE_CONNECTION_STRING')
driver_path = chromedriver_autoinstaller.install()

# Konfigurasjon for Selenium
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
        time.sleep(5)
        page_source = driver.page_source
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
        driver.quit()
        return list(emails)
    except Exception as e:
        print(f"Feil ved uthenting av e-post fra {url}: {e}")
        return []

def search_emails_and_display(batch_size=5):
    """
    Processes emails in small batches using the `id` column for ordering.
    """
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
                    email_list = list(unique_emails)

                    if email_list:
                        for email in email_list:
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

@api6_blueprint.route('/search_emails', methods=['GET'])
def search_emails_endpoint():
    global process_running

    with process_lock:
        print(f"Prosesstart - process_running: {process_running}")
        if process_running:
            return jsonify({"error": "Prosessen er stoppet, kan ikke hente e-poster."}), 400

        process_running = True

    try:
        result = search_emails_and_display()
        return jsonify({"status": "Done" if result else "Error"}), 200
    except Exception as e:
        print(f"Feil under behandling: {str(e)}")
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500
    finally:
        with process_lock:
            process_running = False
            print(f"Prosesstopp - process_running: {process_running}")

@api6_blueprint.route("/update_email", methods=["POST"])
def update_email():
    try:
        data = request.get_json()
        org_nr = data.get("org_nr")
        email = data.get("email")

        if not org_nr or not email:
            return jsonify({"error": "Org.nr and email are required."}), 400

        query = text(
            'UPDATE imported_table SET "E_post_1" = :Email WHERE "Org_nr" = :Org_nr'
        )
        db.session.execute(query, {"email": email, "org_nr": org_nr})
        db.session.commit()

        return jsonify({"status": "E-post oppdatert!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500

@api6_blueprint.route('/delete_stored_result', methods=['POST'])
def delete_stored_result():
    data = request.get_json()
    org_nr = data.get("org_nr")

    if not org_nr:
        return jsonify({"status": "Organisasjonsnummer mangler"}), 400

    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM email_results WHERE "Org_nr" = %s
            """, (org_nr,))
            conn.commit()

        return jsonify({"status": f"Slettet org.nr {org_nr}"}), 200

    except Exception as e:
        print(f"Feil ved sletting av org.nr {org_nr}: {e}")
        return jsonify({"status": "Feil ved sletting"}), 500

@api6_blueprint.route('/start_process_google', methods=['POST'])
def start_process_google():
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

@api6_blueprint.route('/stop_process_google', methods=['POST'])
def stop_process_google():
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
