import logging
import os

LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, "..", "smart_attendance.log")


def get_logger(name="SmartAttendance"):
    """Returns a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(LOG_FORMAT)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        try:
            fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            pass

    return logger
