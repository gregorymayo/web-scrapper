# Halodoc Homelab Packages Scraper
This project is a web scraping tool designed to extract data from the Halodoc Homelab packages page. The scraper uses Selenium and ChromeDriver to navigate and extract data from the web page. 
Additionally, it uses the Requests library to interact with Google search to find the most accurate result based on the extracted titles and further scrapes data from the resulting URLs.

# Installation
## Prerequisites
Python 3.6+
Google Chrome browser
ChromeDriver (compatible with your version of Chrome)

# Features
- Extracts titles from the Halodoc Homelab packages page.
- Uses Google search to find the most accurate results based on extracted titles.
- Navigates to the resulting URLs to scrape additional data.
- Combines Selenium for web interaction and Requests for HTTP requests.
