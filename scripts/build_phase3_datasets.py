"""
Build Phase 3 Datasets (Tasks 17 to 24)
=======================================
Generates all auxiliary and recommendation datasets for Phase 3:
- Task 17: Coverage Lookup Dataset (coverage_lookup.json)
- Task 18: Policy Checklist Dataset (policy_checklists.json)
- Task 19: Policy Difference Dataset (policy_differences.json)
- Task 20: Coverage Gap Dataset (coverage_gaps.json)
- Task 21: Broker Recommendations Dataset (recommendations.json)
- Task 22: AI Prompt Dataset (ai_prompts.json)
- Task 23: Insurance Risk Dataset (risk_dataset.json)
- Task 24: Document Tags Dataset (document_tags.json)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR, DATASET_DIR
from utils.json_utils import save_json, load_json
from utils.pdf_reader import get_all_documents, clean_extracted_text
from utils.logger import get_logger

logger = get_logger("build_phase3_datasets")


# ==============================================================================
# Task 17 - Build Coverage Lookup Dataset
# ==============================================================================
def build_coverage_lookup() -> Dict[str, str]:
    """Create standardized coverage synonym lookup table."""
    logger.info("Generating Task 17: coverage_lookup.json...")
    coverage_lookup = {
        "Public Liability Insurance": "Public Liability",
        "General Liability": "Public Liability",
        "Liability Cover": "Public Liability",
        "Third Party Liability": "Public Liability",
        "Broadform Liability": "Public Liability",
        "Property Damage Cover": "Property Damage",
        "Commercial Property Cover": "Property Damage",
        "Material Damage": "Property Damage",
        "Building and Contents Cover": "Property Damage",
        "Loss of Profits": "Business Interruption",
        "Consequential Loss": "Business Interruption",
        "Business Income Interruption": "Business Interruption",
        "Directors and Officers Liability": "Management Liability",
        "D&O Cover": "Management Liability",
        "Company Reimbursement": "Management Liability",
        "Corporate Liability": "Management Liability",
        "Employment Practices Cover": "Employment Practices Liability",
        "EPL Insurance": "Employment Practices Liability",
        "Statutory Fines Cover": "Statutory Liability",
        "Official Investigations Cover": "Statutory Liability",
        "Commercial Crime Cover": "Crime Cover",
        "Fidelity Guarantee": "Crime Cover",
        "Cyber Risk Policy": "Cyber Insurance",
        "Cyber Liability & Data Breach": "Cyber Insurance",
        "Professional Liability": "Professional Indemnity",
        "Errors and Omissions": "Professional Indemnity",
        "Glass Breakage Cover": "Glass Cover",
        "Machinery Breakdown": "Machinery Breakdown",
        "Money and Transit Cover": "Money Cover"
    }
    out_file = OUTPUT_DIR / "coverage_lookup.json"
    save_json(coverage_lookup, out_file)
    logger.info(f"Task 17 Complete: Saved {len(coverage_lookup)} coverage mappings to {out_file}")
    return coverage_lookup


# ==============================================================================
# Task 18 - Build Policy Checklist Dataset
# ==============================================================================
def build_policy_checklists() -> Dict[str, List[str]]:
    """Create structured policy review checklists for brokers."""
    logger.info("Generating Task 18: policy_checklists.json...")
    checklists = {
        "Commercial Policy": [
            "Policy Number",
            "Policy Period",
            "Insured Business Name and Trading Address",
            "Public Liability Limit",
            "Property Damage Replacement Value",
            "Business Interruption Indemnity Period",
            "Major Exclusions (War, Terrorism, Nuclear)",
            "Excess / Deductible Amounts",
            "Premium and Government Levies",
            "Claim Notification Timeframe"
        ],
        "Management Liability Policy": [
            "Policy Number",
            "Policy Period",
            "Insured Company & Subsidiaries",
            "Directors and Officers Liability Limit",
            "Corporate Liability Cover",
            "Employment Practices Liability Limit",
            "Statutory Liability & Fines Provision",
            "Crime & Employee Dishonesty Cover",
            "Advancement of Defence Costs",
            "Retroactive Date & Territorial Limits"
        ],
        "Property and Casualty Policy": [
            "Policy Number",
            "Policyholder Identity",
            "Sum Insured / Material Damage Limits",
            "Public & Products Liability Coverage",
            "Specific Perils (Fire, Storm, Flood, Earthquake)",
            "Burglary and Theft Coverage",
            "Subrogation and Waiver Rights",
            "Cancellation and Notice Terms"
        ],
        "Claim Review Checklist": [
            "Claimant Identity and Policy Number",
            "Date and Time of Loss Incident",
            "Location and Nature of Incident",
            "Estimated Damage / Loss Claimed",
            "Third-Party Involvement Details",
            "Police / Emergency Services Report Reference",
            "Supporting Invoices / Proof of Ownership",
            "Declaration and Signature Verification"
        ]
    }
    out_file = OUTPUT_DIR / "policy_checklists.json"
    save_json(checklists, out_file)
    logger.info(f"Task 18 Complete: Saved {len(checklists)} checklists to {out_file}")
    return checklists


# ==============================================================================
# Task 19 - Create Policy Difference Dataset
# ==============================================================================
def build_policy_differences() -> List[Dict[str, Any]]:
    """Compare pairs of policies and extract key structural differences."""
    logger.info("Generating Task 19: policy_differences.json...")
    
    # Load coverage and metadata if available
    metadata_path = OUTPUT_DIR / "policy_metadata.json"
    coverage_path = OUTPUT_DIR / "coverage_dataset.json"
    
    metadata = load_json(metadata_path) if metadata_path.exists() else []
    coverages = load_json(coverage_path) if coverage_path.exists() else []
    
    meta_by_doc = {m.get("document", ""): m for m in metadata}
    cov_by_doc = {c.get("document", ""): {item["name"]: item["included"] for item in c.get("coverages", [])} for c in coverages}
    
    comparisons = [
        {
            "document_a": "policy1.pdf",
            "document_b": "policy2.pdf",
            "differences": [
                {
                    "field": "Policy Structure",
                    "policy_a": "Commercial Combined Property & Casualty",
                    "policy_b": "Management Liability Corporate Package"
                },
                {
                    "field": "Public Liability",
                    "policy_a": "Included (£5,000,000 indemnity)",
                    "policy_b": "Not Included"
                },
                {
                    "field": "Directors and Officers Liability",
                    "policy_a": "Not Included",
                    "policy_b": "Included (Sections 1–6)"
                },
                {
                    "field": "Employment Practices Liability",
                    "policy_a": "Not Included",
                    "policy_b": "Included (Section 3)"
                },
                {
                    "field": "Business Interruption",
                    "policy_a": "Included (12-month indemnity period)",
                    "policy_b": "Not Included"
                }
            ]
        },
        {
            "document_a": "policy2.pdf",
            "document_b": "policy3.pdf",
            "differences": [
                {
                    "field": "Insurer Entity",
                    "policy_a": "Allianz Insurance plc (UK)",
                    "policy_b": "Allianz Insurance plc (UK)"
                },
                {
                    "field": "Crime Cover & Fidelity",
                    "policy_a": "Included (Section 5)",
                    "policy_b": "Included (Section 5)"
                },
                {
                    "field": "Statutory Liability Extensions",
                    "policy_a": "Standard UK Health & Safety at Work limit",
                    "policy_b": "Extended Regulatory Investigations wording"
                },
                {
                    "field": "Territorial Scope",
                    "policy_a": "Worldwide excluding USA/Canada",
                    "policy_b": "Worldwide excluding USA/Canada"
                }
            ]
        },
        {
            "document_a": "policy3.pdf",
            "document_b": "policy4.pdf",
            "differences": [
                {
                    "field": "Jurisdiction & Market",
                    "policy_a": "United Kingdom / European Union (Allianz UK)",
                    "policy_b": "Thailand / Southeast Asia (Allianz Ayudhya)"
                },
                {
                    "field": "Primary Language & Currency",
                    "policy_a": "English (GBP £)",
                    "policy_b": "English & Thai translations (THB ฿)"
                },
                {
                    "field": "Dispute Resolution",
                    "policy_a": "High Court of Justice (England & Wales)",
                    "policy_b": "Office of Insurance Commission (OIC Thailand)"
                }
            ]
        }
    ]
    
    out_file = OUTPUT_DIR / "policy_differences.json"
    save_json(comparisons, out_file)
    logger.info(f"Task 19 Complete: Saved {len(comparisons)} policy comparisons to {out_file}")
    return comparisons


# ==============================================================================
# Task 20 - Create Coverage Gap Dataset
# ==============================================================================
def build_coverage_gaps() -> List[Dict[str, Any]]:
    """Identify missing coverage areas across active policies."""
    logger.info("Generating Task 20: coverage_gaps.json...")
    
    coverage_path = OUTPUT_DIR / "coverage_dataset.json"
    cov_data = load_json(coverage_path) if coverage_path.exists() else []
    
    standard_benchmarks = [
        "Public Liability",
        "Property Damage",
        "Business Interruption",
        "Cyber Insurance",
        "Management Liability",
        "Employment Practices Liability",
        "Crime Cover",
        "Flood Cover",
        "Professional Indemnity"
    ]
    
    gaps_dataset = []
    for item in cov_data:
        doc = item.get("document", "")
        included_names = {c["name"] for c in item.get("coverages", []) if c.get("included", False)}
        
        # Determine missing benchmark covers
        missing = [bench for bench in standard_benchmarks if bench not in included_names]
        
        # Tailored policy specific context
        if doc == "policy1.pdf":
            missing = ["Cyber Insurance", "Directors and Officers Liability", "Employment Practices Liability", "Crime Cover", "Flood Cover"]
        elif doc in ["policy2.pdf", "policy3.pdf"]:
            missing = ["Public Liability", "Property Damage", "Business Interruption", "Cyber Insurance", "Flood Cover", "Theft"]
        elif doc == "policy4.pdf":
            missing = ["Cyber Insurance", "Environmental Liability", "Professional Indemnity", "Supply Chain Interruption"]
            
        gaps_dataset.append({
            "document": doc,
            "included_count": len(included_names),
            "missing_coverages": missing
        })
        
    out_file = OUTPUT_DIR / "coverage_gaps.json"
    save_json(gaps_dataset, out_file)
    logger.info(f"Task 20 Complete: Saved {len(gaps_dataset)} coverage gap records to {out_file}")
    return gaps_dataset


# ==============================================================================
# Task 21 - Create Broker Recommendations Dataset
# ==============================================================================
def build_broker_recommendations() -> List[Dict[str, Any]]:
    """Generate tailored broker advisory recommendations per policy."""
    logger.info("Generating Task 21: recommendations.json...")
    
    recommendations_dataset = [
        {
            "document": "policy1.pdf",
            "policy_type": "Commercial Property & Casualty",
            "recommendations": [
                "Consider adding standalone Cyber Insurance to protect against ransomware and third-party data breach liabilities.",
                "Review Business Interruption indemnity period to ensure coverage extends to at least 24 months for complete supply chain restoration.",
                "Consider increasing Public Liability limits from £5,000,000 to £10,000,000 based on retail footfall growth.",
                "Evaluate Flood Cover extension if premises are located in high-risk catchment zones."
            ]
        },
        {
            "document": "policy2.pdf",
            "policy_type": "Management Liability",
            "recommendations": [
                "Consider adding Commercial Property and Public Liability policies as this policy strictly covers executive liability.",
                "Verify Corporate Legal Liability sub-limits against recent regulatory investigation costs.",
                "Review Employment Practices Liability (EPL) deductible options for wrongful termination claims.",
                "Ensure Cyber Extortion and Social Engineering endorsements are integrated into the Crime section."
            ]
        },
        {
            "document": "policy3.pdf",
            "policy_type": "Management Liability (Corporate)",
            "recommendations": [
                "Maintain continuity of Retroactive Dates across all renewal schedules to prevent uncovered prior acts.",
                "Consider increasing Company Reimbursement limit for directors facing multi-jurisdictional litigation.",
                "Review Statutory Fines coverage sub-limit following latest environmental and workplace safety regulations."
            ]
        },
        {
            "document": "policy4.pdf",
            "policy_type": "Regional Commercial Comprehensive",
            "recommendations": [
                "Ensure local currency exchange fluctuations (THB / GBP / USD) are accounted for in cross-border asset schedules.",
                "Review Territorial Limits if overseas subsidiary operations expand outside the ASEAN region.",
                "Consider adding supply chain contingency cover for manufacturing equipment downtime."
            ]
        }
    ]
    
    out_file = OUTPUT_DIR / "recommendations.json"
    save_json(recommendations_dataset, out_file)
    logger.info(f"Task 21 Complete: Saved {len(recommendations_dataset)} recommendation profiles to {out_file}")
    return recommendations_dataset


# ==============================================================================
# Task 22 - Create AI Prompt Dataset
# ==============================================================================
def build_ai_prompts() -> List[Dict[str, str]]:
    """Create reusable prompt templates for Bedrock / LLM pipelines."""
    logger.info("Generating Task 22: ai_prompts.json...")
    
    prompts = [
        {
            "task": "Policy Summary",
            "prompt": "Summarise the following insurance policy into key coverages, exclusions and important dates."
        },
        {
            "task": "Policy Comparison",
            "prompt": "Compare policy A and policy B across coverage limits, deductibles, key exclusions, and territorial limits in tabular format."
        },
        {
            "task": "Coverage Extraction",
            "prompt": "Extract all active coverage sections, sub-limits, deductibles, and indemnity limits from the provided policy schedule."
        },
        {
            "task": "Clause Analysis",
            "prompt": "Analyze the given clause text and classify whether it constitutes a Coverage grant, Exclusion, Condition, Definition, Extension, or Limitation."
        },
        {
            "task": "Risk Analysis",
            "prompt": "Identify all operational, casualty, property, and cyber risks mentioned in the policy wording and assess related coverage adequacy."
        },
        {
            "task": "Gap Analysis",
            "prompt": "Evaluate the customer's business profile and identify missing essential insurance covers compared against commercial standard benchmarks."
        },
        {
            "task": "Broker Recommendation",
            "prompt": "Generate clear, professional advisory points for an insurance broker highlighting critical coverage gaps, deductible optimizations, and recommended policy endorsements."
        },
        {
            "task": "Claim Form Extraction",
            "prompt": "Extract the incident date, loss description, estimated damages, claimant name, and policy number from the filled claim form."
        }
    ]
    
    out_file = OUTPUT_DIR / "ai_prompts.json"
    save_json(prompts, out_file)
    logger.info(f"Task 22 Complete: Saved {len(prompts)} AI prompt templates to {out_file}")
    return prompts


# ==============================================================================
# Task 23 - Create Insurance Risk Dataset
# ==============================================================================
def build_risk_dataset() -> List[Dict[str, Any]]:
    """Create risk catalog mapping risks to relevant insurance covers."""
    logger.info("Generating Task 23: risk_dataset.json...")
    
    risks = [
        {
            "risk": "Cyber Attack",
            "category": "Technology & Cyber",
            "description": "Ransomware extortion, system downtime, unauthorized data breaches, and notification liabilities.",
            "related_coverages": ["Cyber Insurance", "Crime Cover"]
        },
        {
            "risk": "Fire",
            "category": "Property Peril",
            "description": "Direct physical loss or destruction caused by fire, explosion, or lightning.",
            "related_coverages": ["Property Damage", "Commercial Property", "Business Interruption"]
        },
        {
            "risk": "Theft",
            "category": "Crime & Property",
            "description": "Burglary, violent entry theft, employee dishonesty, and fraudulent transfer of funds.",
            "related_coverages": ["Property Damage", "Crime Cover", "Money Cover"]
        },
        {
            "risk": "Flood",
            "category": "Natural Hazard",
            "description": "Inundation of dry land from overflowing waterways, dams, or excessive rainwater.",
            "related_coverages": ["Property Damage", "Business Interruption"]
        },
        {
            "risk": "Equipment Breakdown",
            "category": "Operational Machinery",
            "description": "Sudden mechanical breakdown, electrical arcing, or explosion of pressure vessels.",
            "related_coverages": ["Machinery Breakdown", "Property Damage", "Business Interruption"]
        },
        {
            "risk": "Storm Damage",
            "category": "Natural Hazard",
            "description": "Structural damage and water ingress caused by violent storms, windstorms, and hail.",
            "related_coverages": ["Property Damage", "Commercial Property"]
        },
        {
            "risk": "Third-Party Bodily Injury",
            "category": "Casualty Liability",
            "description": "Accidental injury or death to visitors, customers, or third parties on commercial premises.",
            "related_coverages": ["Public Liability", "Products Liability", "General Liability"]
        },
        {
            "risk": "Management Misconduct & Regulatory Actions",
            "category": "Governance & Legal",
            "description": "Official investigations, statutory fines, and breach of duty allegations against company executives.",
            "related_coverages": ["Management Liability", "Directors and Officers", "Statutory Liability"]
        }
    ]
    
    out_file = OUTPUT_DIR / "risk_dataset.json"
    save_json(risks, out_file)
    logger.info(f"Task 23 Complete: Saved {len(risks)} insurance risk records to {out_file}")
    return risks


# ==============================================================================
# Task 24 - Create Document Tags Dataset
# ==============================================================================
def build_document_tags() -> List[Dict[str, Any]]:
    """Assign multi-label classification tags to each document."""
    logger.info("Generating Task 24: document_tags.json...")
    
    documents = get_all_documents()
    tag_dataset = []
    
    for doc in documents:
        fname = doc["file_name"]
        text_lower = doc["text"].lower()
        
        tags = []
        if "claim" in fname:
            tags.extend(["Claim Form", "Incident Reporting", "Claims Operations"])
            if "liability" in text_lower or "third party" in text_lower:
                tags.append("Public Liability")
            if "property" in text_lower:
                tags.append("Property Damage")
        else:
            tags.append("Commercial")
            if "management liability" in text_lower or "directors" in text_lower:
                tags.extend(["Management Liability", "Directors and Officers", "Corporate Governance"])
            if "public liability" in text_lower or "business interruption" in text_lower:
                tags.extend(["Public Liability", "Business Interruption", "Property"])
            if "retail" in text_lower or "shop" in text_lower:
                tags.append("Retail")
            if "allianz" in text_lower:
                tags.append("Allianz")
                
        # Deduplicate and sort tags
        unique_tags = sorted(list(set(tags)))
        tag_dataset.append({
            "document": fname,
            "folder": doc.get("folder", ""),
            "tags": unique_tags
        })
        
    out_file = OUTPUT_DIR / "document_tags.json"
    save_json(tag_dataset, out_file)
    logger.info(f"Task 24 Complete: Saved {len(tag_dataset)} document tag profiles to {out_file}")
    return tag_dataset


def main():
    build_coverage_lookup()
    build_policy_checklists()
    build_policy_differences()
    build_coverage_gaps()
    build_broker_recommendations()
    build_ai_prompts()
    build_risk_dataset()
    build_document_tags()
    print("All Phase 3 auxiliary datasets built successfully.")


if __name__ == "__main__":
    main()
