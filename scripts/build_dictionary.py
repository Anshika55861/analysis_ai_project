"""
Task 3 - Build Insurance Dictionary

Automatically extracts insurance terms and their definitions from every
document section (using DEFINITION_TRIGGERS from config), deduplicates
case-insensitively, and groups similar terms into clusters with canonical
entries and aliases using RapidFuzz with an explicit antonym guard.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
from rapidfuzz import fuzz

from config.settings import OUTPUT_DIR
from config.patterns import DEFINITION_TRIGGERS
from utils.logger import setup_logger
from utils.section_extractor import extract_sections
from utils.json_utils import save_json, load_json
from scripts.extract_sections import load_documents

logger = setup_logger()

DICTIONARY_FILE = OUTPUT_DIR / "insurance_dictionary.json"

# Matches "Term means definition." / "Term shall mean definition." / "Term refers to definition."
DEFINITION_PATTERN = re.compile(
    r"(?P<term>[A-Z][A-Za-z()/&,'\- ]{1,45}?)\s+"
    r"(?:means|shall mean|refers to)\s+"
    r"(?P<definition>.+?)(?:\.\s|\.$|\n\n)",
    flags=re.DOTALL,
)

# Known antonym and opposing party pairs that must NEVER be grouped as synonyms/aliases
ANTONYM_PAIRS = {
    ("major", "minor"),
    ("minor", "major"),
    ("before", "after"),
    ("after", "before"),
    ("primary", "secondary"),
    ("secondary", "primary"),
    ("temporary", "permanent"),
    ("permanent", "temporary"),
    ("initial", "final"),
    ("final", "initial"),
    ("first", "second"),
    ("second", "first"),
    ("upper", "lower"),
    ("lower", "upper"),
    ("inpatient", "outpatient"),
    ("outpatient", "inpatient"),
    ("direct", "indirect"),
    ("indirect", "direct"),
    ("partial", "total"),
    ("total", "partial"),
    ("voluntary", "compulsory"),
    ("compulsory", "voluntary"),
    ("gross", "net"),
    ("net", "gross"),
    ("insured", "insurer"),
    ("insurer", "insured"),
    ("lessor", "lessee"),
    ("lessee", "lessor"),
}


def clean_definition(text: str) -> str:
    """Collapse whitespace and newlines inside a captured definition."""
    return re.sub(r"\s+", " ", text or "").strip()


def build_keywords(term: str) -> list[str]:
    """
    Build a search keyword list: term (lowercase) plus individual words.
    """
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", term)]
    keywords = list(dict.fromkeys([term.lower()] + words))
    return keywords


def are_antonyms(term_a: str, term_b: str) -> bool:
    """
    Check if two candidate terms differ by exactly one word that forms
    a known antonym or opposing legal party pair.
    """
    words_a = [w.lower() for w in re.findall(r"[A-Za-z]+", term_a)]
    words_b = [w.lower() for w in re.findall(r"[A-Za-z]+", term_b)]

    if len(words_a) != len(words_b):
        return False

    diffs = []
    for wa, wb in zip(words_a, words_b):
        if wa != wb:
            diffs.append((wa, wb))

    if len(diffs) == 1:
        if tuple(diffs[0]) in ANTONYM_PAIRS:
            return True

    return False


def extract_terms_from_text(text: str) -> dict[str, dict]:
    """
    Scan a block of text for 'Term means/shall mean/refers to definition' sentences.
    """
    terms = {}
    for match in DEFINITION_PATTERN.finditer(text):
        term = match.group("term").strip()
        definition = clean_definition(match.group("definition"))

        # Skip junk matches: too short term or definition
        if len(term) < 3 or len(definition) < 10:
            continue

        # Clean trailing punctuation from term
        term_clean = term.strip(" ,;:-")
        if not term_clean:
            continue

        terms[term_clean] = {
            "description": definition,
            "keywords": build_keywords(term_clean),
        }

    return terms


def deduplicate_terms(raw_terms: dict[str, dict]) -> dict[str, dict]:
    """
    Deduplicate terms case-insensitively, retaining the longest/most complete definition.
    """
    deduped = {}
    lower_map = {}

    for term, data in raw_terms.items():
        key = term.lower()
        if key in lower_map:
            existing_term = lower_map[key]
            existing_desc = deduped[existing_term]["description"]
            # Keep the longer description
            if len(data["description"]) > len(existing_desc):
                del deduped[existing_term]
                deduped[term] = data
                lower_map[key] = term
            else:
                # Merge keywords
                for kw in data.get("keywords", []):
                    if kw not in deduped[existing_term]["keywords"]:
                        deduped[existing_term]["keywords"].append(kw)
        else:
            deduped[term] = data
            lower_map[key] = term

    return deduped


def group_similar_terms(
    terms_dict: dict[str, dict],
    similarity_threshold: float = 82.0
) -> dict[str, dict]:
    """
    Group similar term names with RapidFuzz token_sort_ratio (threshold ~82)
    into canonical clusters with an 'aliases' list, respecting the antonym guard.
    """
    term_names = list(terms_dict.keys())
    grouped_dictionary = {}
    assigned_terms = set()

    for i, term_a in enumerate(term_names):
        if term_a in assigned_terms:
            continue

        cluster_aliases = []
        best_desc = terms_dict[term_a]["description"]
        all_keywords = list(terms_dict[term_a].get("keywords", []))

        for j in range(i + 1, len(term_names)):
            term_b = term_names[j]
            if term_b in assigned_terms:
                continue

            # Antonym guard: Never group if terms differ by an antonym pair
            if are_antonyms(term_a, term_b):
                continue

            score = fuzz.token_sort_ratio(term_a.lower(), term_b.lower())
            if score >= similarity_threshold:
                cluster_aliases.append(term_b)
                assigned_terms.add(term_b)

                # Keep longer description
                if len(terms_dict[term_b]["description"]) > len(best_desc):
                    best_desc = terms_dict[term_b]["description"]

                for kw in terms_dict[term_b].get("keywords", []):
                    if kw not in all_keywords:
                        all_keywords.append(kw)

        grouped_dictionary[term_a] = {
            "description": best_desc,
            "keywords": all_keywords,
            "aliases": cluster_aliases,
        }
        assigned_terms.add(term_a)

    return grouped_dictionary


def is_definition_section(section_name: str) -> bool:
    """
    Check if a section heading matches any configured definition trigger.
    """
    sec_lower = section_name.lower()
    return any(trigger.lower() in sec_lower for trigger in DEFINITION_TRIGGERS)


def main():
    logger.info("Starting Task 3 - Build Insurance Dictionary")

    # Load existing hand-curated dictionary as seed (strip stale aliases before grouping)
    seed_terms = {}
    if DICTIONARY_FILE.exists():
        try:
            raw_seed = load_json(DICTIONARY_FILE)
            for term, data in raw_seed.items():
                seed_terms[term] = {
                    "description": data.get("description", ""),
                    "keywords": data.get("keywords", build_keywords(term)),
                }
            logger.info(f"Loaded {len(seed_terms)} existing seed terms.")
        except Exception as e:
            logger.warning(f"Could not load existing dictionary seed: {e}")

    documents = load_documents()
    raw_collected_terms = dict(seed_terms)
    total_sections_scanned = 0

    for document in documents:
        sections = extract_sections(document)

        for section in sections:
            total_sections_scanned += 1
            # Scan all sections, especially definition-bearing ones
            found_terms = extract_terms_from_text(section["text"])
            for term, details in found_terms.items():
                if term not in raw_collected_terms or len(details["description"]) > len(raw_collected_terms[term]["description"]):
                    raw_collected_terms[term] = details

    # 1. Deduplicate case-insensitively
    deduped_terms = deduplicate_terms(raw_collected_terms)

    # 2. Group similar terms into canonical entries with aliases
    grouped_dictionary = group_similar_terms(deduped_terms, similarity_threshold=82.0)

    OUTPUT_DIR.mkdir(exist_ok=True)
    save_json(grouped_dictionary, DICTIONARY_FILE)

    # Summary
    grouped_with_aliases = {
        term: data["aliases"]
        for term, data in grouped_dictionary.items()
        if data.get("aliases")
    }

    logger.info(
        f"Dictionary saved to {DICTIONARY_FILE} ({len(grouped_dictionary)} entries total)."
    )

    print("\nInsurance Dictionary Build Summary")
    print("-" * 50)
    print(f"Total sections scanned    : {total_sections_scanned}")
    print(f"Raw terms collected       : {len(raw_collected_terms)}")
    print(f"Terms after dedup         : {len(deduped_terms)}")
    print(f"Final canonical entries   : {len(grouped_dictionary)}")
    print(f"Entries with aliases      : {len(grouped_with_aliases)}")

    if grouped_with_aliases:
        print("\nSample grouped entries with aliases:")
        for term, aliases in list(grouped_with_aliases.items())[:6]:
            print(f"  • {term} -> aliases: {aliases}")


if __name__ == "__main__":
    main()
