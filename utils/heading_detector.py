"""
Heading Detector Utility

Uses PyMuPDF (fitz) to detect document headings based on visual layout
and structural signals:
1. Numbered headings (e.g. 1, 1.1, 2.3)
2. ALL CAPS text (> 1 word)
3. Bold text styling (PyMuPDF span flags / font name)
4. Font size compared to document body text baseline
5. Extra vertical spacing before heading vs page median gap

Includes a hard gate requiring a minimum font size increase over body
baseline before stylistic signals contribute, preventing false positive
detection of inline numbered clauses.
"""

import re
import statistics
from collections import Counter
from pathlib import Path
import pymupdf as fitz

from utils.logger import setup_logger

logger = setup_logger()

# Regex for numbered headings like "1", "1.1", "2.3.1"
NUMBERED_HEADING_REGEX = re.compile(r"^\d+(?:\.\d+)*\b")

# Mid-sentence ending connectors that indicate a wrapped paragraph line rather than a heading
MID_SENTENCE_ENDINGS = {
    "and", "or", "the", "a", "an", "of", "in", "to", "for", "with", "as", "by",
    "that", "which", "who", "whom", "whose", "from", "on", "at", "about"
}

# Stoplist phrases commonly found in large-font marketing taglines / preambles
TAGLINE_STOPWORDS = (
    "thank you for choosing",
    "welcome to",
    "dares to tell",
    "we are one of the",
    "allianz group, one of",
)


def compute_body_font_size(doc: fitz.Document) -> float:
    """
    Compute the document's body text font size as the size that covers
    the most characters (not lines) across the entire document.
    """
    size_char_counts = Counter()

    for page in doc:
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:  # Text block
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if text:
                        size = round(span.get("size", 10.0), 1)
                        size_char_counts[size] += len(text)

    if not size_char_counts:
        return 10.0

    body_size, _ = size_char_counts.most_common(1)[0]
    return float(body_size)


def is_bold_span(span: dict) -> bool:
    """
    Check if a PyMuPDF span is bold via flags or font family name.
    PyMuPDF bold flag is bit 4 (1 << 4 = 16 or 2**4).
    """
    flags = span.get("flags", 0)
    if bool(flags & (1 << 4)):
        return True

    font_name = span.get("font", "").lower()
    if any(b in font_name for b in ("bold", "black", "heavy", "semibold", "demi")):
        return True

    return False


def detect_layout_headings(pdf_path: str | Path) -> dict[int, list[str]]:
    """
    Detect structural headings from a PDF file using PyMuPDF.

    Parameters
    ----------
    pdf_path : str or Path
        Path to the PDF file.

    Returns
    -------
    dict[int, list[str]]
        Mapping of 1-indexed page numbers to a list of detected candidate
        heading strings on that page.
    """
    path_obj = Path(pdf_path)
    if not path_obj.exists():
        logger.warning(f"Heading detection skipped - file not found: {pdf_path}")
        return {}

    headings_by_page: dict[int, list[str]] = {}

    try:
        doc = fitz.open(str(path_obj))
        body_size = compute_body_font_size(doc)
        logger.debug(f"{path_obj.name}: Document body font size baseline is {body_size}pt")

        for page_idx, page in enumerate(doc):
            page_number = page_idx + 1
            headings_by_page[page_number] = []

            page_dict = page.get_text("dict")
            blocks = page_dict.get("blocks", [])

            # Collect lines with their visual attributes and bounding boxes
            page_lines = []
            for block in blocks:
                if block.get("type") != 0:
                    continue

                block_lines = block.get("lines", [])
                is_multi_line_paragraph = len(block_lines) >= 3

                for line in block_lines:
                    spans = line.get("spans", [])
                    if not spans:
                        continue

                    line_text = " ".join(s.get("text", "") for s in spans).strip()
                    line_text = re.sub(r"\s+", " ", line_text)
                    if not line_text:
                        continue

                    # If the entire block has 3+ lines of the same font style, it's a paragraph block
                    if is_multi_line_paragraph:
                        span_sizes = [s.get("size", 0) for s in spans]
                        avg_line_size = sum(span_sizes) / len(span_sizes) if span_sizes else 0
                        if avg_line_size < body_size * 1.8:
                            continue

                    max_size = max(s.get("size", 0.0) for s in spans)
                    has_bold = any(is_bold_span(s) for s in spans)
                    bbox = line.get("bbox", (0, 0, 0, 0))

                    page_lines.append({
                        "text": line_text,
                        "max_size": max_size,
                        "has_bold": has_bold,
                        "bbox": bbox,
                        "top_y": bbox[1],
                        "bottom_y": bbox[3],
                    })

            if not page_lines:
                continue

            # Sort lines top-to-bottom
            page_lines.sort(key=lambda item: (item["top_y"], item["bbox"][0]))

            # Compute vertical gaps between consecutive lines to establish median line spacing
            gaps = []
            for i in range(1, len(page_lines)):
                gap = page_lines[i]["top_y"] - page_lines[i - 1]["bottom_y"]
                if gap > 0:
                    gaps.append(gap)

            median_gap = statistics.median(gaps) if gaps else max(2.0, body_size * 0.2)

            # Score each line for heading probability
            for i, line_info in enumerate(page_lines):
                text = line_info["text"]
                words = text.split()

                # Headings must be reasonably short (<= 10 words, >= 1 word, len >= 2)
                if not (1 <= len(words) <= 10) or len(text) < 2:
                    continue

                # Headings must not start with lowercase letters
                if text[0].islower():
                    continue

                # Headings must not end with mid-sentence connector words
                last_word_clean = re.sub(r"[^\w]", "", words[-1].lower())
                if last_word_clean in MID_SENTENCE_ENDINGS:
                    continue

                # Headings must not be marketing taglines / callout fragments
                lowered_text = text.lower()
                if any(tag in lowered_text for tag in TAGLINE_STOPWORDS):
                    continue

                # Hard gate: Require some minimum size increase over body text baseline
                font_ratio = line_info["max_size"] / max(body_size, 1.0)
                if font_ratio < 1.05:
                    continue  # Gate failed: do not score, prevents body clause misdetection

                # 1. Font Size Signal
                if font_ratio >= 1.5:
                    size_score = 4.0  # Large font jump clears threshold (>=3.5) alone
                elif font_ratio >= 1.3:
                    size_score = 2.5
                else:
                    size_score = 1.0  # Modest jump (1.05-1.3x): needs bold + spacing/caps to qualify

                score = size_score

                # 2. Numbered Headings Signal (e.g. 1, 1.1, 2.3)
                is_numbered = bool(NUMBERED_HEADING_REGEX.match(text))
                if is_numbered:
                    score += 0.5

                # 3. ALL CAPS Text Signal (> 1 word to avoid single-letter acronym noise)
                is_all_caps = text.isupper() and len(words) > 1 and any(c.isalpha() for c in text)
                if is_all_caps:
                    score += 1.0

                # 4. Bold Text Signal
                if line_info["has_bold"]:
                    score += 1.0

                # 5. Extra Spacing Before Heading Signal (>= 1.8x median gap)
                if i > 0:
                    prev_gap = line_info["top_y"] - page_lines[i - 1]["bottom_y"]
                    if prev_gap >= 1.8 * median_gap and prev_gap > 3.0:
                        score += 0.5

                # Threshold to qualify as structural heading candidate
                if score >= 3.5:
                    headings_by_page[page_number].append(text)

        doc.close()
        return headings_by_page

    except Exception as e:
        logger.error(f"Error detecting layout headings for {pdf_path}: {e}")
        return {}
