from ssl import Options
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
import gradio as gr
from flask import Flask, jsonify, Blueprint, request

api4_blueprint = Blueprint('api4', __name__)
# Konfigurer ChromeDriver
options = Options()
options.binary_location = r'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
chrome_service = Service('C:\\Users\\Krist\\chromedriver-win64\\chromedriver-win64\\chromedriver.exe')

# Sett opp Chrome med nødvendige innstillinger
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-webusb")
options.add_argument("--disable-extensions")
options.add_argument("--enable-unsafe-swiftshader")
options.add_argument("--disable-gpu")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--use-gl=swiftshader")
options.add_argument("--disable-webgl")
options.add_argument("--disable-webgpu")
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")




# options.add_argument('--headless')  # Fjern for å teste med GUI

driver = webdriver.Chrome(service=chrome_service, options=options)

def find_emails_on_facebook(company_name):
    try:
        # Google-søk etter firma på Facebook
        search_url = f"https://www.google.com/search?q=site:facebook.com+OR+site:1881.no+{company_name}&hl=no&gl=no&cr=countryNO"
        
        driver.get(search_url)
        # Vent på at søkeresultater skal laste inn
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH,"//h3"))
        )
        
        # Finn det første søkeresultatet
        first_result = driver.find_element(By.XPATH, "//h3")
        
        # Forsøk å klikke med ulike strategier
        try:
            # Rull til elementet
            driver.execute_script("arguments[0].scrollIntoView(true);", first_result)
            # Klikk med JavaScript som en sikkerhetskopi
            driver.execute_script("arguments[0].click();", first_result)
        except:
            # Vent på at blokkerende element skal forsvinne
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element((By.CLASS_NAME, "jw8mI"))
            )
            # Flytt musen bort fra overlappende elementer
            action = ActionChains(driver)
            action.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), 0, 0).perform()
            first_result.click()

        # Vent til siden laster inn
        time.sleep(5)

        # Få sidekilden og parse den
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Finn e-postadresser med BeautifulSoup
        emails = set()
        for text in soup.stripped_strings:
            # Bruk regex for å finne e-postadresser i teksten
            found_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            emails.update(found_emails)
        
        return "\n".join(emails) if emails else "Ingen e-poster funnet."
    except Exception as e:
        # Lagre skjermdump for feildiagnose
        driver.save_screenshot("debug_screenshot.png")
        return f"Feil: {e}"
    
@api4_blueprint.route('/search_by_company_name', methods=['GET'])
def search_emails():
    company_name = request.args.get('company_name')
    
    if not company_name:
        return jsonify({"error": "Company name is required."}), 400
    
    # Call the scraping function
    emails = find_emails_on_facebook(company_name)
    
    return jsonify({"emails": emails})

