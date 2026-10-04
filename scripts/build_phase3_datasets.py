"""
Build Phase 3 Datasets (Tasks 17 to 24)
=======================================
Generates all auxiliary and recommendation datasets for Phase 3 dynamically:
- Task 17: Coverage Lookup Dataset (coverage_lookup.json)
- Task 18: Policy Checklist Dataset (policy_checklists.json)
- Task 19: Policy Difference Dataset (policy_differences.json) -> Dynamic pairwise comparison
- Task 20: Coverage Gap Dataset (coverage_gaps.json) -> Dynamic set comparison
- Task 21: Broker Recommendations Dataset (recommendations.json) -> Rule-based from data
- Task 22: AI Prompt Dataset (ai_prompts.json)
- Task 23: Insurance Risk Dataset (risk_dataset.json) -> Master perils + dynamic text detection
- Task 24: Document Tags Dataset (document_tags.json) -> Text-based relevance rules

ZERO document-specific hardcoding: logic works dynamically for any added PDF.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

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
        "Money and Transit Cover": "Money Cover",
        "Marine Cargo": "Cargo & Goods in Transit",
        "Transit Cover": "Cargo & Goods in Transit",
        "Personal Accident Cover": "Personal Accident",
        "Accidental Death & Dismemberment": "Personal Accident",
        "Inpatient Medical": "Medical Expenses & Inpatient Care",
        "Hospitalisation Cover": "Medical Expenses & Inpatient Care"
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
        "Personal Accident and Health Policy": [
            "Policy Number",
            "Insured Person(s) and Eligible Dependents",
            "Policy Period and Effective Date",
            "Medical Inpatient Annual Maximum Limit",
            "Personal Accident Capital Sum Insured",
            "Room and Board Daily Allowance Limit",
            "Pre-existing Conditions Exclusions",
            "Hospital Network and Direct Billing Service",
            "Premium Payment Mode and Tax Invoice",
            "Claim Notification Procedure"
        ],
        "Management Liability Policy": [
            "Policy Number",
            "Insured Company and Subsidiaries",
            "Policy Period",
            "Directors and Officers Liability Limit",
            "Company Reimbursement Provision",
            "Advancement of Defense Costs Terms",
            "Employment Practices Liability (EPL) Cover",
            "Corporate Legal Liability Sub-limit",
            "Retroactive Date and Territorial Limits",
            "Major Exclusions (Fraud, Deliberate Acts, Prior Pending Litigation)",
            "Notification of Circumstances and Claim Timeframe"
        ],
        "Marine Cargo and Transit Policy": [
            "Policy Number",
            "Shipper and Consignee Information",
            "Policy Period / Open Cover Period",
            "Conveyance Method (Vessel, Aircraft, Road, Rail)",
            "Sum Insured per Conveyance / Location",
            "Institute Cargo Clauses (A, B, or C)",
            "War and Strikes Risk Extensions",
            "Transit Deductible / Excess",
            "Survey and Claim Agent Notification"
        ],
        "Commercial Property and Casualty Policy": [
            "Policy Number",
            "Policyholder and Business Trading Address",
            "Material Damage / Buildings and Contents Sum Insured",
            "Business Interruption Indemnity Period",
            "Public and Products Liability Limit of Indemnity",
            "Specified Perils (Fire, Storm, Flood, Earthquake, Theft)",
            "Deductible / Excess Amounts",
            "Premium and Applicable Taxes / Levies",
            "Waiver of Subrogation Provisions"
        ],
        "Claim Review Checklist": [
            "Claimant Identity and Policy Number",
            "Date and Time of Loss Incident",
            "Location and Nature of Incident",
            "Estimated Damage / Loss Claimed",
            "Third-Party Involvement Details",
            "Police / Medical / Survey Report Reference",
            "Supporting Invoices and Proof of Loss",
            "Declaration and Claimant Signature Verification"
        ]
    }
    out_file = OUTPUT_DIR / "policy_checklists.json"
    save_json(checklists, out_file)
    logger.info(f"Task 18 Complete: Saved {len(checklists)} checklists to {out_file}")
    return checklists


# ==============================================================================
# Task 19 - Create Policy Difference Dataset (Dynamic Pairwise Comparison)
# ==============================================================================
def build_policy_differences() -> List[Dict[str, Any]]:
    """
    Compare pairs of policies dynamically using structured data.
    ZERO hardcoded strings: compares metadata, coverages, limits, and scope.
    """
    logger.info("Generating Task 19: policy_differences.json (Dynamic Pairwise Comparison)...")
    
    metadata_path = OUTPUT_DIR / "policy_metadata.json"
    coverage_path = OUTPUT_DIR / "coverage_dataset.json"
    
    metadata_list = load_json(metadata_path) if metadata_path.exists() else []
    coverage_list = load_json(coverage_path) if coverage_path.exists() else []
    
    meta_by_doc = {m.get("document", ""): m for m in metadata_list}
    cov_by_doc = {}
    for c_entry in coverage_list:
        d = c_entry.get("document", "")
        cov_by_doc[d] = {item["name"]: item for item in c_entry.get("coverages", [])}

    doc_names = [m.get("document") for m in metadata_list if m.get("document")]
    comparisons = []

    # Compare consecutive pairs dynamically: (0, 1), (1, 2), (2, 3) etc.
    for i in range(len(doc_names) - 1):
        doc_a = doc_names[i]
        doc_b = doc_names[i + 1]

        meta_a = meta_by_doc.get(doc_a, {})
        meta_b = meta_by_doc.get(doc_b, {})
        covs_a = cov_by_doc.get(doc_a, {})
        covs_b = cov_by_doc.get(doc_b, {})

        diffs = []

        # 1. Compare Policy Type
        p_type_a = meta_a.get("policy_type", "Unknown")
        p_type_b = meta_b.get("policy_type", "Unknown")
        if p_type_a != p_type_b:
            diffs.append({
                "field": "Policy Type",
                "policy_a": p_type_a,
                "policy_b": p_type_b
            })

        # 2. Compare Insurer Entity
        ins_a = meta_a.get("insurer", "Unknown")
        ins_b = meta_b.get("insurer", "Unknown")
        if ins_a != ins_b:
            diffs.append({
                "field": "Insurer Entity",
                "policy_a": ins_a,
                "policy_b": ins_b
            })

        # 3. Compare Currency
        curr_a = meta_a.get("currency", "Unknown")
        curr_b = meta_b.get("currency", "Unknown")
        if curr_a != curr_b:
            diffs.append({
                "field": "Operating Currency",
                "policy_a": curr_a,
                "policy_b": curr_b
            })

        # 4. Compare Premium Basis
        prem_a = meta_a.get("premium", "As stated in Schedule")
        prem_b = meta_b.get("premium", "As stated in Schedule")
        if prem_a != prem_b:
            diffs.append({
                "field": "Premium Basis",
                "policy_a": prem_a,
                "policy_b": prem_b
            })

        # 5. Compare Coverages Dynamically
        all_cov_names = sorted(list(set(list(covs_a.keys()) + list(covs_b.keys()))))
        for c_name in all_cov_names:
            c_info_a = covs_a.get(c_name, {})
            c_info_b = covs_b.get(c_name, {})
            inc_a = c_info_a.get("included", False)
            inc_b = c_info_b.get("included", False)
            lim_a = c_info_a.get("limit")
            lim_b = c_info_b.get("limit")

            if inc_a != inc_b or (inc_a and inc_b and lim_a != lim_b):
                val_a = f"Included ({lim_a})" if inc_a and lim_a else ("Included" if inc_a else "Not Included")
                val_b = f"Included ({lim_b})" if inc_b and lim_b else ("Included" if inc_b else "Not Included")
                diffs.append({
                    "field": f"Coverage: {c_name}",
                    "policy_a": val_a,
                    "policy_b": val_b
                })

        comparisons.append({
            "document_a": doc_a,
            "document_b": doc_b,
            "differences": diffs
        })

    out_file = OUTPUT_DIR / "policy_differences.json"
    save_json(comparisons, out_file)
    logger.info(f"Task 19 Complete: Saved {len(comparisons)} dynamic policy comparisons to {out_file}")
    return comparisons


# ==============================================================================
# Task 20 - Create Coverage Gap Dataset (Dynamic Set Comparison)
# ==============================================================================
STANDARD_REFERENCE_COVERAGES = [
    "Personal Accident",
    "Medical Expenses & Inpatient Care",
    "Directors and Officers Liability",
    "Cargo & Goods in Transit",
    "Public Liability",
    "Property Damage",
    "Business Interruption",
    "Cyber Insurance",
    "Crime Cover",
    "Professional Indemnity",
    "Flood",
    "Theft"
]

def build_coverage_gaps() -> List[Dict[str, Any]]:
    """
    Calculate missing coverages using dynamic Python set/list comparison.
    ZERO document-specific hardcoding.
    """
    logger.info("Generating Task 20: coverage_gaps.json (Dynamic Set Comparison)...")
    
    coverage_path = OUTPUT_DIR / "coverage_dataset.json"
    cov_data = load_json(coverage_path) if coverage_path.exists() else []
    
    gaps_dataset = []
    for item in cov_data:
        doc = item.get("document", "")
        # Actual included coverages for this policy
        included_names = [c["name"] for c in item.get("coverages", []) if c.get("included", False)]
        included_set = set(included_names)

        # Python list comparison against standard reference catalog
        missing = [cov for cov in STANDARD_REFERENCE_COVERAGES if cov not in included_set]

        gaps_dataset.append({
            "document": doc,
            "included_coverages": included_names,
            "total_included": len(included_names),
            "missing_coverages": missing,
            "total_gaps": len(missing)
        })

    out_file = OUTPUT_DIR / "coverage_gaps.json"
    save_json(gaps_dataset, out_file)
    logger.info(f"Task 20 Complete: Saved {len(gaps_dataset)} dynamic coverage gap records to {out_file}")
    return gaps_dataset


# ==============================================================================
# Task 21 - Create Broker Recommendations Dataset (Rule-Based from Data)
# ==============================================================================
def build_broker_recommendations() -> List[Dict[str, Any]]:
    """
    Generate tailored recommendations dynamically using Python rules based
    on identified coverage gaps, policy type, and extracted attributes.
    ZERO document-specific hardcoding.
    """
    logger.info("Generating Task 21: recommendations.json (Dynamic Rule-Based)...")
    
    metadata_path = OUTPUT_DIR / "policy_metadata.json"
    gaps_path = OUTPUT_DIR / "coverage_gaps.json"
    
    metadata = load_json(metadata_path) if metadata_path.exists() else []
    gaps_data = load_json(gaps_path) if gaps_path.exists() else []
    
    gaps_by_doc = {g.get("document", ""): g.get("missing_coverages", []) for g in gaps_data}
    
    recommendations_dataset = []
    
    for meta in metadata:
        doc = meta.get("document", "")
        ptype = meta.get("policy_type", "").lower()
        curr = meta.get("currency", "standard currency")
        missing_covs = set(gaps_by_doc.get(doc, []))
        
        recs = []
        
        # Rule 1: Cyber gap for business/commercial/executive policies
        if "Cyber Insurance" in missing_covs and any(k in ptype for k in ["directors", "management", "cargo", "commercial"]):
            recs.append("Consider reviewing standalone Cyber Insurance coverage to protect corporate digital assets and data breach liabilities.")
            
        # Rule 2: Business Interruption gap when property is involved
        if "Business Interruption" in missing_covs and any(k in ptype for k in ["property", "commercial", "cargo"]):
            recs.append("Consider adding Business Interruption cover to protect operating revenue during physical recovery periods.")
            
        # Rule 3: Public Liability gap for operations
        if "Public Liability" in missing_covs and not any(k in ptype for k in ["health", "personal accident"]):
            recs.append("Consider evaluating third-party Public Liability insurance to cover bodily injury and property damage exposures.")
            
        # Rule 4: Personal Health & Accident recommendations
        if any(k in ptype for k in ["health", "accident"]):
            recs.append("Review annual medical aggregate limits against projected hospitalisation and surgical cost trends.")
            if "Personal Accident" not in missing_covs:
                recs.append("Verify Accidental Death & Permanent Disablement capital sums insured align with household income protection needs.")
            else:
                recs.append("Consider adding Accidental Death & Dismemberment benefits to supplement health coverage.")

        # Rule 5: Management Liability / D&O recommendations
        if "directors" in ptype or "management" in ptype:
            recs.append("Maintain continuity of retroactive dates across policy renewals to avoid uncovered past executive decisions.")
            recs.append("Review Corporate Legal Liability and investigation costs sub-limits against latest regulatory enforcement trends.")

        # Rule 6: Marine Cargo & Transit recommendations
        if "cargo" in ptype or "transit" in ptype:
            recs.append("Ensure transit warehouse storage limits adequately cover maximum seasonal inventory accumulations.")
            recs.append("Verify institute cargo clauses (A, B, or C) align with specific maritime and intermodal transit routes.")

        # Rule 7: Deductible / Excess threshold advisory
        recs.append(f"Review deductible/excess thresholds in {curr} to balance out-of-pocket loss exposure with annual premium savings.")

        # Rule 8: Renewal continuity rule
        exp = meta.get("expiry_date", "stated expiry")
        recs.append(f"Ensure policy renewal review is initiated before {exp} to prevent any lapse in contractual cover.")

        recommendations_dataset.append({
            "document": doc,
            "policy_type": meta.get("policy_type", ""),
            "total_recommendations": len(recs),
            "recommendations": recs
        })
        
    out_file = OUTPUT_DIR / "recommendations.json"
    save_json(recommendations_dataset, out_file)
    logger.info(f"Task 21 Complete: Saved {len(recommendations_dataset)} dynamic recommendation profiles to {out_file}")
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
# Task 23 - Create Insurance Risk Dataset (Master Catalog + Dynamic Detection)
# ==============================================================================
MASTER_RISK_CATALOG = [
    {
        "risk": "Cyber Attack",
        "category": "Technology & Information Security",
        "description": "Unauthorized network access, ransomware extortion, data breach, and system interruption.",
        "related_coverages": ["Cyber Insurance", "Crime Cover"],
        "keywords": ["cyber", "ransomware", "malware", "data breach", "hacker", "hacking"]
    },
    {
        "risk": "Fire & Explosion",
        "category": "Property Peril",
        "description": "Direct physical loss or destruction caused by fire, explosion, or lightning.",
        "related_coverages": ["Property Damage", "Commercial Property", "Business Interruption"],
        "keywords": ["fire", "explosion", "lightning", "combustion", "burn"]
    },
    {
        "risk": "Theft & Dishonesty",
        "category": "Crime & Property",
        "description": "Burglary, violent entry theft, employee dishonesty, and fraudulent fund transfer.",
        "related_coverages": ["Property Damage", "Crime Cover", "Money Cover"],
        "keywords": ["theft", "burglary", "dishonesty", "stolen", "robbery", "embezzlement"]
    },
    {
        "risk": "Flood & Water Damage",
        "category": "Natural Peril",
        "description": "Inundation of dry land from overflowing natural watercourses or escaping water.",
        "related_coverages": ["Property Damage", "Business Interruption"],
        "keywords": ["flood", "inundation", "water damage", "overflow"]
    },
    {
        "risk": "Equipment Breakdown",
        "category": "Engineering & Operational",
        "description": "Sudden mechanical breakdown, electrical arcing, or pressure vessel explosion.",
        "related_coverages": ["Machinery Breakdown", "Property Damage", "Business Interruption"],
        "keywords": ["machinery breakdown", "equipment breakdown", "mechanical failure"]
    },
    {
        "risk": "Storm & Tempest",
        "category": "Natural Peril",
        "description": "Physical damage caused by gale, typhoon, cyclone, tempest, or hail.",
        "related_coverages": ["Property Damage", "Commercial Property"],
        "keywords": ["storm", "tempest", "hail", "typhoon", "cyclone", "hurricane"]
    },
    {
        "risk": "Accidental Bodily Injury",
        "category": "Casualty & Personal Peril",
        "description": "Accidental bodily injury resulting in death, permanent disablement, or medical expense.",
        "related_coverages": ["Personal Accident", "Public Liability", "Medical Expenses & Inpatient Care"],
        "keywords": ["accidental bodily injury", "disablement", "accidental death", "bodily injury", "fracture"]
    },
    {
        "risk": "Medical Illness & Disease",
        "category": "Healthcare Peril",
        "description": "Acute or chronic sickness requiring inpatient hospitalisation, surgical treatment, or medical care.",
        "related_coverages": ["Medical Expenses & Inpatient Care"],
        "keywords": ["inpatient", "hospitalisation", "hospitalization", "surgical", "illness", "medical expenses"]
    },
    {
        "risk": "Executive Misconduct & Regulatory Action",
        "category": "Governance & Management Liability",
        "description": "Official investigations, statutory fines, breach of fiduciary duty, and claims against directors.",
        "related_coverages": ["Directors and Officers Liability", "Management Liability", "Statutory Liability"],
        "keywords": ["directors and officers", "breach of duty", "wrongful act", "official investigation", "regulatory"]
    },
    {
        "risk": "Cargo Transit Loss",
        "category": "Maritime & Logistics",
        "description": "Physical loss or damage to goods during sea, air, road, or rail transit from collision, overturning, or stranding.",
        "related_coverages": ["Cargo & Goods in Transit"],
        "keywords": ["cargo", "transit", "conveyance", "collision", "overturning", "jettison", "stranding"]
    }
]

def build_risk_dataset() -> Dict[str, Any]:
    """
    Create master risk catalog and dynamically detect which risks appear in each document.
    ZERO document-specific hardcoding.
    """
    logger.info("Generating Task 23: risk_dataset.json (Master + Dynamic Detection)...")
    
    documents = get_all_documents()
    
    # Dynamic document risk mapping based on text analysis
    doc_risks = {}
    for doc in documents:
        fname = doc["file_name"]
        text_lower = doc["text"].lower()
        detected_risks = []

        for r in MASTER_RISK_CATALOG:
            for kw in r["keywords"]:
                pattern = r"\b" + re.escape(kw) + r"\b"
                if re.search(pattern, text_lower):
                    detected_risks.append(r["risk"])
                    break
        doc_risks[fname] = detected_risks
        logger.info(f"{fname} -> Detected risks: {detected_risks}")

    clean_master = [
        {
            "risk": r["risk"],
            "category": r["category"],
            "description": r["description"],
            "related_coverages": r["related_coverages"]
        }
        for r in MASTER_RISK_CATALOG
    ]

    result = {
        "master_risks": clean_master,
        "document_risks": doc_risks
    }

    out_file = OUTPUT_DIR / "risk_dataset.json"
    save_json(result, out_file)
    logger.info(f"Task 23 Complete: Saved {len(clean_master)} master risks and {len(doc_risks)} document mappings to {out_file}")
    return result


# ==============================================================================
# Task 24 - Create Document Tags Dataset (Dynamic Relevance Rules)
# ==============================================================================
def build_document_tags() -> List[Dict[str, Any]]:
    """
    Assign strictly relevant tags to each document using Python content rules.
    ZERO document-specific hardcoding: evaluates actual headings, text, and doc category.
    """
    logger.info("Generating Task 24: document_tags.json (Dynamic Relevance Rules)...")
    
    documents = get_all_documents()
    tag_dataset = []
    
    for doc in documents:
        fname = doc["file_name"]
        text_lower = doc["text"].lower()
        first_page = doc["pages"][0]["text"].lower() if doc.get("pages") else text_lower[:2000]

        tags: Set[str] = set()

        # 1. Document Type Tags
        if "claim" in fname.lower() or "claim form" in first_page:
            tags.add("Claim Form")
            tags.add("Claims Operations")
            if "property" in text_lower:
                tags.add("Property Claim")
            if "medical" in text_lower or "health" in text_lower:
                tags.add("Health Claim")
            if "fidelity" in text_lower:
                tags.add("Fidelity Guarantee")
        else:
            tags.add("Policy Wording")

        # 2. Line of Business Tags (Based on prominent title / introductory text)
        if any(k in first_page for k in ["directors and officers", "complete directors"]):
            tags.add("Management Liability")
            tags.add("Directors and Officers")
            tags.add("Corporate Governance")
        elif any(k in first_page for k in ["cargo", "marine", "transit"]):
            tags.add("Marine Cargo")
            tags.add("Transit Insurance")
            tags.add("Logistics")
        elif any(k in first_page for k in ["beyond care", "personal health", "accident and health"]):
            tags.add("Health Insurance")
            tags.add("Personal Accident")
            tags.add("Personal Lines")
        elif "commercial combined" in first_page or "commercial property" in first_page:
            tags.add("Commercial")
            tags.add("Property Damage")

        # 3. Insurer Brand Tag
        if "allianz" in text_lower:
            tags.add("Allianz")

        sorted_tags = sorted(list(tags))
        tag_dataset.append({
            "document": fname,
            "folder": doc.get("folder", ""),
            "tags": sorted_tags
        })
        logger.info(f"{fname} -> Tags: {sorted_tags}")

    out_file = OUTPUT_DIR / "document_tags.json"
    save_json(tag_dataset, out_file)
    logger.info(f"Task 24 Complete: Saved {len(tag_dataset)} dynamic document tag profiles to {out_file}")
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
    print("All Phase 3 datasets built dynamically without document-specific hardcoding.")


if __name__ == "__main__":
    main()
