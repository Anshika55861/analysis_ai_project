#!/usr/bin/env python3
"""
scripts/create_ai_evaluations.py - Task 29: Create AI Response Evaluation Dataset
Prepares ground-truth evaluation benchmark cases for 5 core AI tasks:
  1. Policy summary
  2. Coverage extraction
  3. Clause explanation
  4. Policy comparison
  5. Risk identification
Saves benchmark to output/ai_evaluation.json.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json, load_json
from config.settings import OUTPUT_DIR

logger = setup_logger("create_ai_evaluations")


def build_ai_evaluation_dataset() -> List[Dict[str, Any]]:
    """Generates ground-truth evaluation test cases for AI models."""
    
    # Load actual extracted data to ground the evaluations
    cov_file = OUTPUT_DIR / "coverage_dataset.json"
    coverages_data = load_json(cov_file) if cov_file.exists() else []
    cov_by_doc = {}
    for item in coverages_data:
        d = item.get("document", "")
        included = [c.get("name") or c.get("coverage_name") for c in item.get("coverages", []) if c.get("included") and (c.get("name") or c.get("coverage_name"))]
        cov_by_doc[d] = included

    evaluations: List[Dict[str, Any]] = [
        # 1. Policy Summary Task
        {
            "task": "Policy Summary",
            "document": "policy1.pdf",
            "input_context": "Summarize policy1.pdf core coverages and key exclusions.",
            "expected_result": {
                "policy_type": "Special Personal Health and Accident Insurance",
                "insurer": "Allianz Ayudhya General Insurance Public Company Limited",
                "core_coverages": ["Personal Accident", "Medical Expenses"],
                "key_exclusions": ["Pre-existing conditions", "Extreme hazardous sports", "Suicide or self-inflicted injury"]
            }
        },
        {
            "task": "Policy Summary",
            "document": "policy2.pdf",
            "input_context": "Summarize policy2.pdf commercial package coverages.",
            "expected_result": {
                "policy_type": "Commercial Select Package Policy",
                "insurer": "Allianz Insurance plc",
                "core_coverages": ["Property Damage", "Business Interruption", "Public Liability", "Employers Liability"],
                "key_exclusions": ["War and terrorism", "Cyber attack loss", "Pollution unless sudden and accidental"]
            }
        },
        {
            "task": "Policy Summary",
            "document": "policy3.pdf",
            "input_context": "Summarize policy3.pdf management liability wording.",
            "expected_result": {
                "policy_type": "Directors and Officers / Management Liability",
                "insurer": "Allianz Insurance plc",
                "core_coverages": ["Directors and Officers Liability", "Corporate Legal Liability", "Employment Practices Liability"],
                "key_exclusions": ["Deliberate fraudulent acts", "Prior pending litigation before retroactive date"]
            }
        },
        {
            "task": "Policy Summary",
            "document": "policy4.pdf",
            "input_context": "Summarize policy4.pdf transit cargo insurance.",
            "expected_result": {
                "policy_type": "Marine and Inland Transit Cargo Policy",
                "insurer": "Allianz Insurance plc",
                "core_coverages": ["Transit Damage", "Theft in Transit", "General Average Contribution"],
                "key_exclusions": ["Inherent vice or natural deterioration", "Insufficient packaging", "Delay in transit"]
            }
        },

        # 2. Coverage Extraction Task
        {
            "task": "Coverage Extraction",
            "document": "policy2.pdf",
            "input_context": "Extract all included affirmative coverages for policy2.pdf.",
            "expected_result": cov_by_doc.get("policy2.pdf") or ["Public Liability", "Property Damage", "Business Interruption"]
        },
        {
            "task": "Coverage Extraction",
            "document": "policy3.pdf",
            "input_context": "Extract all included affirmative coverages for policy3.pdf.",
            "expected_result": cov_by_doc.get("policy3.pdf") or ["Directors and Officers Liability", "Corporate Legal Liability", "Employment Practices Liability"]
        },
        {
            "task": "Coverage Extraction",
            "document": "policy1.pdf",
            "input_context": "Extract all included affirmative coverages for policy1.pdf.",
            "expected_result": cov_by_doc.get("policy1.pdf") or ["Personal Accident", "Medical Expenses"]
        },
        {
            "task": "Coverage Extraction",
            "document": "policy4.pdf",
            "input_context": "Extract all included affirmative coverages for policy4.pdf.",
            "expected_result": cov_by_doc.get("policy4.pdf") or ["Marine and Transit Cargo", "Theft in Transit"]
        },

        # 3. Clause Explanation Task
        {
            "task": "Clause Explanation",
            "document": "policy2.pdf",
            "input_context": "Explain the operational meaning of the Subrogation Clause.",
            "expected_result": {
                "clause_name": "Subrogation Rights",
                "plain_english_explanation": "Allows the insurer to step into the policyholder's legal rights after paying a claim to recover damages from the responsible third party.",
                "legal_effect": "The policyholder cannot waive or compromise third-party recovery rights without insurer consent."
            }
        },
        {
            "task": "Clause Explanation",
            "document": "policy3.pdf",
            "input_context": "Explain the operational meaning of the Defense Costs Advancement Clause.",
            "expected_result": {
                "clause_name": "Advancement of Defense Costs",
                "plain_english_explanation": "The insurer pays legal defense fees and expenses as they are incurred before final resolution or judgment of the claim.",
                "legal_effect": "Directors and officers do not have to fund protracted litigation out-of-pocket, subject to repayment if fraud is proven."
            }
        },
        {
            "task": "Clause Explanation",
            "document": "policy1.pdf",
            "input_context": "Explain the operational meaning of the Pre-existing Condition Exclusion.",
            "expected_result": {
                "clause_name": "Pre-Existing Conditions Exclusion",
                "plain_english_explanation": "Medical illnesses or injuries that manifested or were diagnosed before the policy effective date are excluded from coverage.",
                "legal_effect": "Claims arising directly or indirectly from prior chronic symptoms will not be reimbursed."
            }
        },

        # 4. Policy Comparison Task
        {
            "task": "Policy Comparison",
            "document": "policy2.pdf vs policy3.pdf",
            "input_context": "Compare commercial property coverage against management liability.",
            "expected_result": {
                "comparison_focus": "Commercial Package vs Management Liability",
                "property_coverage": "policy2 covers physical property and business interruption; policy3 covers no physical property.",
                "liability_coverage": "policy2 covers third-party bodily injury/property damage; policy3 covers executive management decisions and regulatory liability.",
                "cyber_coverage": "policy2 excludes cyber; policy3 offers management-level cyber loss extensions."
            }
        },
        {
            "task": "Policy Comparison",
            "document": "policy1.pdf vs policy2.pdf",
            "input_context": "Compare personal health policy against commercial package policy.",
            "expected_result": {
                "comparison_focus": "Personal Accident/Health vs Commercial Package",
                "insured_entity": "policy1 insures an individual person; policy2 insures a registered business/commercial enterprise.",
                "currency": "policy1 is denominated in THB; policy2 is denominated in GBP.",
                "governing_law": "policy1 is governed by Thailand OIC regulations; policy2 is governed by English Law & FCA."
            }
        },

        # 5. Risk Identification Task
        {
            "task": "Risk Identification",
            "document": "policy2.pdf",
            "input_context": "Identify the primary commercial operational risks addressed in policy2.pdf.",
            "expected_result": [
                "Fire and Explosion",
                "Theft and Burglary",
                "Flood and Water Damage",
                "Public Bodily Injury and Third-Party Property Damage",
                "Business Interruption Loss"
            ]
        },
        {
            "task": "Risk Identification",
            "document": "policy3.pdf",
            "input_context": "Identify the primary executive and governance risks addressed in policy3.pdf.",
            "expected_result": [
                "Management Misconduct",
                "Regulatory Investigation Costs",
                "Employment Practices Liability",
                "Shareholder and Derivative Lawsuits"
            ]
        },
        {
            "task": "Risk Identification",
            "document": "policy4.pdf",
            "input_context": "Identify the transportation perils addressed in policy4.pdf.",
            "expected_result": [
                "Cargo Damage in Transit",
                "Theft and Hijacking",
                "Vessel Stranding or Overturning",
                "General Average and Salvage Charges"
            ]
        }
    ]

    return evaluations


def main():
    logger.info("Starting Task 29: Create AI Response Evaluation Dataset...")
    eval_dataset = build_ai_evaluation_dataset()
    
    tasks_covered = set(e["task"] for e in eval_dataset)
    logger.info(f"Generated {len(eval_dataset)} ground-truth AI evaluation test cases across {len(tasks_covered)} tasks.")
    logger.info(f"Tasks covered: {sorted(list(tasks_covered))}")

    out_path = OUTPUT_DIR / "ai_evaluation.json"
    save_json(eval_dataset, out_path)
    logger.info(f"Task 29 Complete: Saved AI evaluation dataset to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
