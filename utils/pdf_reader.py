"""
Reusable PDF reader utility with advanced text cleaning and (cid:...) removal.
"""

import re
from pathlib import Path
import pymupdf as fitz
import pdfplumber

from utils.logger import setup_logger

logger = setup_logger()


def clean_extracted_text(text: str) -> str:
    """
    Cleans raw extracted PDF text:
    - Removes all (cid:NNN) corrupted font artifacts and variations
    - Strips unprintable control characters and zero-width spaces
    - Normalizes unicode quotation marks, dashes, and hyphens
    - Replaces non-ascii bullets with standard hyphens
    - Fixes excessive spacing while preserving genuine paragraph breaks
    """
    if not text:
        return ""

    # 1. Remove all (cid:NNN) tokens and stray cid:NNN strings
    text = re.sub(r"\(cid:\s*\d+\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bcid:\s*\d+\b", "", text, flags=re.IGNORECASE)

    # 2. Strip unprintable control characters except newline (\n) and tab (\t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 3. Strip null bytes, replacement characters, and invisible whitespace
    text = text.replace("\x00", "").replace("\u200b", "").replace("\ufeff", "").replace("\ufffd", "")

    # 4. Normalize quotes, dashes, and bullets for consistent encoding
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u2022", "-").replace("\u25a1", "-").replace("\u25aa", "-").replace("\u25cb", "-")

    # 5. Clean line by line
    clean_lines = []
    for raw_line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        # Keep non-empty lines or a single spacing line
        if line:
            clean_lines.append(line)
        elif clean_lines and clean_lines[-1] != "":
            clean_lines.append("")

    return "\n".join(clean_lines).strip()



def read_pdf(pdf_path: str | Path) -> dict:
    """
    Read a PDF file page by page using PyMuPDF (fitz) with pdfplumber fallback,
    ensuring all extracted text is clean, readable, and free from (cid:...) artifacts.

    Parameters
    ----------
    pdf_path : str or Path

    Returns
    -------
    dict
    """
    path_obj = Path(pdf_path)

    result = {
        "file_name": path_obj.name,
        "path": str(path_obj),
        "pages": [],
        "page_count": 0,
        "success": False,
        "error": None
    }

    # Attempt PyMuPDF extraction first (cleanest font handling)
    try:
        doc = fitz.open(path_obj)
        result["page_count"] = len(doc)
        logger.info(f"Reading {path_obj.name} with PyMuPDF ({len(doc)} pages)")

        for page_number, page in enumerate(doc, start=1):
            raw_text = page.get_text("text") or ""
            clean_page_text = clean_extracted_text(raw_text)

            result["pages"].append({
                "page_number": page_number,
                "text": clean_page_text
            })

        result["success"] = True
        return result

    except Exception as fitz_error:
        logger.warning(f"PyMuPDF failed on {path_obj.name}: {fitz_error}. Trying pdfplumber fallback...")

    # Fallback to pdfplumber
    try:
        with pdfplumber.open(path_obj) as pdf:
            result["page_count"] = len(pdf.pages)
            logger.info(f"Reading {path_obj.name} with pdfplumber ({len(pdf.pages)} pages)")

            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    raw_text = page.extract_text() or ""
                except Exception as page_error:
                    logger.warning(f"Could not extract text from page {page_number} of {path_obj.name}: {page_error}")
                    raw_text = ""

                clean_page_text = clean_extracted_text(raw_text)
                result["pages"].append({
                    "page_number": page_number,
                    "text": clean_page_text
                })

        result["success"] = True
        return result

    except Exception as error:
        logger.error(f"Failed to read {path_obj.name}: {error}")
        result["error"] = str(error)
        return result


def get_all_documents() -> list:
    """
    Convenience helper to read all PDF documents from the dataset directory,
    concatenating all pages and ensuring clean text extraction.
    """
    from config.settings import DATASET_DIR

    all_docs = []
    for category_dir in sorted(DATASET_DIR.iterdir()):
        if not category_dir.is_dir():
            continue

        for pdf_path in sorted(category_dir.glob("*.pdf")):
            doc_data = read_pdf(pdf_path)
            full_text = "\n\n".join(p["text"] for p in doc_data.get("pages", []))
            all_docs.append({
                "file_name": pdf_path.name,
                "folder": category_dir.name,
                "path": str(pdf_path),
                "page_count": doc_data.get("page_count", 0),
                "pages": doc_data.get("pages", []),
                "text": full_text
            })

    return all_docs