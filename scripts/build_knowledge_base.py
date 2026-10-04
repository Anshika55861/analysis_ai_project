#!/usr/bin/env python3
"""
scripts/build_knowledge_base.py - Task 31: Create Insurance Knowledge Base
Combines core domain knowledge into one centralized, reusable knowledge base:
  - Insurance terms (definitions and canonical mappings)
  - Common clauses (categorized representative policy clauses)
  - Risks (peril taxonomy and mitigation strategies)
  - Coverages (standardized coverage catalogue)
  - Recommendations (underwriting and broker advisory rules)
Saves to output/insurance_knowledge_base.json.
"""

import sys
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json, load_json
from config.settings import OUTPUT_DIR

logger = setup_logger("build_knowledge_base")


def build_knowledge_base() -> Dict[str, Any]:
    """Assembles all domain knowledge components into a unified master dictionary."""
    
    # 1. Insurance Terms
    dict_file = OUTPUT_DIR / "insurance_dictionary.json"
    terms_raw = load_json(dict_file) if dict_file.exists() else []
    term_mapping_file = OUTPUT_DIR / "term_mapping.json"
    mapping_raw = load_json(term_mapping_file) if term_mapping_file.exists() else []
    
    terms_section = {
        "total_terms": len(terms_raw),
        "dictionary": terms_raw,
        "canonical_mappings": mapping_raw
    }

    # 2. Common Clauses
    clauses_file = OUTPUT_DIR / "classified_clauses.json"
    classified_clauses = load_json(clauses_file) if clauses_file.exists() else []
    
    # Pick representative clauses per category
    clauses_by_cat = {}
    for i, c in enumerate(classified_clauses):
        cat = c.get("category", "General")
        clauses_by_cat.setdefault(cat, [])
        if len(clauses_by_cat[cat]) < 10:  # Top 10 representative clauses per category
            cid = c.get("clause_id") or c.get("clause_number") or f"{c.get('document', 'doc')}_clause_{i+1}"
            ctext = c.get("clause") or c.get("clause_text") or ""
            ctitle = c.get("clause_title") or f"{cat} Clause"
            cdoc = c.get("document") or "unknown"
            
            clauses_by_cat[cat].append({
                "clause_id": cid,
                "clause_title": ctitle,
                "clause_text": ctext,
                "document": cdoc
            })

    clauses_section = {
        "categories_covered": list(clauses_by_cat.keys()),
        "representative_clauses": clauses_by_cat
    }

    # 3. Risks & Perils
    risks_file = OUTPUT_DIR / "risk_dataset.json"
    risks_raw = load_json(risks_file) if risks_file.exists() else {}
    if isinstance(risks_raw, dict):
        risks_list = risks_raw.get("master_risks", risks_raw.get("risks", []))
    else:
        risks_list = risks_raw

    risks_section = {
        "total_risks": len(risks_list),
        "peril_catalog": risks_list
    }

    # 4. Coverages
    lookup_file = OUTPUT_DIR / "coverage_lookup.json"
    lookup_raw = load_json(lookup_file) if lookup_file.exists() else {}
    if isinstance(lookup_raw, dict):
        coverage_mappings = lookup_raw
    else:
        coverage_mappings = {item.get("synonym", str(i)): item.get("canonical", "") for i, item in enumerate(lookup_raw)}

    coverages_section = {
        "total_mappings": len(coverage_mappings),
        "coverage_lookup": coverage_mappings
    }

    # 5. Recommendations & Business Rules
    recs_file = OUTPUT_DIR / "recommendations.json"
    recs_raw = load_json(recs_file) if recs_file.exists() else []
    
    rules_file = OUTPUT_DIR / "rules_dataset.json"
    rules_raw = load_json(rules_file) if rules_file.exists() else []

    recommendations_section = {
        "policy_recommendations": recs_raw,
        "underwriting_rules": rules_raw
    }

    # Master Knowledge Base
    kb = {
        "title": "Enterprise Insurance Knowledge Base",
        "description": "Unified insurance domain ontology, common contractual clauses, risk taxonomy, coverage mappings, and advisory rules.",
        "version": "1.0.0",
        "insurance_terms": terms_section,
        "common_clauses": clauses_section,
        "risks": risks_section,
        "coverages": coverages_section,
        "recommendations": recommendations_section
    }

    return kb


def main():
    logger.info("Starting Task 31: Create Insurance Knowledge Base...")
    kb = build_knowledge_base()

    logger.info(f"Knowledge Base built successfully:")
    logger.info(f"  - Insurance terms: {kb['insurance_terms']['total_terms']} terms")
    logger.info(f"  - Clause categories: {len(kb['common_clauses']['categories_covered'])} categories")
    logger.info(f"  - Risks: {kb['risks']['total_risks']} perils")
    logger.info(f"  - Coverage mappings: {kb['coverages']['total_mappings']} entries")
    logger.info(f"  - Underwriting rules: {len(kb['recommendations']['underwriting_rules'])} rules")

    out_path = OUTPUT_DIR / "insurance_knowledge_base.json"
    save_json(kb, out_path)
    logger.info(f"Task 31 Complete: Saved knowledge base to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
