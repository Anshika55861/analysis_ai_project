"""
Common insurance section headings.
Now loaded dynamically from config/headings.json via config_loader.
"""

from config.config_loader import get_config_item

SECTION_HEADINGS = get_config_item("section_headings", [])