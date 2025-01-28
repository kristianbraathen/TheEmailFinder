import time
import requests
import pyodbc  # For å koble til databasen
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint, request
import re
from urllib.parse import unquote
from threading import Lock
from Db import db
import chromedriver_autoinstaller
import os
import tempfile

# Flask-app
api3_blueprint = Blueprint('api3', __name__)
process_lock = Lock()
process_running = False  # Global flag to track the process state 
connection_string = os.getenv('DATABASE_CONNECTION_STRING')

#Install ChromeDriver automatically if not set
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
chrome_options.binary_location = os.getenv('CHROME_BIN')  # Path to the Chrome binary (if needed)

# Set Chrome options
# Headless mode (if running in a server or CI environment)
chrome_options.add_argument("--headless=new")

# General settings for server/container environments
chrome_options.add_argument("--disable-gpu")  # Disable GPU (important in headless environments)
chrome_options.add_argument("--no-sandbox")  # Avoid sandboxing issues in containers
chrome_options.add_argument("--disable-extensions")  # Disable extensions
chrome_options.add_argument("--disable-dev-shm-usage")  # Address shared memory issues in Docker
chrome_options.add_argument("--disable-software-rasterizer")  # Disable software rendering

# Language and regional settings
chrome_options.add_argument("--lang=en-NO")  # Norwegian language

# Safe rendering mode
chrome_options.add_argument("--enable-unsafe-swiftshader")  # SwiftShader for software rendering fallback (optional)

# Experimental: User data settings
# This is what you currently have
chrome_options.add_argument("--disable-user-data-dir")  # Ensure no specific user profile is loaded

# Add this to avoid DBus-related errors
chrome_options.add_argument("--disable-dev-tools")  # Disable developer tools
chrome_options.add_argument("--remote-debugging-port=0")  # Prevent remote debugging

# Add extra logging for debugging purposes
chrome_options.add_argument("--log-level=3")  # Suppress logs (INFO, WARNING, and ERROR logs)

# Optional: Disable default apps
chrome_options.add_argument("--disable-default-apps")

# Ensure a unique, isolated session is created
chrome_options.add_argument("--disable-session-crashed-bubble")  # Disable "restore session" dialog
# Initialize the WebDriver
driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

# Google Custom Search API-konfigurasjon
API_KEY = "AIzaSyDX42Nl71H81zGkm8_4WDzkLv26N9Vpn_E"
CSE_ID = "05572ab81b7254d58"

# Funksjon for å gjøre et søk via Google Custom Search API
def google_custom_search(query):
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CSE_ID}&gl=no&lr=lang:no"
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
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options, executable_path=driver_path)
        driver.get(url)
        time.sleep(5)  # Bytt gjerne med WebDriverWait for bedre ytelse
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
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            query = """
            SELECT [Org.nr], [firmanavn]
            FROM [dbo].[imported_table]
            WHERE status = 'aktiv selskap' AND [E-post 1] IS NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            global process_running
            results = []
            for row in rows:
                if not process_running:  # Sjekk om prosessen skal stoppes
                    print("Prosessen er stoppet.")
                    break

                org_nr, company_name = row

                # Google Custom Search med firmanavn og Norge
                search_query = f'"{company_name}" "Norge" -groups -posts -photos -photo -videos -type=3'
                print(f"Søker med query: {search_query}")
                
                search_results = google_custom_search(search_query)
                all_emails = []
                for url in search_results:
                    if not process_running:  # Sjekk om prosessen skal stoppes
                        print("Prosessen er stoppet.")
                        break
                    emails = extract_email_selenium(url)
                    all_emails.extend(emails)

                # Fjern duplikater fra e-postene
                unique_emails = set(all_emails)
                email_list = list(unique_emails)

                # Lagre resultatene
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

# Flask-endepunkt for å søke etter e-poster
@api3_blueprint.route('/search_emails', methods=['GET'])
def search_emails_endpoint():
    global process_running
    if not process_running:  # Kontroller før du setter prosessen som kjørende
        return jsonify({"error": "Prosessen er stoppet, kan ikke hente e-poster."}), 400

    process_running = True  # Sett prosessen som kjørende
    try:
        results = search_emails_and_display()
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500
@api3_blueprint.route("/update_email", methods=["POST"])
def update_email():
    try:
        # Parse the request JSON
        data = request.get_json()
        org_nr = data.get("org_nr")
        email = data.get("email")

        if not org_nr or not email:
            return jsonify({"error": "Org.nr and email are required."}), 400

        # Perform the update in the database
        query = f"UPDATE [dbo].[imported_table] SET [e_post 1] = :email WHERE [Org.nr] = :org_nr"
        db.session.execute(query, {"email": email, "org_nr": org_nr})
        db.session.commit()

        return jsonify({"status": "E-post oppdatert!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500

@api3_blueprint.route('/start_process', methods=['POST'])
def start_process():
    global process_running
    with process_lock:  # Sikrer trådtrygg tilgang
        if process_running:
            return jsonify({"status": "Process is already running"}), 400
        try:
            process_running = True
            # Start prosessen her
            return jsonify({"status": "Process started successfully"}), 200
        except Exception as e:
            process_running = False
            return jsonify({"status": f"Error starting process: {str(e)}"}), 500

@api3_blueprint.route('/stop_process', methods=['POST'])
def stop_process():
    global process_running
    with process_lock:
        if not process_running:
            return jsonify({"status": "Process is not running"}), 400
        try:
            process_running = False
            # Stopp prosessen her
            return jsonify({"status": "Process stopped successfully"}), 200
        except Exception as e:
            process_running = True
            return jsonify({"status": f"Error stopping process: {str(e)}"}), 500
