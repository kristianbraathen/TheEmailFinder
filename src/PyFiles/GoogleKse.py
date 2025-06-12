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
from src.PyFiles.Db import db

api6_blueprint = Blueprint('api6', __name__)
CORS(api6_blueprint, origins=["https://theemailfinder-d8ctecfsaab2a7fh.norwayeast-01.azurewebsites.net"])

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
CSE_ID = "879ff228f5bff4ed9"  # GoogleKse specific CSE ID

class GoogleKse:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleKse, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.process_running = False
            self._provider_type = None
            self._initialized = True

    @property
    def provider_type(self):
        return self._provider_type

    @provider_type.setter
    def provider_type(self, value):
        self._provider_type = value

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def search_company(self, company_name):
        if not self._provider_type:
            raise ValueError("Provider type not set. Please set provider_type before searching.")
        search_query = f'"{company_name}" "Norge"'
        return google_custom_search(search_query)

    def extract_email_selenium(self, url):
        return extract_email_selenium(url)

    def stop(self):
        self.process_running = False

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
