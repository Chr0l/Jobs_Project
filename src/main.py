import os
import sys
import json
import uuid
from datetime import datetime

from dotenv import load_dotenv
from cryptography.fernet import Fernet

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))
from tools.logging_manager import LoggingManager

class EnvironmentManager:
    def __init__(self, env_file_path=".env"):
        self.env_file_path = env_file_path
        self.logger = LoggingManager(logger_name="EnvironmentManager").get_logger()

    def load_or_create_env_file(self):
        if not os.path.exists(self.env_file_path):
            with open(self.env_file_path, "w") as f:
                f.write("# Environment variables\n")
            self.logger.info(f"Created .env file at: {self.env_file_path}")
        load_dotenv(self.env_file_path)

    def load_or_create_secret_key(self):
        secret_key_str = os.getenv("SECRET_KEY")
        if secret_key_str:
            try:
                secret_key_data = json.loads(secret_key_str)
                key = secret_key_data["key"]
                self.logger.info(f"Loaded SECRET_KEY from .env: {key}")
            except json.JSONDecodeError:
                self.logger.error("Invalid SECRET_KEY format in .env.")
                raise
        else:
            key = Fernet.generate_key().decode()
            secret_key_data = {
                "key": key,
                "created_at": datetime.now().isoformat(),
                "is_automatic": True,
            }
            os.environ["SECRET_KEY"] = json.dumps(secret_key_data)
            with open(self.env_file_path, "a") as f:
                f.write(f"SECRET_KEY={json.dumps(secret_key_data)}\n")
            self.logger.info(f"Generated and set new SECRET_KEY in .env: {key}")

        try:
            Fernet(key)
        except ValueError:
            self.logger.error("Invalid SECRET_KEY format.")
            raise

    def load_or_create_database_config(self):
        database_config_str = os.getenv("DATABASE_CONFIG")
        if database_config_str:
            try:
                database_config = json.loads(database_config_str)
                self.logger.info(f"Loaded database configuration from .env: {database_config}")
            except json.JSONDecodeError:
                self.logger.error("Invalid DATABASE_CONFIG format in .env.")
                raise
        else:
            database_config = {
                "url": "sqlite:///data/db.sqlite",
                "local": True,
                "is_automatic": True,
            }
            os.environ["DATABASE_CONFIG"] = json.dumps(database_config)

            os.makedirs("data", exist_ok=True)

            with open(self.env_file_path, "a") as f:
                f.write(f"DATABASE_CONFIG={json.dumps(database_config)}\n")

            self.logger.info("Created default database configuration (SQLite) and saved to .env.")

        try:
            from sqlalchemy import create_engine
            create_engine(database_config["url"])
        except Exception as e:
            self.logger.error(f"Invalid database URL: {database_config['url']}. Error: {e}")
            raise

        self.logger.info(f"Using database URL: {database_config['url']}")

    def validate_and_create_databases(self):
        from tools.database_manager import DatabaseManager

        db_manager = DatabaseManager()
        db_manager.create_tables()

    def setup_environment(self):
        self.load_or_create_env_file()
        self.load_or_create_secret_key()
        self.load_or_create_database_config()
        self.validate_and_create_databases()


if __name__ == "__main__":
    env_manager = EnvironmentManager()
    env_manager.setup_environment()

    from scraping.linkedin import LinkedInCrawler

    os.environ['SESSION_UID'] = uuid.uuid4().hex
    crawler = LinkedInCrawler(browser="chrome", user_id=1)
    while True:
        try:
            crawler.search_jobs(location="Brasil")
        except Exception as e:
            print(e)
            continue
