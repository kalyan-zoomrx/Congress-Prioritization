import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Optional

_current_log_file = None
_loggers_initialized: Set[str] = set()

def get_logger(name: str = "app"):
    """
    Logger structure:
    logs/<YYYY-MM-DD>/<YYYY-MM-DD HH-MM-SS>.log

    Console → WARNING + ERROR  
    File → INFO + WARNING + ERROR + DEBUG  

    Format:
    [TIMESTAMP]: filename: line: LEVEL: message
    """
    global _current_log_file

    # --- Directory and Filename setup ---
    base_log_dir = Path("logs")
    today = datetime.now().strftime("%Y-%m-%d")
    dated_dir = base_log_dir / today
    
    if _current_log_file is None:
        try:
            dated_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            log_filename = f"{timestamp}.log"
            _current_log_file = dated_dir / log_filename
        except OSError as e:
            print(f"Failed to create log directory: {e}")
            _current_log_file = Path("fallback.log")

    # --- Logger ---
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Avoid re-adding handlers
    if name in _loggers_initialized:
        return logger
    
    _loggers_initialized.add(name)

    # --- Custom Formatter ---
    class CustomFormatter(logging.Formatter):
        def format(self, record):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            filename = record.filename  # Actual file, not logger name
            line = record.lineno
            level = record.levelname
            message = record.getMessage()

            return f"[{timestamp}]: {filename}: line {line}: {level}: {message}"

    formatter = CustomFormatter()

    # --- File Handler (DEBUG+) ---
    try:
        file_handler = logging.FileHandler(_current_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # Capture DEBUG in file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as e:
        print(f"Failed to create file handler: {e}")

    # --- Console Handler (WARNING+) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger