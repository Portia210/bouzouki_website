import logging
from logging.handlers import RotatingFileHandler
import pytz
from datetime import datetime
import os

def setup_logger(name="logger", level=logging.DEBUG, log_file=None, app_timezone=None):
    """
    Sets up a logger with both console and file handlers.
    
    Args:
        name (str): Name of the logger
        level (int): Logging level (default: DEBUG)
        log_file (str, optional): Log file name
    
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        # Custom formatter class for timezone support
        class TimezoneFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                # Convert float timestamp time, by default as the local timezone
                dt = datetime.fromtimestamp(record.created)
                # Convert to app timezone if provided
                if app_timezone:
                    dt = dt.astimezone(app_timezone)
                if datefmt:
                    return dt.strftime(datefmt)
                else:
                    return dt.strftime("%Y-%m-%d %H:%M:%S")

        # Formatter with filename and line number
        formatter = TimezoneFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file is provided)
        if log_file:
            file_handler = RotatingFileHandler(log_file, maxBytes=5000000, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

# Create default logger instance with configurable level
# Default to INFO for production, but allow override via LOG_LEVEL environment variable
log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_name, logging.INFO)
logger = setup_logger(name="logger", level=log_level, log_file=None)


if __name__ == "__main__":
    logger.info("Hello, world!")