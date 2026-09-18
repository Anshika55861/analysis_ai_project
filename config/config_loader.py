"""
Configuration Loader Module

Loads config/headings.json once and provides cached access to
headings, patterns, triggers, and thresholds.
"""

import json
from pathlib import Path

_CONFIG_CACHE = None
_CONFIG_PATH = Path(__file__).resolve().parent / "headings.json"


def load_headings_config(config_path: Path = None) -> dict:
    """
    Load the consolidated JSON configuration file.
    Caches result in memory after the first read.
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None and config_path is None:
        return _CONFIG_CACHE

    path_to_load = config_path or _CONFIG_PATH

    with open(path_to_load, "r", encoding="utf-8") as f:
        config = json.load(f)

    if config_path is None:
        _CONFIG_CACHE = config

    return config


def get_config_item(key: str, default=None):
    """
    Retrieve a specific key from the loaded configuration.
    """
    config = load_headings_config()
    return config.get(key, default)
