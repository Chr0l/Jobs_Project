import os
import re
import sys
import time

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, StaleElementReferenceException
)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src',)))
from tools.browser_manager import BrowserManager
from tools.logging_manager import LoggingManager
from tools.database_manager import DatabaseManager
from utils import orm_base

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
    def __init__(self, user_id):
        self._get_user_data(user_id)
        self.login()

    def login(self):
        """Handles the entire login process."""
        self.logger.info("Starting login process")
        self.driver.get("https://www.linkedin.com/")

        if self.browser_manager.inject_cookies(self.user_data):
            self.driver.refresh()

            if not self.__is_login_required():
                self.logger.info("Login not required, session is active.")
                return

        self.driver.get("https://www.linkedin.com/login")
        self.__fill_login_form()
        self.__handle_captcha()

    def _get_user_data(self, user_id):
        """Gets the user data from the database."""
        try:
            from utils.orm_base import User
            self.user_data = self.db_manager.get_entries(
                User,
                {"id": user_id}
            )[0]
            if not self.user_data:
                self.logger.error("No user found with the ID {user_id}")
                raise ValueError("No user found with the ID {user_id}")
        except Exception as e:
            self.logger.error(f"Error getting user data: {e}")
            raise

    def __is_login_required(self):
        """
        Checks if the user is already logged in.
        """
        try:
            time.sleep(2)
            self.driver.find_elements(By.CSS_SELECTOR, ".global-nav__me-photo")
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

            # Ajuste dos seletores para usar o atributo 'name'
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "session_key"))  # E-mail
            )
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "session_password"))  # Senha
            )

            with self.db_manager.session_scope() as session:
                user = session.merge(self.user_data)
                decrypted_password = user.decrypt_password()

                username_field.send_keys(user.email)
                password_field.send_keys(decrypted_password)
                password_field.send_keys(Keys.RETURN)

            self.logger.info("Login form submitted")

        except TimeoutException:
            self.logger.error("Timeout waiting for login form elements.")
        except Exception as e:
            self.logger.error(f"Failed to log in: {e}", exc_info=True)

    def __handle_captcha(self):
        """Handles CAPTCHA if present."""
        #TODO create function to handle captchas
        try:
            WebDriverWait(self.driver, timeout=10).until(
                lambda x: self.driver.execute_script("return document.readyState === 'complete'")
            )

            captcha_elements = self.driver.find_elements(By.CLASS_NAME, "captcha-challenge")
            if captcha_elements:
                self.logger.warning("CAPTCHA detected, waiting for user to solve")
                input("Please solve the CAPTCHA and press ENTER to continue.")
            else:
                self.logger.info("No CAPTCHA detected.")
        except TimeoutException:
            self.logger.warning("Timeout waiting for page to load completely.")

class LinkedInCrawler(Login):
    def __init__(self, user_id, browser="chrome", headless=False):
        self.logger = LoggingManager(logger_name='LinkedInCrawler').get_logger()
        self.browser_manager = BrowserManager(browser=browser, headless=headless)
        self.driver = self.browser_manager.driver
        self.db_manager = DatabaseManager()

        super().__init__(user_id)

        self.search_count = 0
        self.user_wants_to_stop = False

    def search_jobs(self, location=None, keywords=None):
        print(self.search_count)
        """
        Searches for jobs on LinkedIn.
        """
        url = "https://www.linkedin.com/jobs/search/?"
        if keywords:
            url += f"keywords={keywords}&"
        if location:
            url += f"location={location}&"

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
                    if not self._url_exists(job_data['url']):
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
        self.driver.execute_script("arguments[0].scrollIntoView();", card)

        action_button = card.find_element(By.XPATH, ".//button[contains(@class, 'job-card-container__action')]")
        action_button = action_button.find_element(By.XPATH, ".//*[name()='use']")
        if action_button.get_attribute('href') != "#close-small":
            return None

        try:
            title_element = card.find_element(By.XPATH, ".//a[contains(@class, 'job-card-list__title')]")
            location_element = card.find_element(By.CLASS_NAME, "job-card-container__metadata-item").text.split("(")
            if len(location_element) > 1:
                location = location_element[0].strip()
                work_format = location_element[1].rstrip(")")
            else:
                location = location_element[0]
                work_format = 'N/A'

            return {
                'platform': 'LinkedIn',
                'title': title_element.find_element(By.TAG_NAME, "strong").text,
                'company': card.find_element(By.CLASS_NAME, "job-card-container__primary-description").text,
                'location': location,
                'work_format': work_format,
                'url': title_element.get_attribute('href').split('?')[0],
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
            current_page_element = self.driver.find_element(By.CSS_SELECTOR, "li.artdeco-pagination__indicator--number.active.selected")
            next_page_element = current_page_element.find_element(By.XPATH, "following-sibling::li[1]/button")
            self.driver.execute_script("arguments[0].scrollIntoView();", next_page_element)
            self.driver.execute_script("arguments[0].click();", next_page_element)
            return True
        except NoSuchElementException:
            self.logger.warning("There are no more pages to navigate or the next page is not directly accessible.")
            return False
        except Exception as e:
            self.logger.error(f"Failed to navigate to the next page: {e}", exc_info=True)
            return False

    def _url_exists(self, url):
        """Checks if the URL already exists in the database."""
        with self.db_manager.session_scope() as session:
            exists = session.query(orm_base.JobsBaseInfo).filter(orm_base.JobsBaseInfo.url == url).first() is not None
        return exists

    def _insert_job_data(self, job_data):
        """Inserts job data into the database."""
        try:
            self.db_manager.add_entry(orm_base.JobsBaseInfo(**job_data), orm_base.JobsBaseInfo)
            return True
        except Exception as e:
            self.logger.error(f"Failed to insert job data into the database: {e}")
            return False

    def close(self):
        """Closes the webdriver and saves cookies."""
        self.logger.info("Saving cookies and closing browser")
        self.browser_manager.save_cookies(self.user_data)
        self.browser_manager.close()

