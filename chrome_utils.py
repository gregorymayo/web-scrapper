import os
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Check the ChromeDriver path
def check_chromedriver_path(path):
    if os.path.exists(path):
        print(f"ChromeDriver path is correct. This is the path of your ChromeDriver: {path}")
    else:
        print(f"ChromeDriver path is incorrect. Please check your path: {path}")
        sys.exit()

# Extra setup for ChromeDriver
def setup_driver(path):
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(path)
    return webdriver.Chrome(service=service, options=options)
