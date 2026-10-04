#!/usr/bin/env python3
"""
scripts/statistics.py - Task 33: Generate Dataset Statistics
Calculates holistic project-wide metrics by inspecting all generated datasets:
  - Total documents, policies, and claim forms
  - Total coverages, clauses, and semantic chunks
  - Total questions (Q&A, evaluation, search test queries)
  - Total risks, recommendations, and rules
  - Total pages and average pages per document
Saves comprehensive metrics to output/dataset_statistics.json.
"""

import sys
import importlib.util
from pathlib import Path

# Provide standard library statistics passthrough to prevent shadowing in third-party libraries (e.g. PyMuPDF)
try:
    for _p in sys.path:
        _stat_file = Path(_p) / "statistics.py"
        if _stat_file.exists() and "scripts" not in str(_stat_file) and _stat_file != Path(__file__).resolve():
            _spec = importlib.util.spec_from_file_location("_stdlib_statistics", _stat_file)
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            for _attr in dir(_mod):
                if not _attr.startswith("__"):
                    globals()[_attr] = getattr(_mod, _attr)
            break
except Exception:
    pass

import pandas as pd
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json, load_json
from config.settings import OUTPUT_DIR

logger = setup_logger("statistics")


def generate_dataset_statistics() -> Dict[str, Any]:
    """Inspects all datasets and compiles comprehensive summary statistics."""
    
    # 1. Document & Page Counts (from dataset.csv)
    dataset_csv = OUTPUT_DIR / "dataset.csv"
    total_docs = 0
    total_pages = 0
    avg_pages = 0.0
    if dataset_csv.exists():
        df = pd.read_csv(dataset_csv)
        total_docs = len(df)
        page_col = None
        for col in ["Pages", "page_count", "pages"]:
            if col in df.columns:
                page_col = col
                break
        if page_col:
            total_pages = int(df[page_col].sum())
            avg_pages = round(float(df[page_col].mean()), 2)

    # 2. Policies
    meta_file = OUTPUT_DIR / "policy_metadata.json"
    meta_data = load_json(meta_file) if meta_file.exists() else []
    total_policies = len(meta_data)
    total_claim_forms = max(0, total_docs - total_policies)

    # 3. Coverages
    cov_file = OUTPUT_DIR / "coverage_dataset.json"
    cov_data = load_json(cov_file) if cov_file.exists() else []
    total_cov_entries = sum(len(item.get("coverages", [])) for item in cov_data)
    distinct_coverages = set()
    for item in cov_data:
        for c in item.get("coverages", []):
            name = c.get("name") or c.get("coverage_name")
            if name:
                distinct_coverages.add(name)

    lookup_file = OUTPUT_DIR / "coverage_lookup.json"
    lookup_data = load_json(lookup_file) if lookup_file.exists() else {}
    coverage_synonyms_count = len(lookup_data)

    # 4. Clauses
    clauses_file = OUTPUT_DIR / "clauses.json"
    clauses_raw = load_json(clauses_file) if clauses_file.exists() else {}
    raw_clauses_count = len(clauses_raw.get("clauses", [])) if isinstance(clauses_raw, dict) else len(clauses_raw)
    
    classified_file = OUTPUT_DIR / "classified_clauses.json"
    classified_data = load_json(classified_file) if classified_file.exists() else []
    classified_clauses_count = len(classified_data)

    # 5. Questions & Evaluation
    qa_file = OUTPUT_DIR / "qa_dataset.json"
    qa_data = load_json(qa_file) if qa_file.exists() else []
    qa_count = len(qa_data)

    eval_file = OUTPUT_DIR / "evaluation_dataset.json"
    eval_data = load_json(eval_file) if eval_file.exists() else []
    eval_count = len(eval_data)

    ai_eval_file = OUTPUT_DIR / "ai_evaluation.json"
    ai_eval_data = load_json(ai_eval_file) if ai_eval_file.exists() else []
    ai_eval_count = len(ai_eval_data)

    search_file = OUTPUT_DIR / "search_test_dataset.json"
    search_data = load_json(search_file) if search_file.exists() else []
    search_queries_count = len(search_data)

    total_questions = qa_count + eval_count + ai_eval_count + search_queries_count

    # 6. Risks
    risk_file = OUTPUT_DIR / "risk_dataset.json"
    risk_raw = load_json(risk_file) if risk_file.exists() else {}
    risks_list = risk_raw.get("master_risks", []) if isinstance(risk_raw, dict) else risk_raw
    total_risks = len(risks_list)

    # 7. Recommendations & Rules
    recs_file = OUTPUT_DIR / "recommendations.json"
    recs_data = load_json(recs_file) if recs_file.exists() else []
    total_doc_recs = sum(len(item.get("recommendations", [])) for item in recs_data)

    rules_file = OUTPUT_DIR / "rules_dataset.json"
    rules_data = load_json(rules_file) if rules_file.exists() else []
    total_rules = len(rules_data)

    total_recommendations = total_doc_recs + total_rules

    # 8. Chunks, Entities, Terms
    chunks_file = OUTPUT_DIR / "document_chunks.json"
    chunks_data = load_json(chunks_file) if chunks_file.exists() else []
    total_chunks = len(chunks_data)

    entities_file = OUTPUT_DIR / "entities.json"
    entities_data = load_json(entities_file) if entities_file.exists() else []
    total_entities = len(entities_data)

    dict_file = OUTPUT_DIR / "insurance_dictionary.json"
    dict_data = load_json(dict_file) if dict_file.exists() else []
    total_dictionary_terms = len(dict_data)

    stats = {
        "project_name": "Document Analysis AI",
        "phase": "Phase 4 - Final Delivery",
        "total_documents": total_docs,
        "total_policies": total_policies,
        "total_claim_forms": total_claim_forms,
        "total_pages": total_pages,
        "average_pages_per_document": avg_pages,
        "total_coverages": len(distinct_coverages),
        "total_coverage_evaluations": total_cov_entries,
        "coverage_synonyms_mapped": coverage_synonyms_count,
        "total_clauses_extracted": raw_clauses_count,
        "total_clauses_classified": classified_clauses_count,
        "total_questions": total_questions,
        "verified_qa_pairs": qa_count,
        "ai_evaluation_questions": eval_count + ai_eval_count,
        "search_test_queries": search_queries_count,
        "total_risks": total_risks,
        "total_recommendations": total_recommendations,
        "document_recommendations": total_doc_recs,
        "business_rules": total_rules,
        "total_semantic_chunks": total_chunks,
        "total_named_entities": total_entities,
        "total_insurance_dictionary_terms": total_dictionary_terms
    }

    return stats


def main():
    logger.info("Starting Task 33: Generate Dataset Statistics...")
    stats = generate_dataset_statistics()

    logger.info("Dataset Statistics Summary:")
    logger.info(f"  - Total documents: {stats['total_documents']}")
    logger.info(f"  - Total policies: {stats['total_policies']}")
    logger.info(f"  - Total pages: {stats['total_pages']} (Avg: {stats['average_pages_per_document']} pages/doc)")
    logger.info(f"  - Total coverages: {stats['total_coverages']} distinct ({stats['coverage_synonyms_mapped']} synonyms)")
    logger.info(f"  - Total clauses: {stats['total_clauses_extracted']} extracted ({stats['total_clauses_classified']} classified)")
    logger.info(f"  - Total questions: {stats['total_questions']} (QA: {stats['verified_qa_pairs']}, Search Queries: {stats['search_test_queries']})")
    logger.info(f"  - Total risks: {stats['total_risks']} perils")
    logger.info(f"  - Total recommendations & rules: {stats['total_recommendations']}")
    logger.info(f"  - Semantic chunks: {stats['total_semantic_chunks']}")
    logger.info(f"  - Named entities: {stats['total_named_entities']}")

    out_path = OUTPUT_DIR / "dataset_statistics.json"
    save_json(stats, out_path)
    logger.info(f"Task 33 Complete: Saved statistics to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
