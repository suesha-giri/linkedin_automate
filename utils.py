import time
import logging
import pickle
import requests

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC


def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("window-size=1366,768")
    chrome_options.add_argument("--disable-extensions")
    # Exclude automation flags to make the browser appear less automated
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # chrome_options.headless = True
    service = Service(executable_path="C:\\Users\\Suesha\\linkedin_bot\\chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def load_cookies(driver, cookie_file="linkedin_cookies.pkl"):
    try:
        with open(cookie_file, "rb") as f:
            cookies = pickle.load(f)

        # Add cookies to the browser
        for cookie in cookies:
            print(cookie)
            driver.add_cookie(cookie)
        return True
    except (FileNotFoundError, EOFError) as e:
        return False


def get_logger(log_file="error.log"):
    """"""
    logger = logging.getLogger(__name__)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)

        # Create a file handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')

        # Create a logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        logger.addHandler(file_handler)


    return logger


def wait_for_element(driver, by, value):
    """Helper method to wait for an element."""
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((by, value))
    )
    return element


def ensure_internet_connection():
    while True:
        try:
            requests.get("https://www.facebook.com/", timeout=5)
        except requests.ConnectionError:
            time.sleep(10)