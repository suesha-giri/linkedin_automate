import time
import pickle

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from utils import get_logger, wait_for_element


logger = get_logger()


class Login:
    LOGIN_URL = "https://www.linkedin.com/login"

    def __init__(self, username, password, driver):
        self.username = username
        self.password = password
        self.driver = driver
    
    def login(self):
        driver = self.driver
        driver.get(self.LOGIN_URL)
        time.sleep(5)

        try:
            username_textbox = wait_for_element(driver, By.ID, "username")
            username_textbox.send_keys(self.username)
            time.sleep(2)

            password_textbox = wait_for_element(driver, By.ID, "password")
            password_textbox.send_keys(self.password)
            time.sleep(2)
            password_textbox.send_keys(Keys.RETURN)

            # captcha verification
            time.sleep(20)
            # Wait for the 2FA input box to appear
            wait_for_element(driver, By.ID, "input__phone_verification_pin")
        except Exception as e:
            logger.error(f"Login failed, {e}")
            return False
        
        return self.handle_2FA()

    def handle_2FA(self):
        driver = self.driver

        logger.info("Waiting for user to enter the 2FA code.")

        try:
            code_input = wait_for_element(driver, By.ID, "input__phone_verification_pin")

            logger.info("2FA input field found. Waiting for the user to input the code.")

            WebDriverWait(driver, 30).until(lambda d: len(code_input.get_attribute("value")) == 6)
            submit_button = driver.find_element(By.ID, "two-step-submit-button")
            submit_button.click()

            logger.info("2FA code entered successfully. Waiting for validation.")

            WebDriverWait(driver, 20).until(EC.url_contains("/feed"))
  
            return self.save_cookies()
        except TimeoutException as e:
            logger.error(f"Login or 2FA failed.{e}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False

    def save_cookies(self):
        logger.info("Attempting to save the cookies.")
        driver = self.driver
        cookies = driver.get_cookies()
        time.sleep(3)

        with open("linkedin_cookies.pkl", "wb") as f:
            pickle.dump(cookies, f)

        logger.info("Cookies saved.")

        return True