import os
import sys

from loguru import logger

class LoggingManager:
    def __init__(self, logger_name=__name__):
        self.session_id = os.getenv('SESSION_UID', 'default')
        self.log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.log_file = 'data/app.log'

        logger.remove()
        logger.add(
            self.log_file,
            level=self.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {extra[session_id]} | {level} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="1 week",
            compression="zip",
            enqueue=True,
        )
        logger.add(
            lambda msg: sys.stderr.write(msg),
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {extra[session_id]} | {level} | {name}:{function}:{line} - {message}",
        )

        self.logger = logger.bind(session_id=self.session_id)

    def get_logger(self):
        return self.logger
