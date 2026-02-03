"""
logging_config.py
----------------
Centralized logging configuration for the application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict, Any

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Log levels
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
    
    # Prevent adding handlers multiple times
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = LOG_DIR / 'library_app.log'
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def configure_logging() -> None:
    """Configure root logger and third-party loggers."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVELS.get(LOG_LEVEL, logging.INFO))
    
    # Configure third-party loggers
    for logger_name in ['sqlalchemy', 'mysql.connector']:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Configure our application logger
    logger = get_logger(__name__)
    logger.info("Logging configured successfully")

# Configure logging when module is imported
configure_logging()
