"""
Task 25 - Generate Final AI Dataset
====================================
Combines all datasets created across Phase 1, Phase 2, and Phase 3 into one
comprehensive, unified, structured dataset ready for AI platform ingestion,
OpenSearch indexing, and Amazon Bedrock RAG retrieval.

Outputs: output/final_ai_dataset.json
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR, DATASET_DIR
from utils.json_utils import save_json, load_json
from utils.logger import get_logger

logger = get_logger("build_final_dataset")


def build_final_ai_dataset() -> List[Dict[str, Any]]:
    """Aggregate all multi-phase outputs into a master AI dataset per document."""
    logger.info("Starting Task 25: Aggregating all multi-phase outputs into final_ai_dataset.json...")
    
    # 1. Load all available sub-datasets safely
    def safe_load(filename: str, default=None):
        p = OUTPUT_DIR / filename
        if p.exists():
            return load_json(p)
        logger.warning(f"File {filename} not found in output directory, using default.")
        return default if default is not None else []

    sections_raw = safe_load("sections.json", {})
    if isinstance(sections_raw, dict):
        sections_by_doc = sections_raw
    elif isinstance(sections_raw, list):
        sections_by_doc = {item.get("document", ""): item.get("sections", []) for item in sections_raw}
    else:
        sections_by_doc = {}

    clauses_raw = safe_load("clauses.json", {})
    if isinstance(clauses_raw, dict):
        all_clauses = clauses_raw.get("clauses", [])
    elif isinstance(clauses_raw, list):
        all_clauses = clauses_raw
    else:
        all_clauses = []

    clauses_by_doc: Dict[str, List[Dict]] = {}
    for c in all_clauses:
        d = c.get("document", "")
        if d:
            clauses_by_doc.setdefault(d, []).append(c)

    qa_data = safe_load("qa_dataset.json", [])
    metadata_data = safe_load("policy_metadata.json", [])
    coverage_data = safe_load("coverage_dataset.json", [])
    summaries_data = safe_load("policy_summaries.json", [])
    keywords_data = safe_load("search_keywords.json", [])
    tags_data = safe_load("document_tags.json", [])
    gaps_data = safe_load("coverage_gaps.json", [])
    recs_data = safe_load("recommendations.json", [])
    risks_data = safe_load("risk_dataset.json", [])
    
    # Group Q&A by document
    qa_by_doc: Dict[str, List[Dict]] = {}
    for qa in qa_data:
        d = qa.get("document", "")
        qa_by_doc.setdefault(d, []).append(qa)

        
    metadata_by_doc = {item.get("document", ""): item for item in metadata_data}
    coverage_by_doc = {item.get("document", ""): item.get("coverages", []) for item in coverage_data}
    summaries_by_doc = {item.get("document", ""): item.get("summary", {}) for item in summaries_data}
    keywords_by_doc = {item.get("document", ""): item.get("keywords", []) for item in keywords_data}
    tags_by_doc = {item.get("document", ""): item.get("tags", []) for item in tags_data}
    gaps_by_doc = {item.get("document", ""): item.get("missing_coverages", []) for item in gaps_data}
    recs_by_doc = {item.get("document", ""): item.get("recommendations", []) for item in recs_data}

    # All known documents in the system
    all_docs = sorted(list(set(
        list(sections_by_doc.keys()) +
        list(metadata_by_doc.keys()) +
        list(keywords_by_doc.keys()) +
        list(tags_by_doc.keys())
    )))
    
    final_dataset: List[Dict[str, Any]] = []
    
    for doc_name in all_docs:
        if not doc_name:
            continue
            
        doc_meta = metadata_by_doc.get(doc_name, {})
        doc_sections = sections_by_doc.get(doc_name, [])
        doc_clauses = clauses_by_doc.get(doc_name, [])
        doc_coverages = coverage_by_doc.get(doc_name, [])
        doc_summary = summaries_by_doc.get(doc_name, {})
        doc_keywords = keywords_by_doc.get(doc_name, [])
        doc_tags = tags_by_doc.get(doc_name, [])
        doc_gaps = gaps_by_doc.get(doc_name, [])
        doc_recs = recs_by_doc.get(doc_name, [])
        doc_qa = qa_by_doc.get(doc_name, [])
        
        # Relevant risks associated with this document type
        relevant_risks = []
        doc_tags_set = set(t.lower() for t in doc_tags)
        for r in risks_data:
            covs = [c.lower() for c in r.get("related_coverages", [])]
            if any(c in doc_tags_set for c in covs) or ("commercial" in doc_tags_set and r["risk"] in ["Fire", "Theft", "Public Liability"]):
                relevant_risks.append(r["risk"])

        entry = {
            "document": doc_name,
            "document_type": "Claim Form" if "claim" in doc_name.lower() else "Policy Wording",
            "metadata": doc_meta,
            "tags": doc_tags,
            "keywords": doc_keywords,
            "summary": doc_summary,
            "coverages": doc_coverages,
            "coverage_gaps": doc_gaps,
            "recommendations": doc_recs,
            "associated_risks": relevant_risks,
            "total_sections": len(doc_sections),
            "total_clauses": len(doc_clauses),
            "total_qa_pairs": len(doc_qa),
            "questions": doc_qa[:10],  # Sample representative QA pairs
            "sample_clauses": doc_clauses[:10]  # Sample representative clauses
        }
        final_dataset.append(entry)
        logger.info(f"Aggregated complete profile for: {doc_name}")

    out_file = OUTPUT_DIR / "final_ai_dataset.json"
    save_json(final_dataset, out_file)
    logger.info(f"Task 25 Complete: Saved {len(final_dataset)} unified AI document profiles to {out_file}")
    return final_dataset


def main():
    build_final_ai_dataset()


if __name__ == "__main__":
    main()
