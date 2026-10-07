"""
Task 4 - Clause Analysis

Detects actual policy clauses with clean title extraction, unwraps multi-column
merged lines, performs exact duplicate clause detection with normalization,
and compares clauses across documents using RapidFuzz fuzzy title and content matching.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
from itertools import combinations
from rapidfuzz import fuzz

from config.settings import OUTPUT_DIR
from config.clauses import (
    CLAUSE_SECTION_HEADINGS,
    SIMILARITY_THRESHOLD,
    SIMILARITY_TEXT_LIMIT,
    TITLE_SIMILARITY_THRESHOLD,
)
from utils.logger import setup_logger
from utils.section_extractor import extract_sections
from utils.pdf_reader import clean_extracted_text
from utils.json_utils import save_json
from scripts.extract_sections import load_documents

logger = setup_logger()

# Regex for numbered clauses with optional trailing punctuation: e.g. "10 Fraud", "1.1 Coverage", "2) Claims"
CLAUSE_NUMBER_REGEX = re.compile(
    r"^\s*(\d+(?:\.\d+)*)[\.\)]?\s+(\S.*)$"
)

# Regex to unwrap multi-column merged lines like "10 Fraud 13 Law Applicable and Jurisdiction"
MULTI_COLUMN_SPLIT_REGEX = re.compile(
    r"(?<=[a-zA-Z])\s+(?=\d{1,2}\s+[A-Z][a-z])"
)


def preprocess_section_lines(text: str) -> list[str]:
    """
    Pre-split merged multi-column lines so two concatenated numbered items
    become separate lines before parsing.
    """
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        # Split on multi-column boundary if present
        parts = MULTI_COLUMN_SPLIT_REGEX.split(line)
        for part in parts:
            p = part.strip()
            if p:
                lines.append(p)
    return lines


def split_into_subclauses(text: str, parent_section_title: str) -> list[tuple[str, str, str]]:
    """
    Split a section's text into numbered sub-clauses with extracted titles.

    Returns
    -------
    list of (clause_number, clause_title, clause_content) tuples.
    Empty list if the text has no detectable numbering (len < 2).
    """
    lines = preprocess_section_lines(text)
    subclauses = []

    current_number = None
    current_title = None
    current_lines = []

    for line in lines:
        match = CLAUSE_NUMBER_REGEX.match(line)
        if match:
            num = match.group(1).strip()
            rest = match.group(2).strip()

            # If previous clause buffer exists, save it
            if current_number is not None:
                subclauses.append((
                    current_number,
                    current_title or parent_section_title,
                    "\n".join(current_lines).strip()
                ))

            current_number = num
            words_in_rest = rest.split()

            # If text immediately after the number is short (<= 8 words) and doesn't
            # end in comma or semicolon, treat it as the clause's own title
            if len(words_in_rest) <= 8 and not rest.endswith((",", ";", ":")):
                current_title = rest.strip(". ")
                current_lines = []
            else:
                # Body started on the same line; fallback to parent section title
                current_title = parent_section_title
                current_lines = [rest]
        else:
            if current_number is not None:
                current_lines.append(line)

    if current_number is not None:
        subclauses.append((
            current_number,
            current_title or parent_section_title,
            "\n".join(current_lines).strip()
        ))

    # Require >= 2 numbered items before trusting the numbering
    if len(subclauses) < 2:
        return []

    return subclauses


def build_clause_entries(document: dict, sections: list[dict]) -> list[dict]:
    """
    Turn a document's extracted sections into individual clause entries.
    All text fields are cleaned of non-printable artifacts and (cid:...) tokens.
    """
    entries = []

    for section in sections:
        section_name = clean_extracted_text(section["section"])
        # Match against clause-bearing headings (substring or exact match)
        is_clause_bearing = any(
            cb.lower() in section_name.lower() or section_name.lower() in cb.lower()
            for cb in CLAUSE_SECTION_HEADINGS
        )

        if not is_clause_bearing:
            continue

        sec_text = clean_extracted_text(section["text"])
        subclauses = split_into_subclauses(sec_text, section_name)

        if subclauses:
            for clause_number, clause_title, clause_content in subclauses:
                clean_title = clean_extracted_text(clause_title)
                clean_content = clean_extracted_text(clause_content)
                if len(clean_content) < 15:
                    continue

                entries.append({
                    "Clause Title": clean_title,
                    "Clause Number": clause_number,
                    "Clause Content": clean_content,
                    "Page Number": section["page"],
                    "Document Name": document["file_name"],
                    "Parent Section": section_name,
                })
        else:
            if len(sec_text) >= 20:
                entries.append({
                    "Clause Title": section_name,
                    "Clause Number": "",
                    "Clause Content": sec_text,
                    "Page Number": section["page"],
                    "Document Name": document["file_name"],
                    "Parent Section": section_name,
                })

    return entries


def normalize_clause_text(text: str) -> str:
    """
    Normalize text: convert to lowercase and collapse extra whitespaces.
    """
    text = clean_extracted_text(text or "")
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def detect_exact_duplicates(all_entries: list[dict]) -> tuple[dict, list[dict]]:
    """
    Detect exact duplicate clauses across all extracted entries.
    Normalizes clause content (lowercase, remove extra spaces) and compares exact values.
    Returns:
        statistics: dict with total_clauses, unique_clauses, exact_duplicates_count
        exact_duplicates: list of duplicate clusters with occurrences across documents
    """
    groups = {}
    for entry in all_entries:
        norm_content = normalize_clause_text(entry.get("Clause Content", ""))
        if not norm_content:
            continue
        groups.setdefault(norm_content, []).append(entry)

    exact_duplicates_list = []
    total_duplicate_copies = 0

    for norm_content, entries in groups.items():
        if len(entries) > 1:
            copies = len(entries) - 1
            total_duplicate_copies += copies
            exact_duplicates_list.append({
                "clause_title": entries[0]["Clause Title"],
                "sample_content": entries[0]["Clause Content"][:250],
                "occurrences_count": len(entries),
                "occurrences": [
                    {
                        "document": e["Document Name"],
                        "clause_title": e["Clause Title"],
                        "clause_number": e["Clause Number"],
                        "page": e["Page Number"],
                    }
                    for e in entries
                ],
            })

    # Sort duplicate clusters by occurrences descending
    exact_duplicates_list.sort(key=lambda d: d["occurrences_count"], reverse=True)

    total_clauses = len(all_entries)
    unique_clauses = total_clauses - total_duplicate_copies

    stats = {
        "total_clauses": total_clauses,
        "unique_clauses": unique_clauses,
        "exact_duplicates_count": total_duplicate_copies,
    }

    return stats, exact_duplicates_list


def find_similar_clauses(all_entries: list[dict]) -> list[dict]:
    """
    Compare clauses across *different* documents using RapidFuzz token_sort_ratio
    on clause titles (~70) and content ratio (~0.35), or accept high title match (>=95).
    """
    similar_pairs = []

    for entry_a, entry_b in combinations(all_entries, 2):
        # Only compare clauses from different documents
        if entry_a["Document Name"] == entry_b["Document Name"]:
            continue

        title_a = entry_a["Clause Title"]
        title_b = entry_b["Clause Title"]

        # 1. Fuzzy match on clause titles using token_sort_ratio
        title_similarity = fuzz.token_sort_ratio(title_a.lower(), title_b.lower())

        if title_similarity < TITLE_SIMILARITY_THRESHOLD:
            continue

        # 2. Compare clause contents
        text_a = entry_a["Clause Content"][:SIMILARITY_TEXT_LIMIT]
        text_b = entry_b["Clause Content"][:SIMILARITY_TEXT_LIMIT]

        # rapidfuzz ratio returns 0-100; scale to 0-1
        content_ratio = round(fuzz.ratio(text_a, text_b) / 100.0, 3)

        # Accept if content similarity >= threshold OR if title similarity >= 95
        if content_ratio >= SIMILARITY_THRESHOLD or title_similarity >= 95:
            similar_pairs.append({
                "Clause Title": title_a if title_a == title_b else f"{title_a} / {title_b}",
                "Clause Title A": title_a,
                "Clause Title B": title_b,
                "Document A": entry_a["Document Name"],
                "Clause Number A": entry_a["Clause Number"],
                "Document B": entry_b["Document Name"],
                "Clause Number B": entry_b["Clause Number"],
                "Title Similarity": round(title_similarity, 1),
                "Similarity": content_ratio,
                "Content Similarity": content_ratio,
            })

    # Sort by title similarity and content similarity descending
    similar_pairs.sort(key=lambda p: (p["Title Similarity"], p["Similarity"]), reverse=True)
    return similar_pairs


def main():
    logger.info("Starting Task 4 - Clause Analysis")

    documents = load_documents()
    all_entries = []

    for document in documents:
        sections = extract_sections(document)
        entries = build_clause_entries(document, sections)
        all_entries.extend(entries)

        logger.info(
            f"{document['file_name']} -> {len(entries)} clauses extracted."
        )

    # 1. Detect exact duplicates with normalization (lowercase, whitespace collapse)
    stats, exact_duplicates = detect_exact_duplicates(all_entries)

    # 2. Find cross-document fuzzy similar clauses with RapidFuzz
    similar_pairs = find_similar_clauses(all_entries)

    output = {
        "statistics": stats,
        "clauses": all_entries,
        "exact_duplicates": exact_duplicates,
        "similar_clauses": similar_pairs,
    }

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "clauses.json"

    save_json(output, output_file)
    logger.info(f"Results saved to {output_file}")

    print("\nClause Analysis Summary")
    print("-" * 60)
    print(f"Documents processed        : {len(documents)}")
    print(f"Total clauses found        : {stats['total_clauses']}")
    print(f"Unique clauses             : {stats['unique_clauses']}")
    print(f"Exact duplicate clauses    : {stats['exact_duplicates_count']}")
    print(f"Similar clause pairs       : {len(similar_pairs)}")

    # Show pairs where Title A != Title B to demonstrate fuzzy title matching
    diff_title_pairs = [p for p in similar_pairs if p["Clause Title A"].lower() != p["Clause Title B"].lower()]
    print(f"Pairs with differently-worded titles (Title A != Title B): {len(diff_title_pairs)}")

    if diff_title_pairs:
        print("\nSample differently-worded matching clause pairs:")
        for pair in diff_title_pairs[:8]:
            print(
                f"  - '{pair['Clause Title A']}' ({pair['Document A']}) <-> "
                f"'{pair['Clause Title B']}' ({pair['Document B']}) | "
                f"Title Sim: {pair['Title Similarity']}% | Content Sim: {pair['Similarity']}"
            )


if __name__ == "__main__":
    main()
