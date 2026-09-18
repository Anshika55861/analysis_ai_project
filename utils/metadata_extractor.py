"""
Multi-Method Metadata Extraction Utility

Extracts key metadata fields from insurance documents using multiple
independent methods per field, scoring each candidate with a confidence
level and selecting the highest-confidence non-empty result.

Methods per field:
- Policy Name:
  (a) text_order (0.55 / 0.75 on trigger phrase)
  (b) explicit_pattern (0.65, [ \\t]+ word boundary, >=2 Title Case words)
  (c) layout_fitz (0.50 / 0.80 for prominent title-font text on page 1)
- Insurance Company Name:
  (a) suffix_match (0.85, insurer keyword in first 5 words, legal suffix at end,
      <=12 words, sentence continuation filter)
  (b) keyword_only (0.45, <=12 words)
  (c) layout_fitz (0.50, short bold text with insurer keyword)
- Policy Type, Effective Date, Document Version:
  Standardized (value, confidence, method) wrappers over configured patterns.
"""

import re
from pathlib import Path
import pymupdf as fitz

from config.patterns import (
    POLICY_TYPES,
    COMPANY_SUFFIXES,
    COMPANY_KEYWORDS,
    EFFECTIVE_DATE_TRIGGERS,
    DATE_PATTERN,
    VERSION_PATTERNS,
)
from utils.logger import setup_logger

logger = setup_logger()

# Stoplist for page 1 marketing taglines / non-title lines
MARKETING_TAGLINES = (
    "welcome to",
    "welcome",
    "thank you for choosing",
    "thank you",
    "dares to tell",
    "dares to",
    "insurance that",
    "important",
    "allianz.co.uk",
    "please use",
    "please read",
    "www.",
    "http",
)

# Marketing prefixes to strip from company candidate lines
MARKETING_PREFIX_REGEX = re.compile(
    r"^(?:thank\s+you\s+(?:for\s+choosing)?|welcome\s+to|for\s+more\s+information\s+about)\s+",
    flags=re.IGNORECASE
)

# Sentence continuation words that reject a candidate if trailing after a company suffix or ending a title
SENTENCE_CONTINUATION_WORDS = {
    "we", "us", "our", "you", "your", "are", "is", "one", "and", "which",
    "who", "that", "the", "a", "an", "for", "in", "to", "with"
}

# Policy name trigger phrases
POLICY_NAME_TRIGGERS = (
    "policy wording",
    "terms and conditions",
    "terms & conditions",
    "product disclosure",
    "policy document",
)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip text."""
    return re.sub(r"[ \t]+", " ", text or "").strip()


# ---------------------------------------------------------------------------
# Policy Name Extraction Methods
# ---------------------------------------------------------------------------

def extract_policy_name_text_order(lines: list[str]) -> tuple[str, float, str]:
    """
    Method (a): Scan the first few non-empty lines on page 1 before a trigger
    phrase like 'policy wording' appears.
    """
    title_lines = []
    hit_trigger = False

    for line in lines[:8]:
        norm = line.strip()
        if not norm:
            continue
        lowered = norm.lower()

        if any(trigger in lowered for trigger in POLICY_NAME_TRIGGERS):
            hit_trigger = True
            break

        if any(tag in lowered for tag in MARKETING_TAGLINES):
            continue

        # Skip standalone company names / URLs on line 1
        if any(kw in lowered for kw in ("allianz.co.uk", "insurance plc", "limited")):
            continue

        title_lines.append(norm)

    if title_lines:
        name = " ".join(title_lines[:3]).strip()
        confidence = 0.75 if hit_trigger else 0.55
        return name, confidence, "text_order"

    return "", 0.0, "text_order"


def extract_policy_name_explicit_pattern(text: str) -> tuple[str, float, str]:
    """
    Method (b): Match explicit regex patterns for '<Title Case Words> Policy'
    or 'Policy: <Name>'.
    Uses [ \\t]+ to prevent matching across line breaks, requires >=2 Title-Case
    words and rejects single generic words.
    """
    pattern1 = re.compile(
        r"\b([A-Z][a-z]+(?:[ \t]+(?:and|&|[A-Z][a-z]+))+[ \t]+(?:Policy|Plan|Cover|Insurance|Proposal))\b"
    )
    pattern2 = re.compile(
        r"\b(?:Policy|Product)[ \t]*:[ \t]*([A-Z][a-z]+(?:[ \t]+(?:and|&|[A-Z][a-z]+))+)\b"
    )

    for line in text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue

        m = pattern2.search(line_clean) or pattern1.search(line_clean)
        if m:
            candidate = m.group(1).strip()
            words = candidate.split()
            if len(words) >= 2 and not any(tag in candidate.lower() for tag in ("thank you", "welcome to", "insurance that")):
                return candidate, 0.65, "explicit_pattern"

    return "", 0.0, "explicit_pattern"


def extract_policy_name_layout_fitz(pdf_path: str | Path) -> tuple[str, float, str]:
    """
    Method (c): Find the largest-font title block on page 1 (<=8 words),
    skipping marketing taglines and boosting confidence when prominent.
    """
    path_obj = Path(pdf_path) if pdf_path else None
    if not path_obj or not path_obj.exists():
        return "", 0.0, "layout_fitz"

    try:
        doc = fitz.open(str(path_obj))
        if len(doc) == 0:
            doc.close()
            return "", 0.0, "layout_fitz"

        page = doc[0]
        blocks = page.get_text("dict").get("blocks", [])
        candidates = []

        for block in blocks:
            if block.get("type") != 0:
                continue

            block_text_lines = []
            max_block_size = 0.0

            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                line_text = clean_text(" ".join(s.get("text", "") for s in spans))
                if line_text:
                    block_text_lines.append(line_text)
                    max_block_size = max(max_block_size, max(s.get("size", 0.0) for s in spans))

            full_block_text = clean_text(" ".join(block_text_lines))
            if not full_block_text or len(full_block_text) < 3:
                continue

            words = full_block_text.split()
            if len(words) > 8:
                continue

            lowered = full_block_text.lower()
            if any(tag in lowered for tag in MARKETING_TAGLINES):
                continue

            # Don't pick lines ending in sentence continuation words
            last_word = re.sub(r"[^\w]", "", words[-1].lower())
            if last_word in SENTENCE_CONTINUATION_WORDS:
                continue

            # Don't pick bare URLs or pure company names as policy title if other titles exist
            if "allianz.co.uk" in lowered:
                continue

            candidates.append((max_block_size, full_block_text))

        doc.close()

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_size, best_text = candidates[0]
            lowered = best_text.lower()
            has_policy_kw = any(
                kw in lowered for kw in ("plan", "policy", "cover", "insurance", "guarantee", "accident", "directors", "officers", "cargo")
            )
            # Prominent page-1 title font (>= 24pt) gives high confidence
            if best_size >= 24.0 and has_policy_kw:
                confidence = 0.80
            elif has_policy_kw:
                confidence = 0.60
            else:
                confidence = 0.50
            return best_text, confidence, "layout_fitz"

    except Exception as e:
        logger.debug(f"Layout policy name extraction error: {e}")

    return "", 0.0, "layout_fitz"


# ---------------------------------------------------------------------------
# Insurance Company Name Extraction Methods
# ---------------------------------------------------------------------------

def extract_company_name_suffix_match(lines: list[str]) -> tuple[str, float, str]:
    """
    Method (a): Match a line containing an insurer keyword within the first 5 words
    and a recognized legal company suffix near the end of the line.
    Caps at <= 12 words and guards against trailing sentence continuation words.
    """
    for line in lines:
        cleaned = clean_text(line)
        # Strip marketing greetings like "Thank you for choosing "
        cleaned_no_prefix = MARKETING_PREFIX_REGEX.sub("", cleaned).strip()

        words = cleaned_no_prefix.split()
        if not (1 <= len(words) <= 12):
            continue

        lowered = cleaned_no_prefix.lower()
        first_5_words = " ".join(words[:5]).lower()

        # Insurer keyword within first 5 words
        if not any(kw in first_5_words for kw in COMPANY_KEYWORDS):
            continue

        for suffix in COMPANY_SUFFIXES:
            suffix_lower = suffix.lower()
            idx = lowered.rfind(suffix_lower)
            if idx == -1:
                continue

            # Check trailing text after the suffix
            trailing = lowered[idx + len(suffix_lower):].strip()
            trailing_words = [re.sub(r"[^\w]", "", w) for w in trailing.split() if re.sub(r"[^\w]", "", w)]

            # Reject if trailing words contain sentence continuation words
            if trailing_words:
                if any(w in SENTENCE_CONTINUATION_WORDS for w in trailing_words[:3]):
                    continue
                if len(trailing_words) > 3:
                    continue

            # Extract clean company candidate up to suffix
            candidate = cleaned_no_prefix[: idx + len(suffix)].strip()
            if candidate and len(candidate.split()) >= 2:
                return candidate, 0.85, "suffix_match"

    return "", 0.0, "suffix_match"


def extract_company_name_keyword_only(lines: list[str]) -> tuple[str, float, str]:
    """
    Method (b): Fallback matching the first short line (<=12 words) containing
    an insurer keyword.
    """
    for line in lines:
        cleaned = clean_text(line)
        cleaned = MARKETING_PREFIX_REGEX.sub("", cleaned).strip()
        words = cleaned.split()
        if not (1 <= len(words) <= 12):
            continue

        lowered = cleaned.lower()
        if any(kw in lowered for kw in COMPANY_KEYWORDS):
            if not any(tag in lowered for tag in ("welcome", "thank you for")):
                return cleaned, 0.45, "keyword_only"

    return "", 0.0, "keyword_only"


def extract_company_name_layout_fitz(pdf_path: str | Path, max_pages: int = 2) -> tuple[str, float, str]:
    """
    Method (c): PyMuPDF layout fallback looking for short bold text (<=12 words)
    containing an insurer keyword on the early pages.
    """
    path_obj = Path(pdf_path) if pdf_path else None
    if not path_obj or not path_obj.exists():
        return "", 0.0, "layout_fitz"

    try:
        doc = fitz.open(str(path_obj))
        for page_idx in range(min(max_pages, len(doc))):
            page = doc[page_idx]
            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    line_text = clean_text(" ".join(s.get("text", "") for s in spans))
                    line_text = MARKETING_PREFIX_REGEX.sub("", line_text).strip()
                    words = line_text.split()
                    if not (1 <= len(words) <= 12):
                        continue

                    lowered = line_text.lower()
                    if not any(kw in lowered for kw in COMPANY_KEYWORDS):
                        continue

                    # Check bold span flag or bold font name
                    is_bold = any(
                        bool(s.get("flags", 0) & (1 << 4)) or "bold" in s.get("font", "").lower()
                        for s in spans
                    )

                    if is_bold and not any(tag in lowered for tag in ("welcome", "thank you")):
                        doc.close()
                        return line_text, 0.50, "layout_fitz"

        doc.close()
    except Exception as e:
        logger.debug(f"Layout company name extraction error: {e}")

    return "", 0.0, "layout_fitz"


# ---------------------------------------------------------------------------
# Policy Type, Date, Version Extraction Methods
# ---------------------------------------------------------------------------

def extract_policy_type_method(text: str) -> tuple[str, float, str]:
    """
    Match against configured known policy types.
    """
    lowered = text.lower()
    for policy_type in POLICY_TYPES:
        if policy_type.lower() in lowered:
            return policy_type, 0.70, "known_types_keyword"
    return "", 0.0, "none"


def extract_effective_date_method(text: str) -> tuple[str, float, str]:
    """
    Match effective date near trigger phrases.
    """
    for trigger in EFFECTIVE_DATE_TRIGGERS:
        pattern = rf"{re.escape(trigger)}\s*[:\-]?\s*{DATE_PATTERN}"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(), 0.80, "trigger_regex"
    return "", 0.0, "none"


def extract_document_version_method(text: str) -> tuple[str, float, str]:
    """
    Match document version codes.
    """
    for pattern in VERSION_PATTERNS:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(), 0.80, "version_regex"
    return "", 0.0, "none"


# ---------------------------------------------------------------------------
# Main Unified Extractor
# ---------------------------------------------------------------------------

def get_pages_text(document: dict, max_pages: int = 2) -> list[str]:
    """Get non-empty lines from the first max_pages."""
    pages = document.get("pages", [])[:max_pages]
    lines = []
    for page in pages:
        for line in page.get("text", "").splitlines():
            line_str = line.strip()
            if line_str:
                lines.append(line_str)
    return lines


def extract_metadata(document: dict, category: str) -> dict:
    """
    Extract comprehensive metadata from a PDF document using multi-method
    scoring and confidence ranking.

    Parameters
    ----------
    document : dict
        Output of utils.pdf_reader.read_pdf
    category : str
        Dataset sub-folder name (policy, claim, quote, schedule)

    Returns
    -------
    dict
        Metadata dictionary with confidence scores for Policy Name and Company Name.
    """
    pdf_path = document.get("path")

    # Primary search: first 2 pages by default (reviewer requirement)
    lines_p2 = get_pages_text(document, max_pages=2)
    text_p2 = "\n".join(lines_p2)

    # 1. Policy Name Candidates
    pname_candidates = [
        extract_policy_name_layout_fitz(pdf_path),
        extract_policy_name_explicit_pattern(text_p2),
        extract_policy_name_text_order(lines_p2),
    ]
    valid_pnames = [c for c in pname_candidates if c[0].strip()]
    if valid_pnames:
        valid_pnames.sort(key=lambda c: c[1], reverse=True)
        best_pname, pname_conf, pname_method = valid_pnames[0]
    else:
        best_pname, pname_conf, pname_method = "", 0.0, "none"

    # 2. Insurance Company Name Candidates (pages 1-2)
    company_candidates = [
        extract_company_name_suffix_match(lines_p2),
        extract_company_name_keyword_only(lines_p2),
        extract_company_name_layout_fitz(pdf_path, max_pages=2),
    ]
    valid_companies = [c for c in company_candidates if c[0].strip()]

    # Documented fallback to page 3 if pages 1-2 return nothing (specific real sample document edge case)
    if not valid_companies:
        lines_p3 = get_pages_text(document, max_pages=3)
        text_p3 = "\n".join(lines_p3)
        p3_candidates = [
            extract_company_name_suffix_match(lines_p3),
            extract_company_name_keyword_only(lines_p3),
            extract_company_name_layout_fitz(pdf_path, max_pages=3),
        ]
        valid_companies = [c for c in p3_candidates if c[0].strip()]

    if valid_companies:
        valid_companies.sort(key=lambda c: c[1], reverse=True)
        best_company, company_conf, company_method = valid_companies[0]
    else:
        best_company, company_conf, company_method = "", 0.0, "none"

    # 3. Policy Type, Effective Date, Version
    text_to_search = text_p2 if text_p2 else "\n".join(get_pages_text(document, max_pages=3))
    policy_type, _, _ = extract_policy_type_method(text_to_search)
    effective_date, _, _ = extract_effective_date_method(text_to_search)
    document_version, _, _ = extract_document_version_method(text_to_search)

    metadata = {
        "File Name": document.get("file_name", ""),
        "Category": category,
        "Pages": document.get("page_count", 0),
        "Policy Name": best_pname,
        "Insurance Company Name": best_company,
        "Product Name": best_pname,
        "Policy Type": policy_type,
        "Effective Date": effective_date,
        "Document Version": document_version,
        "Policy Name Confidence": round(pname_conf, 2),
        "Insurance Company Name Confidence": round(company_conf, 2),
    }

    return metadata
