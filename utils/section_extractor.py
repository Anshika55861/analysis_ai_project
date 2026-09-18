"""
Reusable Section Extraction Utility

Extract complete insurance document sections using both keyword matching
and PyMuPDF layout-based heading detection with RapidFuzz.

Features
--------
- Line-by-line heading detection with keyword and layout support
- RapidFuzz fuzzy matching for layout candidates (threshold ~85)
- Document body font size baseline comparison with hard size gating
- Automatic stripping of "(continued)" suffixes to prevent duplicate sections
- Automated dropping of empty section fragments
- Start/end page and text position tracking
- Merges multi-page sections seamlessly
- Advanced text sanitization removing (cid:...) tokens
"""

import re
from pathlib import Path
from rapidfuzz import fuzz

from config.sections import SECTION_HEADINGS
from utils.logger import setup_logger
from utils.heading_detector import detect_layout_headings
from utils.pdf_reader import clean_extracted_text

logger = setup_logger()

# Regex to strip (continued), continued, etc. from heading names
CONTINUED_SUFFIX_REGEX = re.compile(
    r"\s*[-–—:]?\s*(\(?continued\)?|\(?cont\.?\)?)\s*$",
    flags=re.IGNORECASE
)


def normalize_line(text: str) -> str:
    """
    Normalize whitespace and strip a single line before matching.
    """
    text = clean_extracted_text(text)
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def strip_continued_suffix(heading: str) -> str:
    """
    Strip 'continued' or '(continued)' from heading names.
    """
    cleaned = CONTINUED_SUFFIX_REGEX.sub("", heading).strip()
    return cleaned if cleaned else heading


def match_heading(line: str, page_candidates: list[str] | None = None) -> tuple[str | None, str | None]:
    """
    Match a line against configured section headings using:
    1. Exact / pattern matching against configured SECTION_HEADINGS keywords
    2. Fuzzy matching against PyMuPDF layout candidates (if provided)
    """
    norm = normalize_line(line)
    if not norm or len(norm) < 3:
        return None, None

    # 1. Check keyword headings
    for heading in SECTION_HEADINGS:
        # Exact match or starts-with match for numbered headings (e.g. "Section 1 - Definitions")
        if norm.lower() == heading.lower():
            return heading, "keyword_exact"
        if re.match(rf"^(?:Section\s+\d+\s*[-–—:]?\s*|Part\s+[A-Z]\s*[-–—:]?\s*)?{re.escape(heading)}\b", norm, re.IGNORECASE):
            return norm, "keyword_pattern"

    # 2. Check layout candidates
    if page_candidates:
        for cand in page_candidates:
            c_norm = normalize_line(cand)
            if not c_norm:
                continue
            ratio = fuzz.ratio(norm.lower(), c_norm.lower())
            if ratio >= 85:
                return c_norm, "layout"

    return None, None


def is_heading(line: str, page_candidates: list[str] | None = None) -> str | None:
    """
    Returns the matching heading string if this line is a section heading.
    """
    heading, _ = match_heading(line, page_candidates)
    return heading


def extract_sections(document: dict, layout_headings: dict | None = None) -> list[dict]:
    """
    Extract sections from a document dict (from read_pdf).
    """
    pages = document.get("pages", [])
    if not pages:
        return []

    if layout_headings is None:
        doc_path = document.get("path")
        if doc_path and Path(doc_path).exists():
            layout_headings = detect_layout_headings(doc_path)
        else:
            layout_headings = {}

    sections = []
    current_section = None
    current_method = None
    current_text = []
    start_page = None
    start_position = 0
    global_position = 0

    for page in pages:
        page_number = page["page_number"]
        page_candidates = layout_headings.get(page_number, []) if layout_headings else []
        lines = page.get("text", "").splitlines()

        for line in lines:
            line_clean = clean_extracted_text(line)
            heading, method = match_heading(line_clean, page_candidates)

            if heading:
                heading = strip_continued_suffix(heading)

                if current_section:
                    raw_text = clean_extracted_text("\n".join(current_text).strip())
                    if raw_text:
                        sections.append({
                            "section": current_section,
                            "page": start_page,
                            "end_page": page_number,
                            "start_position": start_position,
                            "end_position": global_position,
                            "text": raw_text,
                            "detection_method": current_method or "keyword",
                        })

                current_section = heading
                current_method = method
                current_text = []
                start_page = page_number
                start_position = global_position
            else:
                if current_section:
                    current_text.append(line_clean)

            global_position += len(line_clean) + 1

    if current_section:
        raw_text = clean_extracted_text("\n".join(current_text).strip())
        if raw_text:
            sections.append({
                "section": current_section,
                "page": start_page,
                "end_page": pages[-1]["page_number"],
                "start_position": start_position,
                "end_position": global_position,
                "text": raw_text,
                "detection_method": current_method or "keyword",
            })

    # Drop any remaining empty sections
    sections = [s for s in sections if s["text"].strip()]

    # Merge consecutive identical sections
    sections = merge_duplicate_sections(sections)

    logger.info(
        f"{document.get('file_name', 'Doc')} -> {len(sections)} sections extracted."
    )

    return sections


def merge_duplicate_sections(sections: list[dict]) -> list[dict]:
    """
    Merge duplicate sections spanning multiple pages or consecutive blocks.
    """
    merged = []

    for section in sections:
        if merged and merged[-1]["section"] == section["section"]:
            merged[-1]["text"] = clean_extracted_text(merged[-1]["text"] + "\n" + section["text"])
            merged[-1]["end_page"] = section["end_page"]
            merged[-1]["end_position"] = section["end_position"]
        else:
            merged.append(section)

    return merged