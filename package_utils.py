import requests
import time
import re

from bs4 import BeautifulSoup

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

# Initialize desired_order column title with known keys in the desired order
desired_order = [
    "Judul", "Hasil", "Harga Baru", "Harga Lama", "Tentang Paket Ini",
    "Meliputi 2 Tes", "Meliputi 3 Tes", "Meliputi 4 Tes", "Meliputi 5 Tes",
    "Meliputi 6 Tes", "Meliputi 11 Tes", "Meliputi 15 Tes", "Persiapan Wajib",
    "Sampel Yang Diambil", "Syarat & Ketentuan", "URL"
]

# Function to extract data
def extract_packages(driver):
    packages = []
    elements = driver.find_elements(By.CLASS_NAME, 'hd-base-horizontal-card')
    for element in elements:
        try:
            title = element.find_element(By.CLASS_NAME, 'hd-base-horizontal-card__title').text
            packages.append({'title': title, 'url': None})
        except Exception as e:
            print(f"Error extracting package: {e}")
    return packages


# Function to search for URLs using Google
def find_package_url(package_name):
    search_query = f"{package_name} site:{config.HALODOC_PACKAGE_SHORT_URL}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(f"https://www.google.com/search?q={search_query}", headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        result = soup.find('div', class_='g').find('a', href=True)
        if result:
            return result['href']
    return None

# Function for the retry mechanism
def retry_find_package_url(package_name, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return find_package_url(package_name)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    print(f"All {retries} attempts failed for {package_name}")
    return None

def process_packages(driver, packages):
    all_package_info = []
    for package in packages:
        if package['url'] is not None:
            print(f"Processing {package['title']}")
            try:
                response = requests.get(package['url'])
                response.raise_for_status()
                html_content = response.content
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError) as e:
                print(f"Error fetching URL for {package['title']}: {e}")
                continue

            soup = BeautifulSoup(html_content, 'html.parser')
            try:
                title = soup.find('div', class_="item").get_text(strip=True) if soup.find('div', class_='item') else None
                new_price = soup.find('div', class_="price--new-price").strong.get_text(strip=True) if soup.find('div', class_='price--new-price') else None
                old_price = soup.find('p', class_="price--old-price").get_text(strip=True) if soup.find('p', 'price--old-price') else None
                result_test = soup.find('div', class_="description").get_text(strip=True) if soup.find('div', 'description') else None
            except AttributeError:
                print(f"Error: Required fields were not found for {package['title']}.")
                continue

            package_info = {
                "Judul": title,
                "Harga Baru": new_price,
                "Harga Lama": old_price,
                "Hasil": result_test,
                "URL": package['url']
            }

            info_headers = soup.find_all('span', class_='info-header-title')
            for header in info_headers:
                section_title = header.get_text(strip=True)
                description = header.find_next('div', class_='info-description')
                if description:
                    texts = [tag.get_text(strip=True, separator=' ') for tag in description.find_all(['p', 'li']) if tag.get_text(strip=True)]
                    package_info[section_title] = ' '.join(texts)
                # Additional code to extract test names for sections starting with "Meliputi"
                if re.match(r'^Meliputi \d+ Tes$', section_title):
                    try:
                        driver.get(package['url'])
                        wait = WebDriverWait(driver, 10)
                        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'info-header-title')))
                        elements = driver.find_elements(By.CLASS_NAME, 'package-tests_content-detail')
                        test_details = []
                        for element in elements:
                            driver.execute_script("arguments[0].click();", element)
                            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, 'test-info-header_title')))
                            test_title = driver.find_element(By.CLASS_NAME, 'test-info-header_title').text
                            test_content = driver.find_element(By.CLASS_NAME, 'test-info_content').text
                            test_details.append(f"{test_title}: {test_content}")
                        package_info[section_title] = ' '.join(test_details)
                    except Exception as e:
                        print(f"Error processing tests for {package['title']}: {e}")

            all_package_info.append(package_info)
            print(f"Done processing {package['title']}")
    return all_package_info
