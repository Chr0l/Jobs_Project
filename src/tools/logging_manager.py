import logging
import os

class LoggingManager:
    """
    Class responsible for configuring and managing logging.

    Attributes:
    logger (logging.Logger): The logger instance.
    """

    def __init__(self, log_level=logging.INFO, logger_name=__name__):
        self.log_file = 'data/app.log'
        self.log_level = log_level
        self.logger_name = logger_name
        self.logger = self._create_logger()

    def _create_logger(self):
        """Creates and configures the logger instance."""
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.log_level)

        if not logger.hasHandlers():
            # Create file handler which logs even debug messages
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(self.log_level)

            # Create console handler with a higher log level
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.ERROR)

            # Create formatter and add it to the handlers
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            # Add the handlers to the logger
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def get_logger(self):
        """Returns the logger instance."""
        return self.logger

# Example usage:
# log_manager = LoggingManager(log_file='logs/app.log', logger_name='my_logger')
# logger = log_manager.get_logger()
# logger.info("This is an info message")
# logger.error("This is an error message")
