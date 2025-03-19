"""
Shared logging configuration for the Nasdaq Stock Assistant application.
This ensures all modules log to the same files with consistent formatting.
"""
import logging
from log_utils import setup_logging

# Common parameters for all loggers in the application
APP_NAME = "nasdaq_assistant"
LOG_LEVEL = logging.DEBUG
MAX_LOGS = 20

# Create a single logger instance to be imported by all modules
logger = setup_logging(app_name=APP_NAME, log_level=LOG_LEVEL, max_logs=MAX_LOGS)

def get_logger():
    """
    Get the shared logger instance.
    This function allows modules to access the same logger instance.
    
    Returns:
        logger: Configured logger instance
    """
    return logger
