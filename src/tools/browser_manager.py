import os
import sys
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as OperaService

from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager as FirefoxDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager as EdgeDriverManager
from webdriver_manager.opera import OperaDriverManager

from .logging_manager import LoggingManager

# TODO add safari driver suporte


class BrowserManager:
    """
    Class responsible for creating and managing the webdrivers.

    Arguments:
    browser (str): The browser to be used.
    headless (bool): Whether to run the browser in headless mode or not.

    Returns:
    driver (webdriver): The webdriver instance.

    Raises:
    ValueError: If the browser is not supported.
    """

    __BROWSERS = {"Chrome", "Edge", "Firefox", "Opera"}

    def __init__(self, browser=None, headless=False):
        if not browser:
            raise ValueError(f"No browser specified. Please specify a browser. Supported browsers: {', '.join(self.__BROWSERS)}")
        self.browser = browser.capitalize()
        self.headless = headless
        self._driver = None
        self.options = None
        self.pkl_path = "data/cookies.pkl"
        self.logger = LoggingManager(logger_name='BrowserManager').get_logger()
        self._create_webdriver()

    def _create_webdriver(self):
        """Creates the webdriver instance."""
        if self.browser not in self.__BROWSERS:
            self.logger.error(f"Browser '{self.browser}' not supported. Supported browsers: {', '.join(self.__BROWSERS)}")
            raise ValueError(
                f"Browser '{self.browser}' not supported. Supported browsers: {', '.join(self.__BROWSERS)}"
            )

        try:
            service = self._get_service()
            options = self._get_options()
            self._driver = getattr(webdriver, self.browser)(
                service=service, options=options
            )
            self.logger.info(f"{self.browser} webdriver created successfully.")
        except Exception as e:
            self.logger.error(f"Failed to create {self.browser} webdriver: {e}")
            raise RuntimeError(f"Failed to create {self.browser} webdriver: {e}")

    def _get_service(self):
        """Returns the service instance."""
        try:
            service_class = getattr(webdriver, f"{self.browser}Service")
            driver_manager_class = getattr(sys.modules[__name__], f"{self.browser}DriverManager")
            self.logger.info(f"Installing {self.browser} driver.")
            return service_class(driver_manager_class().install())
        except Exception as e:
            self.logger.error(f"Failed to install {self.browser} driver: {e}")
            raise RuntimeError(f"Failed to install {self.browser} driver: {e}")

    def _get_options(self):
        """Returns the options instance."""
        match self.browser:
            case "Chrome":
                options = webdriver.ChromeOptions()
            case "Firefox":
                options = webdriver.FirefoxOptions()
            case "Edge":
                options = webdriver.EdgeOptions()
            case "Opera":
                options = webdriver.ChromeOptions()
                options.add_experimental_option("w3c", True)

        if options:
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-notifications")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--lang=pt-BR")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_argument("--disable-blink-features=AutomationControlled")
            if self.headless:
                options.add_argument("--headless")

        self.logger.info(f"Options set for {self.browser} browser.")
        return options

    def save_cookies(self):
        """Saves the cookies to the pickle file."""
        try:
            os.makedirs(os.path.dirname(self.pkl_path), exist_ok=True)
            with open(self.pkl_path, "wb") as file:
                pickle.dump(self.driver.get_cookies(), file)
            self.logger.info("Cookies saved successfully.")
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")

    def inject_cookies(self):
        """Injects the cookies from the pickle file."""
        try:
            with open(self.pkl_path, "rb") as file:
                cookies = pickle.load(file)
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.logger.info("Cookies injected successfully.")
        except Exception as e:
            self.logger.error(f"Failed to inject cookies: {e}")

    def close(self):
        """Closes the webdriver instance."""
        if self._driver:
            self._driver.quit()
            self.logger.info("Webdriver closed successfully.")

    @property
    def driver(self):
        """Returns the webdriver instance."""
        if not self._driver:
            self._create_webdriver()
        return self._driver

    @classmethod
    def list_supported_browsers(cls):
        """Returns a list of supported browsers."""
        return list(cls.__BROWSERS)
