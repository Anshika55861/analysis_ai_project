"""
Task 3 - Search Insurance Dictionary

Case-insensitive, partial-word search over the insurance dictionary,
with synonym support and matching across term names, keywords, and aliases.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import OUTPUT_DIR
from config.synonyms import SYNONYMS
from utils.logger import setup_logger
from utils.json_utils import load_json

logger = setup_logger()

DICTIONARY_FILE = OUTPUT_DIR / "insurance_dictionary.json"


def expand_with_synonyms(keyword: str) -> list[str]:
    """
    Return the original keyword plus any synonyms configured for it,
    so a search for e.g. 'excess' also matches the 'Deductible' entry.
    """
    keyword = keyword.lower().strip()
    search_terms = {keyword}

    for term, synonym_list in SYNONYMS.items():
        lowered_synonyms = [s.lower() for s in synonym_list]

        if keyword == term.lower() or keyword in lowered_synonyms:
            search_terms.add(term.lower())
            search_terms.update(lowered_synonyms)

    return list(search_terms)


def search_dictionary(keyword: str, dictionary: dict) -> list[tuple[str, dict]]:
    """
    Case-insensitive, partial-word search across term names, keywords,
    synonym expansion, and aliases list.

    Returns
    -------
    list of (term, details) tuples that matched.
    """
    search_terms = expand_with_synonyms(keyword)
    matches = []
    seen_terms = set()

    for term, details in dictionary.items():
        term_lower = term.lower()

        # Build comprehensive haystack including aliases
        keywords_list = [k.lower() for k in details.get("keywords", [])]
        aliases_list = [a.lower() for a in details.get("aliases", [])]
        haystack = [term_lower] + keywords_list + aliases_list

        if any(
            search_term in field
            for search_term in search_terms
            for field in haystack
        ):
            if term not in seen_terms:
                matches.append((term, details))
                seen_terms.add(term)

    return matches


def main():
    try:
        dictionary = load_json(DICTIONARY_FILE)
    except FileNotFoundError:
        logger.error(
            f"{DICTIONARY_FILE} not found. "
            f"Run scripts/build_dictionary.py first."
        )
        return

    keyword = input("Enter a keyword: ")
    matches = search_dictionary(keyword, dictionary)

    print("\nMatching Terms:\n")

    if not matches:
        print("No matching insurance term found.")
        return

    for term, details in matches:
        aliases = details.get("aliases", [])
        alias_str = f" (Aliases: {', '.join(aliases)})" if aliases else ""
        print(f"Term: {term}{alias_str}")
        print(f"Description: {details['description']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
