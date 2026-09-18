"""
Task 11 - Split Documents into Smaller Parts (Document Chunking)

Splits insurance policy documents into semantic chunks optimized for:
- Vector search (OpenSearch)
- LLM embedding & retrieval (Amazon Bedrock / RAG)
- Automated Q&A systems

Chunking strategy:
- Heading-aware & section-aware
- Page-boundary aware
- Chunk size: ~500 to 1000 characters with natural sentence boundary preservation
- Contextual overlap (~100 chars)
- Strict text sanitization removing (cid:...) font artifacts

Outputs:
- output/document_chunks.json
"""

import os
import sys
import json
import re
from pathlib import Path
import pymupdf as fitz

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR, POLICY_DIR, CLAIM_DIR, DATASET_DIR
from utils.logger import setup_logger
from utils.json_utils import save_json
from utils.pdf_reader import clean_extracted_text

logger = setup_logger()

MIN_CHUNK_SIZE = 400
TARGET_CHUNK_SIZE = 800
MAX_CHUNK_SIZE = 1200
OVERLAP_SIZE = 100


def split_text_into_chunks(text: str, target_size: int = TARGET_CHUNK_SIZE, overlap: int = OVERLAP_SIZE) -> list[str]:
    """
    Splits text into chunks respecting paragraph and sentence boundaries.
    """
    text = clean_extracted_text(text)
    if not text:
        return []

    if len(text) <= MAX_CHUNK_SIZE:
        return [text]

    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) <= target_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                tail = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                current_chunk = f"{tail} {para}".strip()
            else:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sent_chunk = ""
                for sent in sentences:
                    if len(sent_chunk) + len(sent) <= target_size:
                        sent_chunk = f"{sent_chunk} {sent}".strip()
                    else:
                        if sent_chunk:
                            chunks.append(sent_chunk)
                        sent_chunk = sent.strip()
                if sent_chunk:
                    current_chunk = sent_chunk

    if current_chunk and (not chunks or current_chunk != chunks[-1]):
        chunks.append(current_chunk)

    return chunks


def chunk_document(pdf_path: Path, start_chunk_id: int = 1) -> tuple[list[dict], int]:
    """
    Chunks a single PDF document page by page, tracking heading context.
    """
    filename = pdf_path.name
    doc = fitz.open(pdf_path)
    chunks = []
    chunk_id = start_chunk_id
    current_heading = "General"

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        page_text = clean_extracted_text(page.get_text("text") or "")

        lines = page_text.splitlines()
        page_content_lines = []

        for line in lines:
            trimmed = line.strip()
            if len(trimmed) > 3 and len(trimmed) < 60:
                if trimmed.isupper() or any(trimmed.startswith(k) for k in ["Section", "Part", "Definitions", "Exclusions", "Conditions", "Cover", "Introduction", "Benefits"]):
                    current_heading = trimmed
            page_content_lines.append(line)

        clean_page_text = "\n".join(page_content_lines).strip()
        if not clean_page_text or len(clean_page_text) < 30:
            continue

        raw_chunks = split_text_into_chunks(clean_page_text)

        for chunk_txt in raw_chunks:
            chunk_txt_clean = clean_extracted_text(chunk_txt)
            if "(cid:" in chunk_txt_clean or len(chunk_txt_clean.split()) < 5:
                continue

            chunks.append({
                "chunk_id": chunk_id,
                "document": filename,
                "page": page_num,
                "heading": clean_extracted_text(current_heading),
                "char_count": len(chunk_txt_clean),
                "word_count": len(chunk_txt_clean.split()),
                "text": chunk_txt_clean
            })
            chunk_id += 1

    return chunks, chunk_id


def main():
    logger.info("Starting Task 11: Split Documents into Smaller Parts (Document Chunking)...")

    pdf_files = sorted(list(DATASET_DIR.glob("**/*.pdf")))
    all_chunks = []
    current_id = 1

    for pdf_path in pdf_files:
        logger.info(f"Chunking document {pdf_path.name}...")
        doc_chunks, current_id = chunk_document(pdf_path, current_id)
        all_chunks.extend(doc_chunks)
        logger.info(f"  -> Generated {len(doc_chunks)} chunks for {pdf_path.name}")

    out_file = OUTPUT_DIR / "document_chunks.json"
    save_json(all_chunks, out_file)
    logger.info(f"Task 11 Complete: Saved total {len(all_chunks)} chunks to {out_file}")

    print(f"\n--- Total Generated Document Chunks: {len(all_chunks)} ---")


if __name__ == "__main__":
    main()
