import sys
import os
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService                      # noqa: F401
from selenium.webdriver.firefox.service import Service as FirefoxService                    # noqa: F401
from selenium.webdriver.edge.service import Service as EdgeService                          # noqa: F401
from selenium.webdriver.chrome.service import Service as OperaService                       # noqa: F401

from webdriver_manager.chrome import ChromeDriverManager                                    # noqa: F401
from webdriver_manager.firefox import GeckoDriverManager as FirefoxDriverManager            # noqa: F401
from webdriver_manager.microsoft import EdgeChromiumDriverManager as EdgeDriverManager      # noqa: F401
from webdriver_manager.opera import OperaDriverManager                                      # noqa: F401

from .logging_manager import LoggingManager

# TODO add safari driver suporte


class BrowserManager:
    __BROWSERS = {"Chrome", "Edge", "Firefox", "Opera"}

    def __init__(self, browser, headless=False):
        self.browser = browser.capitalize()
        self.headless = headless
        self._driver = None
        self.options = None
        self.pkl_path = "data/cookies.pkl"
        self.logger = LoggingManager(logger_name='BrowserManager').get_logger()
        self._create_webdriver()

    def _create_webdriver(self):
        """Creates the webdriver instance."""
        self.logger.info(f"Creating webdriver for {self.browser} (headless={self.headless})")
        if self.browser not in self.__BROWSERS:
            self.logger.error(f"Browser '{self.browser}' not supported.")
            raise ValueError(
                f"Browser '{self.browser}' not supported. Supported browsers: {', '.join(self.__BROWSERS)}"
            )

        service = self._get_service()
        options = self._get_options()
        try:
            self._driver = getattr(webdriver, self.browser)(
                service=service, options=options
            )
            self.logger.info(f"Webdriver for {self.browser} created successfully")
        except Exception as e:
            self.logger.error(f"Error creating webdriver: {e}")
            raise

    def _get_service(self):
        """Returns the service instance."""
        self.logger.debug(f"Getting service for {self.browser}")
        service_class = getattr(webdriver, f"{self.browser}Service")
        driver_manager_class = getattr(
            sys.modules[__name__], f"{self.browser}DriverManager"
        )

        return service_class(driver_manager_class().install())

    def _get_options(self):
        """Returns the options instance."""
        self.logger.debug(f"Getting options for {self.browser}")
        match self.browser:
            case "Chrome":
                options = webdriver.ChromeOptions()
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
                options.add_argument('sec-ch-ua="Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"')
            case "Firefox":
                options = webdriver.FirefoxOptions()
                options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0",)
            case "Edge":
                options = webdriver.EdgeOptions()
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36 Edg/96.0.1054.29")
            case "Opera":
                options = webdriver.ChromeOptions()
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 OPR/51.0.2830.55")
                options.add_experimental_option("w3c", True)

        # Common options for all browsers
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--disable-popup-blocking")

        options.add_argument("--disable-webgl")
        options.add_argument("--disable-prefetch")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("prefs", {"profile.default_content_setting_values.geolocation": 2})
        options.add_experimental_option("useAutomationExtension", False)

        if self.headless:
            options.add_argument("--headless")
            options.add_argument('--disable-gpu')

        return options

    def save_cookies(self):
        """Saves the cookies to the pickle file."""
        self.logger.info(f"Saving cookies to {self.pkl_path}")
        os.makedirs(os.path.dirname(self.pkl_path), exist_ok=True)
        with open(self.pkl_path, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)

    def inject_cookies(self):
        """Injects the cookies from the pickle file."""
        self.logger.info(f"Injecting cookies from {self.pkl_path}")
        with open(self.pkl_path, "rb") as file:
            cookies = pickle.load(file)
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def close(self):
        """Closes the webdriver instance."""
        self.logger.info("Closing webdriver")
        if self._driver:
            self._driver.quit()

    @property
    def driver(self):
        """Returns the webdriver instance."""
        return self._driver if self._driver else self._create_webdriver()

    @classmethod
    def list_supported_browsers(cls):
        """Returns a list of supported browsers."""
        return list(cls.__BROWSERS)
