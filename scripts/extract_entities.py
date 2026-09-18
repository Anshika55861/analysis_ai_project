"""
Task 10 - Extract Important Insurance Information (Named Entities)

Extracts domain-specific named entities and key values from insurance documents:
- Insurer Name
- Broker
- Policyholder / Insured Entity
- Policy Number / Form Code
- Premium & Rates
- Currency
- Addresses & Registered Offices
- Dates & Durations
- Coverage Limits
- Excess / Deductibles
- Regulatory & Statutory Authorities
- Contact Channels (Phone / Email)

Outputs:
- output/entities.json
"""

import os
import sys
import json
import re
from pathlib import Path
import pymupdf as fitz

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import OUTPUT_DIR, POLICY_DIR, CLAIM_DIR, DATASET_DIR
from utils.logger import setup_logger
from utils.json_utils import save_json
from utils.pdf_reader import clean_extracted_text

logger = setup_logger()

# Regex patterns for high-value entity extraction
ENTITY_PATTERNS = {
    "Policy Number": [
        (r"\b(BeyondCare-PW-EN-\d+|PW-EN-\d+|ALZ-[A-Z0-9\-]+|\d{2}_\d{3}[A-Z]+)\b", "Policy Number / Form Ref"),
        (r"(?:Policy\s*(?:No|Number|Reference|Ref)|BeyondCare)[\s:\.]*([A-Z0-9\-_/]{4,25})", "Policy Number")
    ],
    "Currency": [
        (r"\b(GBP|THB|HKD|USD|EUR|AUD)\b", "ISO Currency Code"),
        (r"(£|\$|€|฿)", "Currency Symbol")
    ],
    "Address": [
        (r"(\d+\s+Ploenchit\s+Tower[^\n\r]+Bangkok\s+\d{5})", "Insurer Headquarters"),
        (r"(\d+\s+Ladymead[^\n\r]+Surrey\s+[A-Z0-9\s]{6,8})", "Insurer Registered Office"),
        (r"(PO\s+Box\s+\d+[^\n\r]+Worthing\s+[A-Z0-9\s]{6,8})", "Insurer Servicing Office")
    ],
    "Regulatory Authority": [
        (r"(Prudential\s+Regulation\s+Authority)", "Statutory Regulator"),
        (r"(Financial\s+Conduct\s+Authority)", "Conduct Regulator"),
        (r"(Office\s+of\s+Insurance\s+Commission|OIC)", "Insurance Commission"),
        (r"(Insurance\s+Authority)", "Insurance Regulator")
    ],
    "Contact Channel": [
        (r"(0\d{3}\s+\d{3}\s+\d{4}|0208\s+\d{3}\s+\d{4})", "Telephone Helpline"),
        (r"([a-zA-Z0-9._%+-]+@allianz\.[a-z.]+)", "Official Email")
    ],
    "Coverage Limit": [
        (r"(?:limit\s+of|benefit\s+is|up\s+to|sum\s+insured\s+(?:of)?|maximum\s+(?:amount\s+payable\s+is)?)\s*(?:of\s+)?([£\$€฿]\s?[\d,]+(?:\s*(?:million|m))?)", "Coverage Limit"),
        (r"\b(THB\s*[\d,]+(?:\s*million)?)\b", "Coverage Limit (THB)"),
        (r"([£\$]\s?[\d,]+(?:,\d{3})*(?:\.\d{2})?)", "Monetary Amount")
    ],
    "Excess / Deductible": [
        (r"(?:excess|deductible)\s*(?:of|is|:)?\s*([£\$€฿]\s?[\d,]+)", "Excess / Deductible Amount")
    ],
    "Date / Period": [
        (r"(\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4})", "Calendar Date"),
        (r"(\b(?:12|24|36)\s+months\b|\b\d{1,2}\s+(?:days|consecutive\s+days)\b)", "Duration / Notice Period")
    ]
}

KNOWN_INSURERS = [
    ("Allianz Ayudhya General Insurance Public Company Limited", "Insurer"),
    ("Allianz Insurance plc", "Insurer"),
    ("AXA China Region Insurance Company (Hong Kong) Limited", "Insurer"),
    ("Allianz Legal Protection", "Underwriting Division"),
    ("Allianz Engineering Inspection Services Limited", "Subsidiary Insurer"),
    ("Pet Plan Limited", "Subsidiary Insurer")
]

KNOWN_BROKERS_ROLES = [
    ("Appointed Insurance Adviser / Broker", "Broker"),
    ("Authorized Insurance Broker", "Broker"),
    ("The Insured Person / Policyholder", "Policyholder"),
    ("Named Insured / Covered Person", "Policyholder"),
    ("Directors and Officers of the Company", "Insured Entity"),
    ("Proposer / Employer", "Proposer")
]


def extract_entities_from_document(pdf_path: Path) -> list[dict]:
    """
    Extracts all named entities, monetary limits, dates, addresses,
    and institutional actors from a given PDF document.
    """
    filename = pdf_path.name
    doc = fitz.open(pdf_path)
    entities = []
    seen_entities = set()

    def add_entity(name: str, ent_type: str, page_num: int, context: str):
        clean_name = clean_extracted_text(name)
        clean_name = re.sub(r"\s+", " ", clean_name).strip()
        if "(cid:" in clean_name or len(clean_name) <= 1:
            return
        if ent_type == "Coverage Limit" and re.match(r"^[£\$]\s*\d$", clean_name):
            return

        key = (clean_name.lower(), ent_type, filename)
        if key not in seen_entities:
            seen_entities.add(key)
            entities.append({
                "entity": clean_name,
                "type": ent_type,
                "document": filename,
                "page": page_num,
                "context": clean_extracted_text(context)[:150]
            })

    for page_idx, page in enumerate(doc):
        page_num = page_idx + 1
        page_text = clean_extracted_text(page.get_text("text") or "")

        for ins_name, ins_type in KNOWN_INSURERS:
            if ins_name.lower() in page_text.lower():
                add_entity(ins_name, ins_type, page_num, f"Insurer entity identified on page {page_num}")

        for role_name, role_type in KNOWN_BROKERS_ROLES:
            if role_name.split()[0].lower() in page_text.lower():
                add_entity(role_name, role_type, page_num, f"Role entity referenced on page {page_num}")

        for ent_type, patterns in ENTITY_PATTERNS.items():
            for pat, sub_type in patterns:
                for match in re.finditer(pat, page_text, re.IGNORECASE):
                    val = match.group(1) if match.groups() else match.group(0)
                    start = max(0, match.start() - 40)
                    end = min(len(page_text), match.end() + 40)
                    ctx = page_text[start:end]
                    add_entity(val, ent_type, page_num, ctx)

    return entities


def main():
    logger.info("Starting Task 10: Extract Important Insurance Information (Entities)...")

    pdf_files = sorted(list(DATASET_DIR.glob("**/*.pdf")))
    all_entities = []

    for pdf_path in pdf_files:
        logger.info(f"Extracting entities from {pdf_path.name}...")
        doc_entities = extract_entities_from_document(pdf_path)
        all_entities.extend(doc_entities)

    out_file = OUTPUT_DIR / "entities.json"
    save_json(all_entities, out_file)
    logger.info(f"Task 10 Complete: Saved {len(all_entities)} extracted entities to {out_file}")

    # Summary by type
    type_counts = {}
    for e in all_entities:
        t = e["type"]
        type_counts[t] = type_counts.get(t, 0) + 1

    print("\n--- Extracted Entities by Type (Task 10) ---")
    for t, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:25s}: {count:4d} entities")


if __name__ == "__main__":
    main()
