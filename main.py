import requests
import time
import random
import json
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from googlesearch import search
import csv

# Initialize the WebDriver
chrome_driver_path = '/Users/gregorymayo/chromedriver-mac-x64/chromedriver'
service = Service(chrome_driver_path)

options = Options()
options.add_argument('--disable-blink-features=AutomationControlled')  # Disables detection of automation
options.add_argument('--headless')  # Run in headless mode if you don't need a GUI
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=service, options=options)
driver.get('https://www.halodoc.com/homelab/packages')

# Wait for the initial set of elements to load
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'packages-lists')))

# Function to extract data
def extract_packages(driver, count):
    packages = []
    # if count == 3:
    #     page_source = driver.page_source
    #     soup = BeautifulSoup(page_source, 'html.parser')
        # print(soup.prettify())

    elements = driver.find_elements(By.CLASS_NAME, 'hd-base-horizontal-card')  # Update this class to the correct one
    for element in elements:
        try:
            title = element.find_element(By.CLASS_NAME, 'hd-base-horizontal-card__title').text
            # subtitle = element.find_element(By.CLASS_NAME, 'hd-base-horizontal-card__subtitle').text
            # doctor_label = element.find_element(By.CLASS_NAME, 'doctor-card__label').text
            # price = element.find_element(By.CLASS_NAME, 'price').text
            # old_price = element.find_element(By.CLASS_NAME, 'price--old-price').text if element.find_elements(By.CLASS_NAME, 'price--old-price') else None
            packages.append({
                'title': title,
                # 'subtitle': subtitle,
                # 'doctor_label': doctor_label,
                # 'price': price,
                # 'old_price': old_price,
                'url': None
            })
        except Exception as e:
            print(f"Error extracting package: {e}")
    return packages

# Scroll and extract data
all_packages = []
# last_height = driver.execute_script("return document.body.scrollHeight")
scroll_container = driver.find_element(By.CSS_SELECTOR, '.cdk-virtual-scroll-viewport')
last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
# print("Initial Height:", last_height)
count = 1

# Extract initial set of packages
all_packages = extract_packages(driver, count)

while True:
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
    time.sleep(2)  # Wait for the new data to load
    # driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.END)
    # time.sleep(2)  # Wait for the new data to load
    # print(count)
    new_packages = extract_packages(driver, count)
    count += 1
    if new_packages:
        all_packages.extend(new_packages)
    # new_height = driver.execute_script("return document.body.scrollHeight")
    new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_container)
    # print("New Height:", new_height)
    if new_height == last_height:
        break
    last_height = new_height

# Close the driver
driver.quit()

# Remove duplicates if any
unique_packages = [dict(t) for t in {tuple(d.items()) for d in all_packages}]

# Function to search for URLs using Google with retry mechanism
def find_package_url(package_name):
    # Open Google
    driver.get("https://www.google.com")
    search_box = driver.find_element(By.NAME, "q")

    # Enter the search query
    search_query = f"{package_name} site:halodoc.com/homelab/packages"
    search_box.send_keys(search_query + Keys.RETURN)

    # Wait for results and try to extract the first result URL
    time.sleep(3)  # Adjust time based on your network speed and system performance
    try:
        # Attempt to find the first search result's URL
        result = driver.find_element(By.CSS_SELECTOR, 'div.g a')
        url = result.get_attribute('href')
        return url
    except Exception as e:
        print(f"Failed to find URL for {package_name}: {str(e)}")
        return None
    # base_url = "https://www.halodoc.com/homelab/packages/"
    # query = f"https://www.halodoc.com/homelab/packages/ {package_name}"
    # retries = 3
    # for i in range(retries):
    #     try:
    #         results = search(query, num_results=10)  # Increase the number of results to check
    #         for url in results:
    #             if url.startswith(base_url):
    #                 return url
    #         print(f"No valid URLs found in search results for {package_name}. Retrying {i + 1}/{retries}...")
    #         time.sleep(5 + i * 5)  # Exponential backoff
    #     except requests.exceptions.HTTPError as e:
    #         if e.response.status_code == 429:
    #             print(f"Rate limited. Retrying {i + 1}/{retries}...")
    #             time.sleep(5 + i * 10)  # Exponential backoff
    #         else:
    #             print(f"HTTP error: {e}")
    #             break
    #     except Exception as e:
    #         print(f"Error searching for URL: {e}")
    #         break
    # return None
def retry_find_package_url(package_name, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return find_package_url(package_name)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    print(f"All {retries} attempts failed for {package_name}")
    return None

# Find URLs for each package with delay
for package in unique_packages:
    package['url'] = retry_find_package_url(package['title'])
    print(package)
    time.sleep(5)

all_package_info = []

for package in unique_packages:
    if(package['url']) is not None:
        driver.get(package['url'])
        wait = WebDriverWait(driver, 10)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "item")))
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "price--new-price")))

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        try:
            title = soup.find('div', class_="item").get_text(strip=True)
            new_price = soup.find('div', class_="price--new-price").strong.get_text(strip=True)
            old_price = soup.find('p', class_="price--old-price").get_text(strip=True)
        except AttributeError:
            print(f"Error: Required fields were not found for {package}.")
            continue  # Skip to the next package if there's an error

        package_info = {

            "Title": title,
            "New Price": new_price,
            "Old Price": old_price
        }

        info_headers = soup.find_all('span', class_='info-header-title')
        for header in info_headers:
            section_title = header.get_text(strip=True)
            description = header.find_next('div', class_='info-description')

            if description:
                texts = [tag.get_text(strip=True, separator=' ') for tag in description.find_all(['p', 'li']) if tag.get_text(strip=True)]
                package_info[section_title] = ' '.join(texts)

        package_info["url"] = package
        all_package_info.append(package_info)

driver.quit()

# Write data to CSV after collecting all data
with open('/Users/gregorymayo/Downloads/output.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = list(all_package_info[0].keys())  # Ensure all keys are included
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for package_info in all_package_info:
        writer.writerow(package_info)
    print("Data has been written to CSV.")