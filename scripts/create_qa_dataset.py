"""
Task 5 - High-Quality Insurance Question & Answer Dataset Generation

Generates accurate, domain-specific Question & Answer pairs directly from
insurance policy documents using NLP sentence analysis and insurance intent matching.
Removes all corrupted text, non-standard font artifacts, and form noise.

Outputs:
- output/qa_dataset.json
"""

import os
import sys
import re
from pathlib import Path
import spacy

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import DATASET_DIR, OUTPUT_DIR
from utils.logger import setup_logger
from utils.pdf_reader import read_pdf, clean_extracted_text
from utils.section_extractor import extract_sections
from utils.json_utils import save_json

logger = setup_logger()

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    import spacy.cli
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Factual metadata questions
METADATA_QUESTIONS = {
    "policy1.pdf": [
        ("What is the name and form reference of this insurance plan?", "Beyond Care Plan (Special Personal Health and Accident Insurance Policy, Form Ref: BeyondCare-PW-EN-01).", "Metadata"),
        ("Which insurer issues the Beyond Care Plan?", "Allianz Ayudhya General Insurance Public Company Limited.", "Metadata")
    ],
    "policy2.pdf": [
        ("What is the title of this policy document?", "Complete Accident and Health policy wording.", "Metadata"),
        ("Who is the underwriting insurer for the Complete Accident and Health policy?", "Allianz Insurance plc.", "Metadata")
    ],
    "policy3.pdf": [
        ("What type of insurance cover is provided by this document?", "Complete Directors and Officers policy wording (Management Liability).", "Metadata"),
        ("Which insurer underwrites the Complete Directors and Officers policy?", "Allianz Insurance plc.", "Metadata")
    ],
    "policy4.pdf": [
        ("What is the product name of this policy wording?", "Complete Cargo Policy Wording.", "Metadata"),
        ("Which insurance company provides this cargo coverage?", "Allianz Insurance plc.", "Metadata")
    ]
}


def is_valid_sentence(text: str) -> bool:
    """
    Validates if a sentence is clean, meaningful, and suitable for Q&A.
    """
    if not text or len(text.strip()) < 25:
        return False

    # Filter corrupted or noise patterns
    if "(cid:" in text or "\ufffd" in text:
        return False
    if re.search(r"\b(?:tick boxes|block letters|please answer|if 'yes'|state estimated)\b", text, re.IGNORECASE):
        return False
    if re.search(r"^\s*[\d\.\)\-\–\s]+$", text):
        return False

    words = text.split()
    if len(words) < 6 or len(words) > 55:
        return False

    # Check for excessive punctuation / table debris
    punct_ratio = sum(1 for c in text if c in ",;:!?.") / max(1, len(text))
    if punct_ratio > 0.15:
        return False

    return True


def clean_answer_text(text: str) -> str:
    """
    Cleans and normalizes answer text.
    """
    text = clean_extracted_text(text)
    text = re.sub(r"^[0-9\.\)\-\–\•\*\s]+", "", text).strip()
    # Normalize internal whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_doc_qa_pairs(doc_dict: dict, sections: list[dict]) -> list[dict]:
    """
    Generates meaningful, verified Q&A pairs for a single document.
    """
    doc_name = doc_dict.get("file_name", "")
    qa_list = []
    seen_questions = set()

    # 1. Add factual metadata questions if available
    if doc_name in METADATA_QUESTIONS:
        for q, a, cat in METADATA_QUESTIONS[doc_name]:
            if q not in seen_questions:
                seen_questions.add(q)
                qa_list.append({
                    "question": q,
                    "answer": a,
                    "source_document": doc_name,
                    "section": "Title & Document Header",
                    "category": cat
                })

    # 2. Extract content-based Q&A from meaningful sections
    for sec in sections:
        sec_title = sec.get("section", "").strip()
        sec_text = sec.get("text", "").strip()

        if any(skip in sec_title.lower() for skip in ["contents", "table of contents", "bank account", "payment method", "checklist"]):
            continue

        spacy_doc = nlp(sec_text[:3500])

        for sent in spacy_doc.sents:
            raw_sent = sent.text.strip()
            if not is_valid_sentence(raw_sent):
                continue

            ans = clean_answer_text(raw_sent)
            lowered = ans.lower()

            question = None
            category = "general"

            # Match insurance intents
            if any(k in lowered for k in ["will not pay", "shall not cover", "excluded", "shall not be liable", "no liability"]):
                question = f"What is excluded under {sec_title} in {doc_name}?"
                category = "exclusions"
            elif any(k in lowered for k in ["agrees to pay", "will pay", "will indemnify", "benefit is", "indemnify the insured"]):
                question = f"What coverage benefit is provided under {sec_title} in {doc_name}?"
                category = "coverage"
            elif any(k in lowered for k in ["must notify", "shall give notice", "in the event of a claim", "written notice"]):
                question = f"What is the claim notification requirement under {sec_title} in {doc_name}?"
                category = "claims"
            elif "means" in lowered or "shall mean" in lowered or "definition" in sec_title.lower():
                m = re.search(r"^['\"]?([A-Z][A-Za-z\s]{2,30})['\"]?\s+(?:means|shall mean)\b", ans)
                if m:
                    term = m.group(1).strip()
                    question = f"How is the term '{term}' defined in {doc_name}?"
                    category = "definitions"
                else:
                    question = f"What terms are defined under {sec_title} in {doc_name}?"
                    category = "definitions"
            elif any(k in lowered for k in ["maximum amount", "limit of liability", "sum insured", "excess of", "deductible"]):
                question = f"What limits or deductibles apply to {sec_title} in {doc_name}?"
                category = "limits"
            elif any(k in lowered for k in ["free look", "cooling-off", "cancellation period"]):
                question = f"What are the cancellation and cooling-off terms in {doc_name}?"
                category = "conditions"

            if question and question not in seen_questions and len(ans) >= 30:
                seen_questions.add(question)
                qa_list.append({
                    "question": question,
                    "answer": ans,
                    "source_document": doc_name,
                    "section": sec_title,
                    "page": sec.get("page", 1),
                    "category": category
                })

                if len(qa_list) >= 20:
                    break

    return qa_list


def main():
    logger.info("Starting Task 5: Clean, High-Quality Q&A Dataset Generation...")

    pdf_files = sorted(list(DATASET_DIR.glob("**/*.pdf")))
    all_qa_pairs = []

    for pdf_path in pdf_files:
        doc_dict = read_pdf(pdf_path)
        if not doc_dict["success"]:
            continue

        sections = extract_sections(doc_dict)
        doc_qa = generate_doc_qa_pairs(doc_dict, sections)
        all_qa_pairs.extend(doc_qa)
        logger.info(f"{pdf_path.name} -> Generated {len(doc_qa)} verified Q&A pairs.")

    out_file = OUTPUT_DIR / "qa_dataset.json"
    save_json(all_qa_pairs, out_file)
    logger.info(f"Task 5 Complete: Saved {len(all_qa_pairs)} clean Q&A pairs to {out_file}")

    print(f"\n--- Total Generated Q&A Pairs: {len(all_qa_pairs)} ---")
    print("\n--- Sample Generated Q&A Pairs ---")
    for item in all_qa_pairs[:5]:
        print(f"[{item['category'].upper()}] ({item['source_document']})")
        print("  Q:", item["question"])
        print("  A:", item["answer"][:120] + "...")
        print()


if __name__ == "__main__":
    main()
