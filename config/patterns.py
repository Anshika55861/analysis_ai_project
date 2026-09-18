"""
Regex / keyword patterns used for metadata extraction (Task 1),
dictionary building (Task 3), and clause numbering (Task 4).

Lists are loaded dynamically from config/headings.json via config_loader.
"""

from config.config_loader import get_config_item

# Known policy types to look for, in priority order.
POLICY_TYPES = get_config_item("policy_types", [])

# Suffixes that usually follow an insurance company's legal name.
COMPANY_SUFFIXES = get_config_item("company_suffixes", [])

# Words that signal a line is naming the insurer.
COMPANY_KEYWORDS = get_config_item("company_keywords", [])

# Phrases that usually precede an effective/commencement/inception date.
EFFECTIVE_DATE_TRIGGERS = get_config_item("effective_date_triggers", [])

# Trigger words identifying definition/glossary sections.
DEFINITION_TRIGGERS = get_config_item("definition_triggers", [
    "definition",
    "definitions",
    "glossary",
    "meaning of terms",
    "interpretation"
])

# A generic date pattern: 12 Jan 2024 / 12/01/2024 / 12-01-2024 / January 12, 2024
DATE_PATTERN = (
    r"(\d{1,2}[\/\-\s](?:\d{1,2}|[A-Za-z]+)[\/\-\s]\d{2,4}"
    r"|[A-Za-z]+\s+\d{1,2},?\s+\d{4})"
)

# Document/version codes such as "BeyondCare-PW-EN-01" or "v2.3"
VERSION_PATTERNS = [
    r"\b([A-Za-z]{2,}-[A-Za-z0-9]+-[A-Za-z0-9-]*\d+)\b",
    r"\bversion\s*[:\-]?\s*([A-Za-z0-9.\-]+)\b",
    r"\b(v\d+(\.\d+)*)\b",
]
