import os
import logging
from datetime import datetime

def get_logger(name: str = "app"):
    """
    Logger structure:
    logs/<YYYY-MM-DD>/<YYYY-MM-DD HH-MM-SS>.log

    Console → WARNING + ERROR  
    File → INFO + WARNING + ERROR  

    Format:
    [TIMESTAMP]: filename: line: LEVEL: message
    """

    # --- Directory setup ---
    base_log_dir = "logs"
    os.makedirs(base_log_dir, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    dated_dir = os.path.join(base_log_dir, today)
    os.makedirs(dated_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    log_filename = f"{timestamp}.log"
    log_filepath = os.path.join(dated_dir, log_filename)

    # --- Logger ---
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Avoid re-adding handlers
    if logger.handlers:
        return logger

    # --- Custom Formatter ---
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = record.filename
            line = record.lineno
            level = record.levelname
            message = record.getMessage()

            return f"[{timestamp}]: {filename}: line {line}: {level}: {message}"

    formatter = CustomFormatter()

    # --- File Handler (INFO+) ---
    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # --- Console Handler (WARNING+) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger