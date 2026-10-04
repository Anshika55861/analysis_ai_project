#!/usr/bin/env python3
"""
scripts/create_rules.py - Task 30: Create Rules Dataset
Creates a reusable, structured rules dataset for automated insurance decisioning:
  - Coverage gap advisory rules
  - Indemnity limit adequacy rules
  - Expiry and renewal triggers
  - Peril exposure and deductible thresholds
Saves to output/rules_dataset.json.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json
from config.settings import OUTPUT_DIR

logger = setup_logger("create_rules")


def build_rules_dataset() -> List[Dict[str, Any]]:
    """Builds a comprehensive business rules dataset for insurance platforms."""
    rules = [
        # Coverage Gap Rules
        {
            "rule": "Missing Cyber Insurance",
            "action": "Recommend Cyber Insurance",
            "condition": "cyber_insurance == false and policy_type in ['commercial', 'corporate']",
            "category": "Coverage Gap",
            "severity": "High"
        },
        {
            "rule": "Missing Business Interruption Cover",
            "action": "Recommend adding Business Interruption extension with 24-month indemnity period",
            "condition": "business_interruption == false and property_damage == true",
            "category": "Coverage Gap",
            "severity": "High"
        },
        {
            "rule": "Missing Directors & Officers Liability",
            "action": "Recommend Management Liability policy for corporate governance protection",
            "condition": "d_and_o == false and entity_type in ['limited_company', 'plc', 'partnership']",
            "category": "Coverage Gap",
            "severity": "Medium"
        },
        {
            "rule": "Missing Terrorism Endorsement",
            "action": "Recommend Pool Re / commercial terrorism extension for urban commercial locations",
            "condition": "terrorism_cover == false and location_type == 'metropolitan'",
            "category": "Coverage Gap",
            "severity": "Medium"
        },
        {
            "rule": "Missing Accidental Disablement Rider",
            "action": "Recommend personal accident permanent disablement scale add-on",
            "condition": "accidental_disablement == false and policy_type == 'personal_accident'",
            "category": "Coverage Gap",
            "severity": "Medium"
        },

        # Limit Adequacy Rules
        {
            "rule": "Public Liability limit is below $10M",
            "action": "Flag for review and recommend limit increase to $10,000,000",
            "condition": "public_liability_limit < 10000000",
            "category": "Limit Adequacy",
            "severity": "High"
        },
        {
            "rule": "Employers Liability statutory minimum check",
            "action": "Ensure statutory minimum of £10M / £5M is maintained and certified",
            "condition": "employers_liability_limit < 10000000 and jurisdiction == 'UK'",
            "category": "Compliance",
            "severity": "High"
        },
        {
            "rule": "Low Property Replacement Sum Insured",
            "action": "Flag underinsurance risk; require professional valuation report",
            "condition": "property_sum_insured < estimated_rebuild_cost",
            "category": "Limit Adequacy",
            "severity": "High"
        },
        {
            "rule": "Low Personal Medical Aggregate Limit",
            "action": "Recommend upgrading to comprehensive tier for chronic emergency cover",
            "condition": "medical_aggregate_limit < 500000 and currency == 'THB'",
            "category": "Limit Adequacy",
            "severity": "Medium"
        },

        # Renewal & Expiry Rules
        {
            "rule": "Policy expires within 30 days",
            "action": "Renewal reminder and request updated exposure declarations",
            "condition": "days_to_expiry <= 30 and days_to_expiry > 0",
            "category": "Renewal",
            "severity": "High"
        },
        {
            "rule": "Policy expired",
            "action": "Flag immediate lapse in coverage and issue urgent reinstatement notice",
            "condition": "days_to_expiry <= 0",
            "category": "Renewal",
            "severity": "Critical"
        },
        {
            "rule": "Retroactive Date Continuity Check",
            "action": "Verify inception date continuity to preserve claims-made coverage history",
            "condition": "policy_type in ['d_and_o', 'epl'] and renewal == true",
            "category": "Compliance",
            "severity": "High"
        },

        # Deductible & Excess Rules
        {
            "rule": "Excessive Commercial Property Deductible",
            "action": "Flag high deductible; recommend voluntary excess buy-down rider",
            "condition": "property_deductible > 0.05 * total_sum_insured",
            "category": "Deductible",
            "severity": "Medium"
        },
        {
            "rule": "Nil Excess on High-Frequency Risks",
            "action": "Suggest standard £250 excess to reduce policy premium",
            "condition": "policy_excess == 0 and peril in ['water_escape', 'glass_breakage']",
            "category": "Deductible",
            "severity": "Low"
        },

        # Peril Exposure Rules
        {
            "rule": "High Flood Exposure Zone",
            "action": "Require specialized flood risk survey and confirm flood defense maintenance",
            "condition": "flood_zone in [2, 3] and flood_cover == true",
            "category": "Risk Exposure",
            "severity": "High"
        },
        {
            "rule": "International Cargo Conveyance",
            "action": "Ensure Institute Cargo Clauses (A) all-risks with war and strikes clauses applied",
            "condition": "transit_type == 'international' and cargo_policy == true",
            "category": "Coverage",
            "severity": "High"
        }
    ]
    return rules


def main():
    logger.info("Starting Task 30: Create Rules Dataset...")
    rules = build_rules_dataset()
    logger.info(f"Generated {len(rules)} business rules across {len(set(r['category'] for r in rules))} categories.")

    for i, r in enumerate(rules[:3]):
        logger.info(f"  Rule {i+1}: '{r['rule']}' -> Action: '{r['action']}'")

    out_path = OUTPUT_DIR / "rules_dataset.json"
    save_json(rules, out_path)
    logger.info(f"Task 30 Complete: Saved rules dataset to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
