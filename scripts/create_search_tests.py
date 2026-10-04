#!/usr/bin/env python3
"""
scripts/create_search_tests.py - Task 28: Create Search Test Dataset
Generates 35+ realistic user search queries for testing OpenSearch and Bedrock search engines.
Maps each query to its ground-truth expected matching document(s).
Saves to output/search_test_dataset.json.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json
from config.settings import OUTPUT_DIR

logger = setup_logger("create_search_tests")


def generate_search_test_dataset() -> List[Dict[str, Any]]:
    """Builds a benchmark test dataset of realistic search queries and expected matches."""
    
    test_queries = [
        # Coverage Queries
        {
            "query": "Public Liability policy",
            "category": "Coverage",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Cyber Insurance",
            "category": "Coverage",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Directors and Officers liability coverage",
            "category": "Coverage",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Marine cargo transit insurance",
            "category": "Coverage",
            "expected_documents": ["policy4.pdf"]
        },
        {
            "query": "Personal Accident and health insurance",
            "category": "Coverage",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Employers Liability statutory certificate",
            "category": "Coverage",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Business Interruption loss of revenue",
            "category": "Coverage",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Corporate Legal Liability cover",
            "category": "Coverage",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Employment Practices Liability claims",
            "category": "Coverage",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Goods in transit inland transport coverage",
            "category": "Coverage",
            "expected_documents": ["policy4.pdf"]
        },

        # Peril & Risk Queries
        {
            "query": "Policies with Flood Cover",
            "category": "Peril",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Fire and lightning property damage",
            "category": "Peril",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Theft and burglary coverage",
            "category": "Peril",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Accidental bodily injury hospital cover",
            "category": "Peril",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Management misconduct and regulatory defense costs",
            "category": "Peril",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Cargo jettison and general average contribution",
            "category": "Peril",
            "expected_documents": ["policy4.pdf"]
        },

        # Financial Limits & Deductibles
        {
            "query": "Property Damage limit",
            "category": "Limit & Excess",
            "expected_documents": ["policy2.pdf"]
        },
        {
            "query": "Medical expenses aggregate limit",
            "category": "Limit & Excess",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Policy aggregate limit of indemnity 5 million",
            "category": "Limit & Excess",
            "expected_documents": ["policy3.pdf"]
        },
        {
            "query": "Excess deductible payable on commercial claims",
            "category": "Limit & Excess",
            "expected_documents": ["policy2.pdf", "policy3.pdf"]
        },

        # Expiry & Temporal
        {
            "query": "Policies expiring in 2027",
            "category": "Dates",
            "expected_documents": ["policy2.pdf", "policy3.pdf"]
        },
        {
            "query": "Policies expiring in 2026",
            "category": "Dates",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Retroactive date inception requirement",
            "category": "Dates",
            "expected_documents": ["policy3.pdf"]
        },

        # Insurer & Jurisdiction
        {
            "query": "Allianz Ayudhya Thailand policies",
            "category": "Entity",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Allianz Insurance plc commercial wordings",
            "category": "Entity",
            "expected_documents": ["policy2.pdf", "policy3.pdf", "policy4.pdf"]
        },
        {
            "query": "Policies governed by English law and UK jurisdiction",
            "category": "Entity",
            "expected_documents": ["policy2.pdf", "policy3.pdf", "policy4.pdf"]
        },

        # Claim Forms & Incident Reports
        {
            "query": "Commercial property damage claim form",
            "category": "Claims",
            "expected_documents": ["claim.pdf", "claim2.pdf"]
        },
        {
            "query": "Commercial insurance proposal form questionnaire",
            "category": "Claims",
            "expected_documents": ["claim1.pdf"]
        },
        {
            "query": "First notice of loss claim notification procedure",
            "category": "Claims",
            "expected_documents": ["claim.pdf", "policy2.pdf"]
        },
        {
            "query": "Third-party liability claim incident details",
            "category": "Claims",
            "expected_documents": ["claim.pdf"]
        },
        {
            "query": "Police report reference and witness details",
            "category": "Claims",
            "expected_documents": ["claim.pdf", "claim2.pdf"]
        },

        # Policy Exclusions & Conditions
        {
            "query": "War and terrorism exclusion wording",
            "category": "Exclusions",
            "expected_documents": ["policy2.pdf", "policy3.pdf", "policy4.pdf"]
        },
        {
            "query": "Sanctions limitation and embargo exclusion clause",
            "category": "Exclusions",
            "expected_documents": ["policy2.pdf", "policy3.pdf", "policy4.pdf"]
        },
        {
            "query": "Pre-existing medical condition exclusion",
            "category": "Exclusions",
            "expected_documents": ["policy1.pdf"]
        },
        {
            "query": "Cancellation clause notice period 30 days",
            "category": "Conditions",
            "expected_documents": ["policy2.pdf", "policy3.pdf"]
        },
        {
            "query": "Subrogation rights of insurer against negligent third parties",
            "category": "Conditions",
            "expected_documents": ["policy2.pdf", "policy4.pdf"]
        }
    ]
    
    return test_queries


def main():
    logger.info("Starting Task 28: Create Search Test Dataset...")
    search_tests = generate_search_test_dataset()
    
    # Validation
    logger.info(f"Generated {len(search_tests)} realistic search queries (Requirement: >= 30).")
    for i, item in enumerate(search_tests[:5]):
        logger.info(f"  Sample {i+1}: '{item['query']}' -> {item['expected_documents']}")

    out_path = OUTPUT_DIR / "search_test_dataset.json"
    save_json(search_tests, out_path)
    logger.info(f"Task 28 Complete: Saved search test dataset to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
