import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime


def setup_logging():
    """
    Configure application-wide logging with daily rotation.

    Logs are saved to ./logs/ directory with daily rotation.
    Format: YYYY-MM-DD_app.log (e.g., 2025-10-10_app.log)
    """
    # Create logs directory if it doesn't exist
    log_dir = "/app/logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define log format
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(funcName)s:%(lineno)d | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # File handler with daily rotation => 파일에 보이는 로그레벨
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}_app.log")
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",  # Rotate at midnight
        interval=1,       # Every 1 day
        backupCount=30,   # Keep 30 days of logs
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # Console handler for Docker logs => 콘솔에 보이는 로그레벨
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Configure root logger =>
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("663897elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)

    logging.info("=" * 80)
    logging.info("Application logging initialized")
    logging.info(f"Log file: {log_file}")
    logging.info("=" * 80)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Usually __name__ of the module

    Returns:
        logging.Logger: Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    return logging.getLogger(name)
