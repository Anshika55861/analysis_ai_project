"""
Task 16 - Create Search Keywords Dataset
=========================================
Dynamically extracts relevant search keywords for every document (policies and claim forms)
to power AI-powered document search and OpenSearch indexing.

Outputs: output/search_keywords.json
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR, DATASET_DIR
from utils.json_utils import save_json, load_json
from utils.pdf_reader import get_all_documents, clean_extracted_text
from utils.logger import get_logger

logger = get_logger("generate_keywords")

CORE_KEYWORD_TAXONOMY = [
    # Lines of Insurance & Coverages
    "Public Liability", "Property Damage", "Commercial Property", "Business Interruption",
    "Management Liability", "Directors and Officers", "Corporate Liability", "Employment Practices Liability",
    "Statutory Liability", "Crime Cover", "Cyber Insurance", "Cyber", "Fire", "Theft", "Flood",
    "Professional Indemnity", "Employers Liability", "Products Liability", "Environmental Liability",
    "Glass Cover", "Money Cover", "Transit Cover", "Machinery Breakdown",
    
    # Policy Attributes & Clauses
    "Limit of Indemnity", "Excess", "Deductible", "Policy Period", "Territorial Limits",
    "Exclusions", "Subrogation", "Indemnity", "Reinstatement", "Claim Notification",
    "Notice of Claim", "Arbitration", "Cancellation", "Premium",
    
    # Industry Sectors & Context
    "Commercial", "Retail", "Manufacturing", "Corporate", "Small Business", "Hospitality",
    "Australia", "United Kingdom", "Worldwide",
    
    # Claim & Legal Terminology
    "Claim Form", "Incident Report", "Loss Adjuster", "Third Party", "Investigation",
    "Accidental Damage", "Bodily Injury", "Property Loss", "Negligence"
]


def extract_keywords_from_text(text: str, max_keywords: int = 20) -> List[str]:
    """Extract matching and contextual keywords from document text."""
    clean_text = clean_extracted_text(text)
    matched_keywords: List[str] = []
    
    # Exact and case-insensitive check against taxonomy
    for term in CORE_KEYWORD_TAXONOMY:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, clean_text, re.IGNORECASE):
            if term not in matched_keywords:
                matched_keywords.append(term)

    # Extract additional capitalized noun phrases / domain terms
    domain_terms = [
        "Allianz", "Policyholder", "Insured Person", "Material Damage", "General Conditions",
        "Claims Procedure", "Settlement of Claims", "Jurisdiction", "Governing Law",
        "Civil Liability", "Defence Costs", "Investigation Costs", "Regulatory Authority"
    ]
    for term in domain_terms:
        if re.search(r"\b" + re.escape(term) + r"\b", clean_text, re.IGNORECASE):
            if term not in matched_keywords:
                matched_keywords.append(term)
                
    return matched_keywords[:max_keywords]


def generate_search_keywords() -> List[Dict]:
    """Generate search keywords dataset for all documents in the dataset directory."""
    logger.info("Starting Task 16: Generating Search Keywords Dataset...")
    
    documents = get_all_documents()
    search_keywords_dataset: List[Dict] = []
    
    for doc in documents:
        file_name = doc["file_name"]
        raw_text = doc["text"]
        
        keywords = extract_keywords_from_text(raw_text)
        
        # Ensure at least standard baseline keywords if sparse
        if "claim" in file_name.lower():
            if "Claim Form" not in keywords:
                keywords.insert(0, "Claim Form")
        else:
            if "Commercial" not in keywords and "Management Liability" not in keywords:
                keywords.append("Commercial Policy")
                
        search_keywords_dataset.append({
            "document": file_name,
            "folder": doc.get("folder", ""),
            "total_keywords": len(keywords),
            "keywords": keywords
        })
        logger.info(f"{file_name} -> {len(keywords)} keywords extracted.")
        
    out_file = OUTPUT_DIR / "search_keywords.json"
    save_json(search_keywords_dataset, out_file)
    logger.info(f"Task 16 Complete: Saved {len(search_keywords_dataset)} document keyword sets to {out_file}")
    return search_keywords_dataset


def main():
    generate_search_keywords()


if __name__ == "__main__":
    main()
