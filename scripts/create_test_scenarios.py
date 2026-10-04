#!/usr/bin/env python3
"""
scripts/create_test_scenarios.py - Task 32: Create AI Test Scenarios
Prepares end-to-end business scenarios for testing the production AI platform:
  - Renewal benchmarking and quote comparison
  - Automated FNOL claims processing
  - Broker commercial gap audit
  - Management liability limit adequacy review
  - Marine cargo transit risk and damage claims validation
Saves to output/ai_test_scenarios.json.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import save_json
from config.settings import OUTPUT_DIR

logger = setup_logger("create_test_scenarios")


def build_ai_test_scenarios() -> List[Dict[str, Any]]:
    """Builds a structured suite of end-to-end business test scenarios."""
    scenarios = [
        {
            "scenario_id": "SCENARIO-01",
            "scenario_name": "Renewal Benchmarking and Policy Comparison",
            "business_domain": "Commercial Underwriting & Broker Advisory",
            "description": "An SME client provides their expiring commercial policy and a renewal quote to evaluate coverage enhancements and pricing.",
            "customer_uploads": [
                {
                    "document_type": "Current Policy",
                    "file_reference": "policy2.pdf",
                    "description": "Expiring Allianz Commercial Select policy wording"
                },
                {
                    "document_type": "New Quote",
                    "file_reference": "policy3.pdf",
                    "description": "Proposed renewal schedule with alternative coverage terms"
                }
            ],
            "ai_expected_actions": [
                "Extract structured metadata (insurer, policyholder, period, currency, premium) from both documents.",
                "Perform pairwise side-by-side comparison across limits, deductibles, and territorial scopes.",
                "Identify missing coverage or excluded perils in the proposed quote.",
                "Highlight premium differences and calculate net financial delta.",
                "Suggest actionable policy improvements and broker negotiation points."
            ],
            "expected_outputs": [
                "policy_comparison_table",
                "coverage_gap_bullet_list",
                "broker_recommendation_memo"
            ]
        },
        {
            "scenario_id": "SCENARIO-02",
            "scenario_name": "Automated First Notice of Loss (FNOL) Claims Processing",
            "business_domain": "Claims Adjudication",
            "description": "A policyholder submits a property damage incident report for a commercial building water leakage incident.",
            "customer_uploads": [
                {
                    "document_type": "Claim Form",
                    "file_reference": "claim.pdf",
                    "description": "Completed Property Damage Incident Notification Form"
                },
                {
                    "document_type": "Active Policy",
                    "file_reference": "policy2.pdf",
                    "description": "Active Commercial Select Package Policy"
                }
            ],
            "ai_expected_actions": [
                "Extract loss date, incident location, claimant contact, and estimated repair costs from claim form.",
                "Verify policy was active on the date of loss (inception to expiry range).",
                "Verify property damage and water escape perils are included in coverage schedule.",
                "Check applicable deductible/excess payable by the claimant.",
                "Screen for policy conditions (e.g., prompt notice within 30 days) and validate exclusion carve-outs.",
                "Generate an automated preliminary claims assessment report for the loss adjuster."
            ],
            "expected_outputs": [
                "fnol_extraction_summary",
                "coverage_verification_status",
                "claim_triage_recommendation"
            ]
        },
        {
            "scenario_id": "SCENARIO-03",
            "scenario_name": "Broker Pre-Underwriting Commercial Gap Audit",
            "business_domain": "Risk Engineering & Sales Enablement",
            "description": "A commercial insurance broker prepares for a renewal meeting by identifying unaddressed risk exposures.",
            "customer_uploads": [
                {
                    "document_type": "Commercial Policy",
                    "file_reference": "policy2.pdf",
                    "description": "Current retail commercial package policy"
                },
                {
                    "document_type": "Proposal Form",
                    "file_reference": "claim1.pdf",
                    "description": "Updated annual turnover and employee declaration"
                }
            ],
            "ai_expected_actions": [
                "Analyze active policy wordings against the commercial broker review checklist.",
                "Detect unhedged perils such as Cyber Attack, Inundation/Flood, and Director Misconduct.",
                "Flag missing standalone Cyber insurance and limited 12-month Business Interruption indemnity.",
                "Generate a formal Broker Advisory Memorandum recommending comprehensive policy extensions."
            ],
            "expected_outputs": [
                "coverage_gap_audit",
                "checklist_compliance_score",
                "client_facing_advisory_report"
            ]
        },
        {
            "scenario_id": "SCENARIO-04",
            "scenario_name": "Executive Management Liability Adequacy Review",
            "business_domain": "Executive Risk & Corporate Governance",
            "description": "A corporate client reviews their D&O policy limits ahead of an initial public offering (IPO) or cross-border expansion.",
            "customer_uploads": [
                {
                    "document_type": "D&O Policy",
                    "file_reference": "policy3.pdf",
                    "description": "Management Liability policy wording"
                }
            ],
            "ai_expected_actions": [
                "Extract aggregate limit of liability, individual director coverage, and corporate reimbursement terms.",
                "Review defense costs advancement clause and repayment obligations.",
                "Verify retroactive date continuity and preservation of prior acts cover.",
                "Validate regulatory investigation inquiry sub-limits.",
                "Provide corporate secretary with executive governance summary and limit benchmark."
            ],
            "expected_outputs": [
                "executive_limit_summary",
                "governance_risk_rating",
                "defense_advancement_analysis"
            ]
        },
        {
            "scenario_id": "SCENARIO-05",
            "scenario_name": "Marine Cargo Transit Risk & Claims Validation",
            "business_domain": "Marine & Logistics Insurance",
            "description": "A freight forwarder submits a claim for damaged electrical equipment transported via ocean vessel and inland road transit.",
            "customer_uploads": [
                {
                    "document_type": "Cargo Policy",
                    "file_reference": "policy4.pdf",
                    "description": "Marine & Transit Cargo Policy Wording"
                },
                {
                    "document_type": "Damage Form",
                    "file_reference": "claim2.pdf",
                    "description": "Transit Damage Inspection Report"
                }
            ],
            "ai_expected_actions": [
                "Verify transit route, conveyance type, and packing standards against policy warranty conditions.",
                "Determine applicable Institute Cargo Clauses (A, B, or C) coverage trigger.",
                "Confirm loss did not arise from excluded perils (ordinary leakage, wear and tear, or insolvency of vessel owners).",
                "Calculate indemnification amount net of transit deductible and salvage recovery.",
                "Issue claims adjustment guidance and subrogation recovery recommendations."
            ],
            "expected_outputs": [
                "transit_clause_evaluation",
                "cargo_loss_computation",
                "recovery_subrogation_action_plan"
            ]
        }
    ]
    return scenarios


def main():
    logger.info("Starting Task 32: Create AI Test Scenarios...")
    scenarios = build_ai_test_scenarios()
    logger.info(f"Generated {len(scenarios)} multi-step business test scenarios.")
    for s in scenarios:
        logger.info(f"  [{s['scenario_id']}] {s['scenario_name']} ({s['business_domain']})")

    out_path = OUTPUT_DIR / "ai_test_scenarios.json"
    save_json(scenarios, out_path)
    logger.info(f"Task 32 Complete: Saved AI test scenarios to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
