import time
import csv

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config
from chrome_utils import check_chromedriver_path, setup_driver
from package_utils import extract_packages, retry_find_package_url, process_packages, desired_order

# Write data to CSV after collecting all data
def write_to_csv(data, file_path):
    if data:
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=desired_order)
            writer.writeheader()
            for package_info in data:
                writer.writerow(package_info)
            print("Data has been written to CSV.")
    else:
        print("No package information found.")

def main():
    # Check ChromeDriver path
    check_chromedriver_path(config.CHROMEDRIVER_PATH)

    # Initialize ChromeDriver
    driver = setup_driver(config.CHROMEDRIVER_PATH)

    # Open the targeted Web Page URL
    driver.get(config.HALODOC_PACKAGE_URL)

    # Wait for the initial set of elements to load
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'packages-lists')))

    # Find the height of the container that we want to extract the data from
    scroll_container = driver.find_element(By.CSS_SELECTOR, '.cdk-virtual-scroll-viewport')
    last_height = driver.execute_script('return arguments[0].scrollHeight', scroll_container)

    # Initialize initial set of packages and extract data
    all_packages = extract_packages(driver)
    while True:
        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scroll_container)
        time.sleep(2)
        # Extract data after scrolling
        new_packages = extract_packages(driver)
        if new_packages:
            all_packages.extend(new_packages)
        new_height = driver.execute_script('return arguments[0].scrollHeight', scroll_container)
        if new_height == last_height:
            break
        last_height = new_height

    driver.quit()

    # Remove duplicates package if any
    unique_packages = [dict(t) for t in {tuple(d.items()) for d in all_packages}]

    # Find URLs for each package with delay
    for package in unique_packages:
        package['url'] = retry_find_package_url(package['title'])
        print(package)
        time.sleep(5)

    # Initialize service for ChromeDriver to solve connection issue
    driver = setup_driver(config.CHROMEDRIVER_PATH)
    all_package_info = process_packages(driver, unique_packages)

    driver.quit()

    # Ensure all keys in all_package_info are included in desired_order
    for package_info in all_package_info:
        for key in package_info.keys():
            if key not in desired_order:
                desired_order.append(key)

    # Ensure all keys in desired_order exist in each package_info
    for package_info in all_package_info:
        for key in desired_order:
            if key not in package_info:
                package_info[key] = None

    write_to_csv(all_package_info, config.OUTPUT_FILE_PATH)

if __name__ == "__main__":
    main()
