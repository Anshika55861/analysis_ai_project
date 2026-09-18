"""
Section headings that should be treated as "clause-bearing" sections
for Task 4 (clause analysis).

Now loaded dynamically from config/headings.json via config_loader.
"""

from config.config_loader import get_config_item

CLAUSE_SECTION_HEADINGS = get_config_item("clause_section_headings", [])

# Similarity ratio (0-1) above which two clauses from different documents
# are flagged as similar.
SIMILARITY_THRESHOLD = get_config_item("similarity_threshold", 0.35)

# How much of a clause's text to compare when computing similarity.
SIMILARITY_TEXT_LIMIT = get_config_item("similarity_text_limit", 4000)

# RapidFuzz token_sort_ratio threshold for title matching across documents.
TITLE_SIMILARITY_THRESHOLD = get_config_item("title_similarity_threshold", 70)
