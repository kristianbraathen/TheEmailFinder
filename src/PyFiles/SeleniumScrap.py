from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time
from flask import Flask, jsonify, Blueprint, request
import chromedriver_autoinstaller  # Automatically installs the correct chromedriver version
import os

api4_blueprint = Blueprint('api4', __name__)

# Configure ChromeDriver using chromedriver-autoinstaller
chromedriver_autoinstaller.install()  

@api4_blueprint.route('/search_by_company_name', methods=['GET'])
def search_emails():
    company_name = request.args.get('company_name')
    
    if not company_name:
        return jsonify({"error": "Company name is required."}), 400
    
    # Call the scraping function
    emails = find_emails_on_facebook(company_name)
    
    return jsonify({"emails": emails})

def find_emails_on_facebook(company_name):
    try:
        # Install and set up ChromeDriver every time the function is called
        chromedriver_autoinstaller.install()

        options = Options()
        chrome_path = os.getenv('CHROME_BIN') or "/usr/bin/google-chrome"
        if not os.path.exists(chrome_path):
            chrome_path = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"

        options.binary_location = chrome_path
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
        options.add_argument('--headless')  # Use headless for production

        driver_path = os.getenv('CHROMEDRIVER_PATH')
        service = Service(driver_path) if driver_path else Service()
        driver = webdriver.Chrome(service=service, options=options)

        # --- Scraping Logic ---
        search_url = f"https://www.google.com/search?q=site:facebook.com+OR+site:1881.no+{company_name}&hl=no&gl=no&cr=countryNO"
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//h3"))
        )

        first_result = driver.find_element(By.XPATH, "//h3")

        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", first_result)
            driver.execute_script("arguments[0].click();", first_result)
        except:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element((By.CLASS_NAME, "jw8mI"))
            )
            action = ActionChains(driver)
            action.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), 0, 0).perform()
            first_result.click()

        time.sleep(5)
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        emails = set()
        for text in soup.stripped_strings:
            found_emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
            emails.update(found_emails)

        return "\n".join(emails) if emails else "Ingen e-poster funnet."
    
    except Exception as e:
        driver.save_screenshot("debug_screenshot.png")
        return f"Feil: {e}"
    
    finally:
        try:
            driver.quit()
        except:
            pass