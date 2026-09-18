"""
Task 9 - Classify Insurance Clauses

Categorizes insurance clauses across policy documents into 6 standard insurance categories:
1. Coverage
2. Exclusion
3. Definition
4. Condition
5. Extension
6. Limitation

Outputs:
- output/classified_clauses.json
"""

import os
import sys
import json
import re
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR
from utils.logger import setup_logger
from utils.json_utils import save_json, load_json
from utils.pdf_reader import clean_extracted_text

logger = setup_logger()

# Classification category rules
CATEGORY_KEYWORDS = {
    "Exclusion": [
        r"\bwill\s+not\s+(?:pay|cover|indemnify|be\s+liable)\b",
        r"\bshall\s+not\s+(?:pay|cover|indemnify|apply|be\s+liable)\b",
        r"\bnot\s+covered\b",
        r"\bexcluded\b",
        r"\bexclusion\b",
        r"\bexcept\s+for\b",
        r"\buninsured\b",
        r"\bno\s+liability\b",
        r"\bwar\b|\bterrorism\b|\bnuclear\b|\bradioactive\b|\bpollution\b|\bdeliberate\b|\bpre-existing\b",
        r"\binjuries\s+that\s+occur\s+as\s+a\s+result\b",
        r"\bunder\s+the\s+influence\s+of\b",
        r"\bwhile\s+committing\s+a\s+felony\b"
    ],
    "Coverage": [
        r"\bagrees?\s+to\s+(?:pay|indemnify|cover)\b",
        r"\bwill\s+(?:pay|cover|indemnify)\b",
        r"\bshall\s+(?:pay|cover|indemnify)\b",
        r"\boperative\s+clause\b",
        r"\binsuring\s+agreement\b",
        r"\binsuring\s+clause\b",
        r"\bscope\s+of\s+cover\b",
        r"\bwhat\s+is\s+covered\b",
        r"\bbenefit\b",
        r"\bentitled\s+to\s+receive\b",
        r"\bloss\s+or\s+damage\s+caused\s+by\b",
        r"\binsured\s+events?\b",
        r"\bindemnify\s+the\s+insured\b"
    ],
    "Definition": [
        r"\bmeans?\b",
        r"\bshall\s+mean\b",
        r"\bdefined\s+as\b",
        r"\bdefinition\b",
        r"\brefers\s+to\b",
        r"\bwords\s+(?:in\s+bold|defined)\b",
        r"\bany\s+person\s+who\b",
        r"\bshall\s+include\b"
    ],
    "Extension": [
        r"\bextension\b",
        r"\bextended\s+to\s+include\b",
        r"\badditional\s+benefit\b",
        r"\boptional\s+cover\b",
        r"\bautomatic\s+extension\b",
        r"\bin\s+addition\s+to\b",
        r"\bsupplementary\s+payment\b",
        r"\bendorsement\b"
    ],
    "Limitation": [
        r"\bshall\s+not\s+exceed\b",
        r"\bmaximum\s+(?:amount|limit|benefit|payable)\b",
        r"\bsub-?limit\b",
        r"\bexcess\b",
        r"\bdeductible\b",
        r"\blimit\s+of\s+liability\b",
        r"\baggregate\s+limit\b",
        r"\binner\s+limit\b",
        r"\bwhichever\s+(?:is\s+the\s+)?lesser\b",
        r"\bup\s+to\s+(?:a\s+maximum\s+of|the\s+sum)\b"
    ],
    "Condition": [
        r"\bcondition\b",
        r"\bprecedent\s+to\s+liability\b",
        r"\bduty\s+of\s+disclosure\b",
        r"\bmust\s+(?:give\s+notice|notify|comply|provide)\b",
        r"\bshall\s+(?:give\s+notice|notify|cooperate)\b",
        r"\bcancellation\b",
        r"\barbitration\b",
        r"\blaw\s+and\s+jurisdiction\b",
        r"\bclaims?\s+procedure\b",
        r"\bsubrogation\b",
        r"\bfraud\b",
        r"\breasonable\s+precautions\b",
        r"\balteration\s+in\s+risk\b",
        r"\byour\s+duty\b"
    ]
}


def classify_clause(title: str, text: str, parent_section: str = "") -> tuple[str, float, str]:
    """
    Classifies a clause text into one of the 6 categories using section context,
    title semantics, and lexical regex patterns.
    """
    title_clean = clean_extracted_text(title)
    text_clean = clean_extracted_text(text)
    sec_clean = clean_extracted_text(parent_section)

    title_lower = title_clean.lower()
    text_lower = text_clean.lower()
    sec_lower = sec_clean.lower()
    combined_ctx = f"{sec_lower} {title_lower}"

    scores = {
        "Coverage": 0.0,
        "Exclusion": 0.0,
        "Definition": 0.0,
        "Condition": 0.0,
        "Extension": 0.0,
        "Limitation": 0.0
    }
    reasons = {cat: [] for cat in scores}

    # Context title weights
    if any(w in combined_ctx for w in ["exclusion", "except", "what is not covered", "uninsured"]):
        scores["Exclusion"] += 4.0
        reasons["Exclusion"].append("Section/Title indicates Exclusion")
    if any(w in combined_ctx for w in ["definition", "meaning of words", "interpretation", "defined terms"]):
        scores["Definition"] += 4.0
        reasons["Definition"].append("Section/Title indicates Definition")
    if any(w in combined_ctx for w in ["condition", "general provisions", "claims procedure", "duty", "jurisdiction", "cancellation"]):
        scores["Condition"] += 4.0
        reasons["Condition"].append("Section/Title indicates Condition")
    if any(w in combined_ctx for w in ["extension", "additional benefit", "endorsement", "optional extension"]):
        scores["Extension"] += 4.0
        reasons["Extension"].append("Section/Title indicates Extension")
    if any(w in combined_ctx for w in ["limit", "excess", "deductible", "basis of settlement", "maximum payable"]):
        scores["Limitation"] += 4.0
        reasons["Limitation"].append("Section/Title indicates Limitation")
    if any(w in combined_ctx for w in ["cover", "insuring clause", "benefit", "what is covered", "operative", "indemnity"]):
        scores["Coverage"] += 4.0
        reasons["Coverage"].append("Section/Title indicates Coverage")

    # Pattern scanning in content
    for cat, patterns in CATEGORY_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                scores[cat] += 1.5
                reasons[cat].append(f"Matched pattern '{pat}'")

    # Content-specific heuristics
    if re.search(r"^\s*['\"]?[A-Z][A-Za-z\s]+['\"]?\s+(?:means|shall mean|refers to)\b", text_clean):
        scores["Definition"] += 3.0
        reasons["Definition"].append("Explicit Definition pattern")

    if re.search(r"\b(?:excess|deductible)\s+(?:of\s+)?(?:£|\$|THB|\d+)\b", text_lower):
        scores["Limitation"] += 2.5
        reasons["Limitation"].append("Excess/Deductible monetary limit")

    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]

    if max_score == 0:
        best_cat = "Condition"
        confidence = 0.50
        rationale = "Default fallback classification"
    else:
        confidence = min(0.95, round(0.60 + (max_score / 15.0), 2))
        rationale = "; ".join(reasons[best_cat][:2])

    return best_cat, confidence, rationale


def extract_additional_section_clauses(sections_data: dict) -> list[dict]:
    """
    Extracts clauses from Definitions, Extensions, Conditions, and Limits sections
    to ensure full coverage across all 6 insurance categories.
    """
    extracted = []

    for doc_name, sec_list in sections_data.items():
        for sec in sec_list:
            sec_name = sec.get("section", "")
            sec_text = sec.get("text", "")
            page = sec.get("page", 1)

            paragraphs = [clean_extracted_text(p) for p in sec_text.split("\n\n") if len(clean_extracted_text(p)) > 30]
            if not paragraphs:
                paragraphs = [clean_extracted_text(line) for line in sec_text.splitlines() if len(clean_extracted_text(line)) > 40]

            for idx, para in enumerate(paragraphs[:15]):
                if "(cid:" in para or len(para.split()) < 5:
                    continue
                first_line = para.splitlines()[0].strip()
                title = first_line[:60] if len(first_line) > 5 else sec_name

                extracted.append({
                    "Clause Title": title,
                    "Clause Number": str(idx + 1),
                    "Clause Content": para,
                    "Page Number": page,
                    "Document Name": doc_name,
                    "Parent Section": sec_name
                })

    return extracted


def main():
    logger.info("Starting Task 9: Classify Insurance Clauses (Clean & Dynamic)...")

    clauses_file = OUTPUT_DIR / "clauses.json"
    sections_file = OUTPUT_DIR / "sections.json"

    all_raw_clauses = []

    if clauses_file.exists():
        data = load_json(clauses_file)
        clause_items = data.get("clauses", []) if isinstance(data, dict) else data
        for c in clause_items:
            clean_c = {
                "Clause Title": clean_extracted_text(c.get("Clause Title", "")),
                "Clause Number": c.get("Clause Number", ""),
                "Clause Content": clean_extracted_text(c.get("Clause Content", "")),
                "Page Number": c.get("Page Number", 1),
                "Document Name": c.get("Document Name", ""),
                "Parent Section": clean_extracted_text(c.get("Parent Section", ""))
            }
            if "(cid:" not in clean_c["Clause Content"] and len(clean_c["Clause Content"].split()) >= 4:
                all_raw_clauses.append(clean_c)

    if sections_file.exists():
        sec_data = load_json(sections_file)
        sec_clauses = extract_additional_section_clauses(sec_data)
        all_raw_clauses.extend(sec_clauses)

    # Deduplicate by text content
    seen_texts = set()
    unique_clauses = []
    for c in all_raw_clauses:
        txt = (c.get("Clause Content") or "").strip()
        if txt and txt not in seen_texts:
            seen_texts.add(txt)
            unique_clauses.append(c)

    classified_results = []
    category_counts = {
        "Coverage": 0,
        "Exclusion": 0,
        "Definition": 0,
        "Condition": 0,
        "Extension": 0,
        "Limitation": 0
    }

    for item in unique_clauses:
        title = item.get("Clause Title", "")
        content = item.get("Clause Content", "")
        parent_sec = item.get("Parent Section", "")
        doc = item.get("Document Name", "")
        page = item.get("Page Number", 1)
        clause_num = item.get("Clause Number", "")

        cat, conf, rationale = classify_clause(title, content, parent_sec)
        category_counts[cat] += 1

        classified_results.append({
            "clause": content,
            "category": cat,
            "document": doc,
            "clause_title": title,
            "clause_number": clause_num,
            "page": page,
            "confidence": conf,
            "rationale": rationale
        })

    out_file = OUTPUT_DIR / "classified_clauses.json"
    save_json(classified_results, out_file)
    logger.info(f"Task 9 Complete: Saved {len(classified_results)} clean classified clauses to {out_file}")

    print("\n--- Clause Category Distribution (Task 9) ---")
    for cat, count in category_counts.items():
        print(f"  {cat:12s}: {count:4d} clauses")


if __name__ == "__main__":
    main()
