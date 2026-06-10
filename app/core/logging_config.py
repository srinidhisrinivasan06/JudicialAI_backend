import logging
import os
import sys

def setup_logging():
    # Log to backend/logs directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # backend root is 2 levels up
    backend_root = os.path.dirname(os.path.dirname(current_dir))
    log_dir = os.path.join(backend_root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    # Formatter definition
    log_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear default handlers to prevent duplication
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console output handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # File output handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    # Quiet down noisy library logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    logging.info("Logging initialized. Writing logs to %s", log_file)

# Call on import to configure logs immediately
setup_logging()
logger = logging.getLogger("justice-lens")
