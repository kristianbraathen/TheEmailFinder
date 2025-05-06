import time
import requests
import psycopg2
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint, request
from .Db import db
import re
from urllib.parse import unquote
from threading import Lock
from sqlalchemy.sql import text
import chromedriver_autoinstaller
import os
import tempfile


# Flask-app
api5_blueprint = Blueprint('api5', __name__)
CORS(api5_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])
process_lock = Lock()
process_running = False  # Global flag to track the process state
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

# Install ChromeDriver automatically if not set
chromedriver_autoinstaller.install()

# Get ChromeDriver path from environment variable (if set)
driver_path = os.getenv('CHROMEDRIVER_PATH')

# If CHROMEDRIVER_PATH is not set, use the default path provided by chromedriver_autoinstaller
if not driver_path:
    driver_path = chromedriver_autoinstaller.install()

# Konfigurasjon for Selenium
chrome_service = Service(driver_path)
chrome_options = Options()

# Specify the location of your Chrome binary (optional if it's in the default path)
chrome_path = os.getenv('CHROME_BIN') or "/usr/bin/google-chrome"
if not os.path.exists(chrome_path):
    chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

# Set Chrome options
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
chrome_options.add_argument("--disable-dev-shm-usage")

# Google Custom Search API-konfigurasjon
API_KEY = "AIzaSyAykkpA2kR9UWYz5TkjjTdLzgr4ek3HDLQ"
CSE_ID = "432c6f0a821194e10"

def create_driver():
    return webdriver.Chrome(service=chrome_service, options=chrome_options)

# Funksjon for å gjøre et søk via Google Custom Search API
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

# Funksjon for å trekke ut e-poster fra nettside
def extract_email_selenium(url):
    try:
        driver = create_driver()  # Opprett WebDriver her, ikke globalt
        driver.get(url)
        time.sleep(5)  
        page_source = driver.page_source
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
        driver.quit()
        return list(emails)
    except Exception as e:
        print(f"Feil ved uthenting av e-post fra {url}: {e}")
        return []

# Funksjon for å søke etter firmaer fra databasen og vise e-poster
def search_emails_and_display():
    try:
        with psycopg2.connect(connection_string) as conn:
            cursor = conn.cursor()
            query = """
            SELECT "Org_nr", Firmanavn
            FROM imported_table
            WHERE Status = 'aktiv selskap' AND "E_post_1" IS NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            global process_running
            results = []
            for row in rows:
                if not process_running:  
                    print("Prosessen er stoppet.")
                    break

                org_nr, company_name = row
                search_query = f'"{company_name}" "Norge" '
                print(f"Søker med query:{search_query}")
                
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
                    results.append({
                        "org_nr": org_nr,
                        "company_name": company_name,
                        "emails": email_list
                    })
            return results

    except Exception as e:
        print(f"Feil: {e}")
        return []

@api5_blueprint.route('/search_emails', methods=['GET'])
def search_emails_endpoint():
    global process_running
    if process_running:  # Hvis prosessen allerede kjører, returner feil
        return jsonify({"error": "Prosessen er stoppet, kan ikke hente e-poster."}), 400

    process_running = True  # Sett prosessen som kjørende
    try:
        results = search_emails_and_display()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500
    finally:
        process_running = False  # Tilbakestill flagget for å tillate nye søk

@api5_blueprint.route("/update_email", methods=["POST"])
def update_email():
    data = request.get_json()
    org_nr = data.get("org_nr")
    email = data.get("email")

    if not org_nr or not email:
        return jsonify({"error": "Missing org_nr or email"}), 400

    try:
        query = text(
            'UPDATE imported_table SET "E_post_1" = :email WHERE "Org_nr" = :org_nr'
        )
        db.session.execute(query, {"email": email, "org_nr": org_nr})
        db.session.commit()

        return jsonify({"status": "E-post oppdatert!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500

@api5_blueprint.route('/delete_stored_result', methods=['POST'])
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

@api5_blueprint.route('/start_process', methods=['POST'])
def start_process_1881():
    global process_running
    with process_lock:  
        if process_running:
            return jsonify({"status": "Process is already running"}), 400
        try:
            process_running = True
            return jsonify({"status": "Process started successfully"}), 200
        except Exception as e:
            process_running = False
            return jsonify({"status": f"Error starting process: {str(e)}"}), 500

@api5_blueprint.route('/stop_process', methods=['POST'])
def stop_process_1881():
    global process_running
    with process_lock:
        if not process_running:
            return jsonify({"status": "Process is not running"}), 400
        try:
            process_running = False
            return jsonify({"status": "Process stopped successfully"}), 200
        except Exception as e:
            process_running = True
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500
