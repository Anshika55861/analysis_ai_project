#!/usr/bin/env python3
"""
scripts/find_duplicates.py - Task 27: Find Duplicate Insurance Information
Identifies shared and duplicate data across insurance documents:
  - Identical and high-similarity clauses shared between documents (from Task 4 similar clauses)
  - Duplicate policy numbers (integrity check)
  - Common coverages shared across multiple policies
  - Shared broker recommendations across policies
Saves findings to output/duplicate_report.json.
"""

import sys
import re
from pathlib import Path
from collections import defaultdict
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import load_json, save_json
from config.settings import OUTPUT_DIR

logger = setup_logger("find_duplicates")


def normalize_text(text: str) -> str:
    """Normalizes text for comparison."""
    if not text:
        return ""
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def find_duplicate_clauses(clauses_raw: Any) -> List[Dict[str, Any]]:
    """Identifies identical and high-similarity clauses across documents."""
    duplicates = []
    seen = set()

    if isinstance(clauses_raw, dict):
        similar = clauses_raw.get("similar_clauses", [])
        for item in similar:
            doc_a = item.get("Document A") or item.get("document_a") or ""
            doc_b = item.get("Document B") or item.get("document_b") or ""
            title = item.get("Clause Title") or item.get("Clause Title A") or ""
            sim = float(item.get("Content Similarity", 0.0) or item.get("Similarity", 0.0))
            title_sim = float(item.get("Title Similarity", 0.0))
            
            if (sim >= 0.85 or title_sim >= 95.0) and title:
                key = (title.lower(), min(doc_a, doc_b), max(doc_a, doc_b))
                if key not in seen:
                    seen.add(key)
                    duplicates.append({
                        "duplicate_type": "Clause",
                        "value": title.strip().capitalize(),
                        "documents": sorted(list(set([doc_a, doc_b]))),
                        "occurrences": 2
                    })

    return duplicates


def find_duplicate_policy_numbers(metadata: list) -> List[Dict[str, Any]]:
    """Checks for duplicate policy numbers across documents."""
    pnum_to_docs = defaultdict(set)
    for item in metadata:
        pnum = item.get("policy_number", "").strip()
        doc = item.get("document", "")
        if pnum and pnum.lower() not in ["null", "none", "unknown"]:
            pnum_to_docs[pnum].add(doc)
            
    duplicates = []
    for pnum, docs in pnum_to_docs.items():
        if len(docs) > 1:
            duplicates.append({
                "duplicate_type": "Policy Number",
                "value": pnum,
                "documents": sorted(list(docs)),
                "occurrences": len(docs)
            })
    return duplicates


def find_duplicate_coverages(coverage_data: list) -> List[Dict[str, Any]]:
    """Identifies standard coverages shared across multiple policies."""
    cov_to_docs = defaultdict(set)
    for item in coverage_data:
        doc = item.get("document", "")
        coverages = item.get("coverages", [])
        for c in coverages:
            name = c.get("coverage_name") or c.get("name") or ""
            included = c.get("included", False)
            if name and included:
                cov_to_docs[name].add(doc)
                
    duplicates = []
    for cov, docs in sorted(cov_to_docs.items()):
        if len(docs) > 1:
            duplicates.append({
                "duplicate_type": "Coverage",
                "value": cov,
                "documents": sorted(list(docs)),
                "occurrences": len(docs)
            })
    return duplicates


def find_duplicate_recommendations(recs_data: list) -> List[Dict[str, Any]]:
    """Identifies identical broker recommendations suggested for multiple policies."""
    rec_to_docs = defaultdict(set)
    rec_to_sample = {}
    for item in recs_data:
        doc = item.get("document", "")
        recommendations = item.get("recommendations", [])
        for r in recommendations:
            rec_text = r if isinstance(r, str) else r.get("recommendation", "")
            norm = normalize_text(rec_text)
            if norm:
                rec_to_docs[norm].add(doc)
                if norm not in rec_to_sample:
                    rec_to_sample[norm] = rec_text.strip()
                
    duplicates = []
    for norm, docs in sorted(rec_to_docs.items()):
        if len(docs) > 1:
            duplicates.append({
                "duplicate_type": "Recommendation",
                "value": rec_to_sample[norm],
                "documents": sorted(list(docs)),
                "occurrences": len(docs)
            })
    return duplicates


def main():
    logger.info("Starting Task 27: Find Duplicate Insurance Information...")
    output_dir = OUTPUT_DIR

    # Load source datasets
    clauses_file = output_dir / "clauses.json"
    metadata_file = output_dir / "policy_metadata.json"
    coverage_file = output_dir / "coverage_dataset.json"
    recs_file = output_dir / "recommendations.json"

    clauses_raw = load_json(clauses_file) if clauses_file.exists() else {}
    metadata = load_json(metadata_file) if metadata_file.exists() else []
    coverages = load_json(coverage_file) if coverage_file.exists() else []
    recs = load_json(recs_file) if recs_file.exists() else []

    all_duplicates: List[Dict[str, Any]] = []

    # 1. Duplicate Clauses
    dup_clauses = find_duplicate_clauses(clauses_raw)
    logger.info(f"Found {len(dup_clauses)} identical/shared clauses across documents.")
    all_duplicates.extend(dup_clauses)

    # 2. Duplicate Policy Numbers
    dup_pnums = find_duplicate_policy_numbers(metadata)
    logger.info(f"Found {len(dup_pnums)} shared policy numbers across documents.")
    all_duplicates.extend(dup_pnums)

    # 3. Duplicate / Shared Coverages
    dup_coverages = find_duplicate_coverages(coverages)
    logger.info(f"Found {len(dup_coverages)} shared coverage types across policies.")
    all_duplicates.extend(dup_coverages)

    # 4. Shared Recommendations
    dup_recs = find_duplicate_recommendations(recs)
    logger.info(f"Found {len(dup_recs)} shared recommendations across policies.")
    all_duplicates.extend(dup_recs)

    # Save output
    out_path = output_dir / "duplicate_report.json"
    save_json(all_duplicates, out_path)
    logger.info(f"Task 27 Complete: Identified {len(all_duplicates)} total duplicate/shared items.")
    logger.info(f"Report saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
