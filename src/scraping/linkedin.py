import os
import re
import sys
import time
import uuid
from dotenv import load_dotenv

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, StaleElementReferenceException
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.tools.browser_manager import BrowserManager
from src.tools.logging_manager import LoggingManager
from src.tools.database_manager import DatabaseManager
from src.utils.orm_base import JobsBaseInfo

scroll_script = """
    var div = document.querySelector('.jobs-search-results-list');
    window.stopScrolling = false;
    var scrollInterval = setInterval(function() {
        if (div.scrollTop + div.clientHeight >= div.scrollHeight || window.stopScrolling) {
            clearInterval(scrollInterval);
        } else {
            div.scrollTop += 100;
        }
    }, 5);
"""

class Login:
    def login(self):
        """
        Handles the entire login process.
        """
        self.logger.info("Starting login process")
        self.driver.get("https://www.linkedin.com/")

        try:
            self.browser_manager.inject_cookies()
            self.driver.refresh()
            if not self.__is_login_required():
                self.logger.info("Login not required, session is active.")
                return
        except FileNotFoundError:
            self.logger.warning("Cookies file not found, proceeding with manual login")

        self.driver.get("https://www.linkedin.com/login")
        self.__fill_login_form()
        self.__handle_captcha()

    def __is_login_required(self):
        """
        Checks if the user is already logged in.
        """
        try:
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR, ".global-nav__me-photo")
            self.logger.info("Already logged in")
            return False
        except NoSuchElementException:
            self.logger.info("Login required")
            return True

    def __fill_login_form(self):
        """
        Fills the login form with the provided credentials.
        """
        try:
            self.logger.info("Filling login form")
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.send_keys(os.getenv("EMAIL"))
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys(os.getenv("PASSWORD"))
            password_field.send_keys(Keys.RETURN)
            self.logger.info("Login form submitted")
        except (TimeoutException, NoSuchElementException):
            self.logger.error("Failed to log in due to page issues.")

    def __handle_captcha(self):
        #TODO create function to handle captchas
        try:
            captcha_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "captcha-internal"))
            )
            if captcha_element:
                self.logger.warning("CAPTCHA detected, waiting for user to solve")
                input("Please solve the CAPTCHA and press ENTER to continue.")
        except TimeoutException:
            self.logger.info("No CAPTCHA detected")

class LinkedInCrawler(Login):
    def __init__(self, browser="chrome", headless=False):
        load_dotenv()
        self.logger = LoggingManager(logger_name='LinkedInCrawler').get_logger()
        self.browser_manager = BrowserManager(browser=browser, headless=headless)
        self.driver = self.browser_manager.driver
        self.db_manager = DatabaseManager()
        self.db_manager.create_tables()
        self.search_count = 0

    def __call__(self, location=None, keywords=None):
        self.login()
        url = "https://www.linkedin.com/jobs/search/?"
        if keywords:
            url += f"keywords={keywords}&"
        if location:
            url += f"location={location}&"

        self.user_wants_to_stop = False

        while True:
            self.search_count += 1
            self.driver.get(url)
            self._get_job_data()
            if self.user_wants_to_stop:
                self.logger.info("All jobs collected. Stopping search.")
                break
            else:
                self.logger.info("No more pages to navigate. Restarting search.")
                break

    def _get_job_data(self):
        """
        Collect data from all job cards on the page.
        """
        while True:
            time.sleep(3)
            try:
                current_page_button = self.driver.find_element(By.CSS_SELECTOR ,"li.artdeco-pagination__indicator--number.active.selected")
                self.current_page_number = int(current_page_button.text)
            except NoSuchElementException:
                self.logger.error("The current page could not be found.")
                return False

            for _ in range(5):
                elements = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__job-card-search--generic-occludable-area")
                if not elements:
                    break
                self.driver.execute_script(scroll_script)

            job_cards = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.jobs-search-results__list-item"))
            )
            for index, card in enumerate(job_cards):
                job_data = self._collect_card_data(index, card)
                if job_data:
                    if not self.url_exists(job_data['url']):
                        if self._insert_job_data(job_data):
                            self._close_job_card(card, index)
                    else:
                        self.logger.warning(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. Vacancy previously collected, called the close vacancy.")
                        self._close_job_card(card, index)

            if not self._navigate_to_next_page():
                break

    def _collect_card_data(self, index, card):
        """
        Collect data from a single job card.
        """
        action_button = card.find_element(By.XPATH, ".//button//span[@class='artdeco-button__text']//*[name()='svg']//*[name()='use']")
        if action_button.get_attribute('href') != "#close-small":
            return None

        try:
            title_element = card.find_element(By.XPATH, ".//a[contains(@class, 'job-card-list__title')]")

            return {
                'platform': 'LinkedIn',
                'title': title_element.text,
                'company': card.find_element(By.CLASS_NAME, "job-card-container__primary-description").text,
                'location': card.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text,
                'url': title_element.get_attribute('href').split('eBP=')[0],
            }

        except NoSuchElementException:
            self.logger.error(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. Specific element not found on the card.")

    def _close_job_card(self, card, index):
        """
        Close a job card to hide it in future searches.
        """
        try:
            close_button = card.find_element(By.XPATH, ".//button[contains(@class, 'artdeco-button') and .//*[name()='svg' and @data-test-icon='close-small']]")
            self.driver.execute_script("arguments[0].click();", close_button)
        except StaleElementReferenceException:
            self.logger.error(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. The job card element has been obsolete.")
            try:
                close_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, ".//button[contains(@class, 'artdeco-button') and .//*[name()='svg' and @data-test-icon='close-small']]"))
                )
                self.driver.execute_script("arguments[0].click();", close_button)
                self.logger.info(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. Closed job card after retry.")
            except Exception as e:
                self.logger.error(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. Failed to close job card after retry: {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Search: {self.search_count} Page: {self.current_page_number} Card: {index+1}. Failed to close job card: {e}", exc_info=True)


    def _navigate_to_next_page(self):
        """
        Navigates to the next page of the search results.

        Returns:
        True if the next page was successfully navigated to, False otherwise.
        """
        pagination = self.driver.execute_script("return document.querySelector('.artdeco-pagination__page-state').textContent;")
        pagination =  [int(num) for num in re.findall(r'\d+', pagination)]

        if pagination[0] != self.current_page_number:
            self.logger.warning(f"The active page is {self.current_page_number}, but {pagination[0]} is indicated as the current page.")

        if self.current_page_number == pagination[1]:
            self.logger.info("There are no more pages to navigate.")
            return False

        try:
            self.logger.info(f"Navigating to page {self.current_page_number + 1}.")
            next_page_button = self.driver.find_element(By.XPATH, f"//button[contains(@aria-label, ' {self.current_page_number + 1}')]")
            self.driver.execute_script("arguments[0].click();", next_page_button)
            return True
        except NoSuchElementException:
            self.logger.warning("There are no more pages to navigate or the next page is not directly accessible.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to navigate to the next page: {e}", exc_info=True)
            return False


    def url_exists(self, url):
        """Checks if the URL already exists in the database."""
        with self.db_manager.session_scope() as session:
            exists = session.query(JobsBaseInfo).filter(JobsBaseInfo.url == url).first() is not None
        return exists

    def _insert_job_data(self, job_data):
        """Inserts job data into the database."""
        try:
            self.db_manager.add_job(job_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to insert job data into the database: {e}")
            return False

    def close(self):
        """Closes the webdriver and saves cookies."""
        self.logger.info("Saving cookies and closing browser")
        self.browser_manager.save_cookies()
        self.browser_manager.close()

if __name__ == "__main__":
    while True:
        os.environ['SESSION_UID'] = uuid.uuid4().hex
        try:
            crawler = LinkedInCrawler(browser="chrome")
            crawler(location="Brasil")
        except Exception as e:
            print(e)
            continue
        finally:
            crawler.close()

