import os
import time

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from login import Login
from utils import (
    get_logger,
    get_chrome_driver,
    load_cookies,
    ensure_internet_connection,
)
from record import (
    get_visited_polls,
    get_or_create_excel_file,
    update_excel_file,
    get_visited_profiles,
)


logger = get_logger()
load_dotenv()


def linkedin_bot():
    driver = get_chrome_driver()
    try:
        driver.get("https://www.linkedin.com")
        time.sleep(5)

        loaded_cookies = load_cookies(driver)
        if not loaded_cookies:
            username = os.getenv("username")
            password = os.getenv("password")

            if not username or not password:
                logger.error("Username or password not found in environment variables.")
                driver.quit()

            login = Login(username, password, driver).login()
            if not login:
                driver.quit()

        # navigate to notifications
        notifications = driver.get("https://www.linkedin.com/notifications/?filter=all")
        time.sleep(5)

        workbook, sheet = get_or_create_excel_file() 
        visited_polls = get_visited_polls(sheet)
        visited_profiles = get_visited_profiles(sheet)

        logger.info("......towards poll")

        try:
            notification_div = driver.find_element(By.XPATH, "//div[@data-finite-scroll-hotkey-context='NOTIFICATIONS']")
            article=notification_div.find_element(By.XPATH, ".//span[text()='Your poll']")
            # article=notification_div.find_element(By.XPATH, ".//article[@data-view-name='notification-card-container']//div//div//a//span[text()='Your poll']")
            # Combined XPath to find the phrase "your poll received"
            # combined_xpath = ".//span[text()='Your poll']/following-sibling::strong[contains(text(), 'received')]"
            polls = notification_div.find_elements(By.XPATH, ".//span[contains(text(), 'Your poll')]")
            print(polls)
        except Exception as e:
            logger.error(str(e))
            logger.info("quittig the driver")
            driver.quit()
        time.sleep(5)

        new_records = []

        for poll in polls:
            # go to its parent anchor tag and get the poll link element
            poll_link_element = poll.find_element(By.XPATH, "./parent::a")
            poll_link = poll_link_element.get_attribute("href")

            if poll_link in visited_polls:
                logger.info("Poll is already visited, so going towards another poll.")
                continue

            poll_link_element.send_keys(Keys.CONTROL + Keys.RETURN)   # Open the link in a new tab
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(5)

            vote_button = driver.find_element(By.XPATH, "//button[contains(text(), 'votes')]")
            vote_button.click()
            time.sleep(5)

            div = driver.find_element(By.ID, "ember1193")
            buttons = div.find_element(By.CSS_SELECTOR, "button[class*='artdeco-tab'][role='tab']")

            click_count = 0 # number of clicks of follow button

            for button in buttons:
                button.click()
                time.sleep(5)

                # Click 'Show more results' until it disappears
                while True:
                    try:
                        show_more_button = driver.find_element(By.XPATH, "//button[span[contains(text(), 'Show more results')]]")
                        show_more_button.click()
                        time.sleep(8)
                    except NoSuchElementException:
                        logger.info("The 'Show more results' button was not found on the page.")
                        break
                
                div_class = driver.find_element(By.CLASS_NAME, "scaffold-finite-scroll__content")
                user_profiles = div_class.find_elements(By.XPATH, ".//a[contains(@class, 'update-components-poll-vote__profile-link')]")
                time.sleep(5)

                for profile in user_profiles:
                    profile_url = profile.get_attribute("href")

                    if profile_url in visited_profiles:
                        logger.info(f"Profile {profile_url} is already visited, so going towards another profile.")
                        continue

                    profile.send_keys(Keys.CONTROL + Keys.RETURN)
                    driver.switch_to.window(driver.window_handles[-1])
                    time.sleep(5)

                    logger.info("User profile to follow opens in the new tab")

                    # follow the user from follow botton or press more and then follow.
                    div_class = driver.find_element(By.CLASS_NAME, "zftDBbmKukicPfhhPZAlxPQGrMwgHzRYudUHM")
                    
                    max_clicks = 300

                    while click_count <= max_clicks:
                        try:
                            # searching for the follow button
                            button = div_class.find_element(By.XPATH, ".//button[.//span[@class='artdeco-button__text' and text()='Follow']]")
                            button.click()
                            time.sleep(10)
                            click_count+=1
                        except NoSuchElementException as e:
                            logger.info("Initial follow button isnt present in the profile. Looking for 'more' button.")

                            button = div_class.find_element(By.XPATH, ".//button[@aria-label='More actions']")
                            button.click() #clicked more button
                            time.sleep(10)

                            follow_button = div_class.find_element(
                                By.XPATH, ".//div[@class='artdeco-dropdown__content-inner']/ul/li/div[contains(@aria-label, 'Follow'))]")
                            follow_button.click()
                            time.sleep(10)
                            click_count+=1

                        # add vsisted poll and profile into list
                        new_records.append((profile_url, poll))

                        # Close the current tab
                        driver.close()
                        driver.switch_to.window(driver.window_handles[-1])

                driver.close()
                driver.switch_to.window(driver.window[-1])
    
        if new_records:
            update_excel_file(workbook, sheet, new_records)

        # Close the browser and end the WebDriver session
        driver.quit()  # This will close the browser and free up resources
    except Exception as e:
        print(e)
        error_msg = str(e)
        # if internet gets disconnected then resume from the same place
        if "ERR_INTERNET_DISCONNECTED" in error_msg:
            logger.error(f"Internet Disconnected. Waiting for the connection...")
            ensure_internet_connection()
            linkedin_bot()
        else:
            logger.error(f"An unexpected error occured, {e}")


    driver.quit()

linkedin_bot()