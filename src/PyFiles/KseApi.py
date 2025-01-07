import time
import requests
import pyodbc  # For å koble til databasen
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify, Blueprint
import re

# Flask-app
api3_blueprint = Blueprint('api3', __name__)

# Konfigurasjon for Selenium
chrome_service = Service('C:\\Users\\Krist\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--lang=en-US")

# Konfigurasjon for databaseforbindelse
connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=(localdb)\\MSSQLLocalDB;"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
)

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
        driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
        driver.get(url)
        time.sleep(5)  # Bytt gjerne med WebDriverWait for bedre ytelse
        page_source = driver.page_source
        emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source))
        driver.quit()
        return list(emails)
    except Exception as e:
        print(f"Feil ved uthenting av e-post fra {url}: {e}")
        return []

# Funksjon for å søke etter firmaer fra databasen og oppdatere e-post
def search_and_update_emails_in_db_batch():
    try:
        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            query = """
            SELECT [org_nr], [firmanavn], [postnummer], [sted]
            FROM [FirmaListe].[dbo].[FullListe]
            WHERE [e_post] IS NULL AND [e_post2] IS NULL
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            updates = []
            for row in rows:
                org_nr, company_name, postal_code, postal_place = row

                search_query = f'"{company_name}" "{postal_code}" "{postal_place}" "Norge" -groups -posts -photos -type=3 '
                print(f"Søker med query: {search_query}")

                search_results = google_custom_search(search_query)
                all_emails = []
                for url in search_results:
                    emails = extract_email_selenium(url)
                    all_emails.extend(emails)

                unique_emails = set(all_emails)
                email_list = list(unique_emails)

                e_post_update = email_list.pop(0) if email_list else None
                if e_post_update:
                    updates.append((e_post_update, org_nr))
                    print(f"Oppdaterer: Org.nr {org_nr}, e_post: {e_post_update}")
                else:
                    print(f"Ingen e-poster funnet for Org.nr {org_nr}.")

            if updates:
                update_query = "UPDATE [FirmaListe].[dbo].[underenheter] SET [e_post] = ? WHERE [org_nr] = ?"
                cursor.executemany(update_query, updates)
                print(f"{len(updates)} oppdateringer utført.")
    except Exception as e:
        print(f"Feil: {e}")

# Flask-endepunkt for oppdatering
@api3_blueprint.route('/update_emails', methods=['POST'])
def update_emails_endpoint():
    try:
        search_and_update_emails_in_db_batch()
        return jsonify({"status": "Emails updated successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"En feil oppstod: {str(e)}"}), 500

