"""
Utility module for project logging.
"""

import logging
from pathlib import Path


def setup_logger(name: str = "insurance_analysis") -> logging.Logger:
    """
    Create and configure a reusable logger.

    Parameters
    ----------
    name : str
        Logger name.

    Returns
    -------
    logging.Logger
    """

    log_folder = Path("logs")
    log_folder.mkdir(exist_ok=True)

    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File output
    file_handler = logging.FileHandler(
        log_folder / "project.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Alias for flexible imports across modules
get_logger = setup_logger