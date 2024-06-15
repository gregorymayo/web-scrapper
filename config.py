from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Access the variables
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')
PACKAGE_URL = os.getenv('PACKAGE_URL')
PACKAGE_SHORT_URL = os.getenv('PACKAGE_SHORT_URL')
OUTPUT_FILE_PATH = os.getenv('OUTPUT_FILE_PATH')