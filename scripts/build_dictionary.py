"""
Task 3 - Build Insurance Dictionary

Automatically extracts insurance terms and their definitions from every
document section, combines them with foundational manually researched
insurance definitions, deduplicates case-insensitively, explicitly decouples
confusable terms (such as Liability vs Disability), tags term provenance
('source': 'manually_researched' vs 'source': 'extracted_from_document'),
and groups similar terms into canonical entries with aliases using RapidFuzz.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
from rapidfuzz import fuzz

from config.settings import OUTPUT_DIR
from config.patterns import DEFINITION_TRIGGERS
from utils.logger import setup_logger
from utils.section_extractor import extract_sections
from utils.pdf_reader import clean_extracted_text
from utils.json_utils import save_json, load_json
from scripts.extract_sections import load_documents

logger = setup_logger()

DICTIONARY_FILE = OUTPUT_DIR / "insurance_dictionary.json"

# Matches "Term means definition." / "Term shall mean definition." / "Term refers to definition."
DEFINITION_PATTERN = re.compile(
    r"(?P<term>[A-Z][A-Za-z /&\-]{2,40}?)\s+"
    r"(?:means|shall mean|refers to)\s+"
    r"(?P<definition>.+?)(?:\.\s|\.$|\n\n)",
    flags=re.DOTALL,
)

# Stop words and junk terms that should never be registered as dictionary terms
JUNK_TERMS = {
    "this", "any", "that", "these", "those", "if", "when", "where", "what", "who", "which",
    "alternative", "general rate", "per confinement", "employees", "pollutants",
    "self report", "funds extension", "if 'yes'", "in this regard", "third party, reconstitution costs",
    "any loss", "loss of", "premium in the", "for the purpose", "describe by what",
}

# Known antonym and opposing party pairs that must NEVER be grouped as synonyms/aliases
ANTONYM_PAIRS = {
    ("major", "minor"),
    ("minor", "major"),
    ("before", "after"),
    ("after", "before"),
    ("primary", "secondary"),
    ("secondary", "primary"),
    ("temporary", "permanent"),
    ("permanent", "temporary"),
    ("initial", "final"),
    ("final", "initial"),
    ("first", "second"),
    ("second", "first"),
    ("upper", "lower"),
    ("lower", "upper"),
    ("inpatient", "outpatient"),
    ("outpatient", "inpatient"),
    ("direct", "indirect"),
    ("indirect", "direct"),
    ("partial", "total"),
    ("total", "partial"),
    ("voluntary", "compulsory"),
    ("compulsory", "voluntary"),
    ("gross", "net"),
    ("net", "gross"),
    ("insured", "insurer"),
    ("insurer", "insured"),
    ("lessor", "lessee"),
    ("lessee", "lessor"),
}

# Explicitly forbidden grouping pairs to prevent semantic conflation
FORBIDDEN_GROUPS = {
    frozenset({"liability", "disability"}),
    frozenset({"insured", "insurer"}),
    frozenset({"lessor", "lessee"}),
    frozenset({"major", "minor"}),
    frozenset({"direct", "indirect"}),
    frozenset({"partial", "total"}),
}

# Foundational curated insurance terms with verified definitions
MANUALLY_RESEARCHED_TERMS = {
    "Premium": {
        "description": "The amount of money paid by the policyholder to the insurer to maintain active insurance coverage.",
        "keywords": ["premium", "payment", "cost", "fee", "insurance rate"],
        "source": "manually_researched",
    },
    "Policy": {
        "description": "A formal legal contract between the insurer and the policyholder setting out the terms, conditions, and coverage scope.",
        "keywords": ["policy", "contract", "agreement", "terms", "coverage"],
        "source": "manually_researched",
    },
    "Claim": {
        "description": "A formal request made by the insured or beneficiary to receive compensation or payment for an insured loss.",
        "keywords": ["claim", "compensation", "payout", "settlement", "loss"],
        "source": "manually_researched",
    },
    "Coverage": {
        "description": "The scope of protection and benefits provided to the insured under an insurance policy.",
        "keywords": ["coverage", "protection", "benefits", "policy", "scope"],
        "source": "manually_researched",
    },
    "Deductible": {
        "description": "The initial fixed amount or percentage of a covered loss that the insured must pay before the insurer covers the remainder.",
        "keywords": ["deductible", "excess", "out-of-pocket", "payment", "loss"],
        "source": "manually_researched",
    },
    "Insured": {
        "description": "The individual or entity named and protected against financial loss under the insurance policy.",
        "keywords": ["insured", "policyholder", "covered person", "client"],
        "source": "manually_researched",
    },
    "Beneficiary": {
        "description": "The person or entity designated to receive the benefits or proceeds from an insurance policy upon a covered event.",
        "keywords": ["beneficiary", "recipient", "proceeds", "claimant"],
        "source": "manually_researched",
    },
    "Liability": {
        "description": "Legal responsibility or financial obligation to compensate a third party for bodily injury, property damage, or financial loss.",
        "keywords": ["liability", "legal", "responsibility", "obligation", "third party"],
        "source": "manually_researched",
    },
    "Disability": {
        "description": "A physical or mental impairment that substantially limits a person's ability to perform routine activities or occupational duties.",
        "keywords": ["disability", "impairment", "incapacity", "accident", "injury"],
        "source": "manually_researched",
    },
    "Risk": {
        "description": "The uncertainty or probability of an adverse event or financial loss occurring.",
        "keywords": ["risk", "hazard", "peril", "uncertainty", "exposure"],
        "source": "manually_researched",
    },
    "Accident": {
        "description": "A sudden, unintended, and unforeseen event resulting in physical injury, property damage, or financial loss.",
        "keywords": ["accident", "unforeseen", "incident", "casualty", "injury"],
        "source": "manually_researched",
    },
    "Endorsement": {
        "description": "A written amendment or rider attached to an insurance policy that alters its coverage, terms, or conditions.",
        "keywords": ["endorsement", "amendment", "rider", "modification", "clause"],
        "source": "manually_researched",
    },
    "Exclusion": {
        "description": "A specific hazard, peril, or condition explicitly excluded from coverage under the insurance policy.",
        "keywords": ["exclusion", "not covered", "uncovered", "exception", "restriction"],
        "source": "manually_researched",
    },
    "Sum Insured": {
        "description": "The maximum monetary liability amount payable by the insurer under the insurance policy for a covered loss.",
        "keywords": ["sum insured", "coverage limit", "maximum benefit", "limit of liability"],
        "source": "manually_researched",
    },
    "Renewal": {
        "description": "The extension or continuation of an existing insurance policy beyond its initial expiry date.",
        "keywords": ["renewal", "extension", "continuation", "policy period"],
        "source": "manually_researched",
    },
    "Underwriting": {
        "description": "The process by which an insurer assesses the risk of an applicant to decide acceptance and determine premium pricing.",
        "keywords": ["underwriting", "risk assessment", "pricing", "acceptance"],
        "source": "manually_researched",
    },
    "Underwriter": {
        "description": "A specialized professional who assesses insurance risks and determines policy coverage terms and premiums.",
        "keywords": ["underwriter", "risk specialist", "assessor", "evaluator"],
        "source": "manually_researched",
    },
    "Co-payment": {
        "description": "A cost-sharing provision in an insurance policy where the insured pays a specified percentage of covered expenses.",
        "keywords": ["co-payment", "copayment", "cost-sharing", "coinsurance"],
        "source": "manually_researched",
    },
    "Waiting Period": {
        "description": "A specified period after policy inception during which certain benefits or illness claims cannot be made.",
        "keywords": ["waiting period", "qualifying period", "moratorium", "inception"],
        "source": "manually_researched",
    },
    "Grace Period": {
        "description": "A designated period of time after the premium due date during which coverage remains active without lapse.",
        "keywords": ["grace period", "late payment", "due date", "lapse protection"],
        "source": "manually_researched",
    },
    "Cashless Claim": {
        "description": "A claim settlement process where the insurer pays network hospitals or service providers directly on behalf of the insured.",
        "keywords": ["cashless claim", "direct billing", "network hospital", "settlement"],
        "source": "manually_researched",
    },
    "Reimbursement Claim": {
        "description": "A claim process where the insured pays medical or repair expenses upfront and later submits proof to the insurer for reimbursement.",
        "keywords": ["reimbursement claim", "pay and claim", "reimbursement", "out-of-pocket"],
        "source": "manually_researched",
    },
    "No Claim Bonus": {
        "description": "A discount or reward granted on renewal premiums to policyholders who make zero claims during the policy year.",
        "keywords": ["no claim bonus", "ncb", "discount", "renewal reward"],
        "source": "manually_researched",
    },
    "Third Party": {
        "description": "An individual or organization other than the policyholder (first party) and insurer (second party) involved in a claim.",
        "keywords": ["third party", "external party", "claimant", "liability"],
        "source": "manually_researched",
    },
    "Business Interruption": {
        "description": "Commercial insurance covering loss of income and fixed operating expenses following an insured disaster or disruption.",
        "keywords": ["business interruption", "consequential loss", "lost profits", "operations"],
        "source": "manually_researched",
    },
    "Cyber Insurance": {
        "description": "Specialized insurance protecting businesses against financial loss, liability, and remediation costs from cyberattacks or data breaches.",
        "keywords": ["cyber insurance", "cyber risk", "data breach", "ransomware", "hack"],
        "source": "manually_researched",
    },
    "Professional Indemnity": {
        "description": "Insurance protecting professionals and businesses against legal liability arising from negligence, errors, or omissions in services.",
        "keywords": ["professional indemnity", "errors and omissions", "malpractice", "negligence"],
        "source": "manually_researched",
    },
    "Public Liability": {
        "description": "Insurance covering legal liabilities for third-party bodily injury or property damage occurring during business operations.",
        "keywords": ["public liability", "third party liability", "bodily injury", "property damage"],
        "source": "manually_researched",
    },
    "Fire Cover": {
        "description": "Property insurance coverage protecting against destruction or damage caused by fire, lightning, or explosion.",
        "keywords": ["fire cover", "fire insurance", "conflagration", "property damage"],
        "source": "manually_researched",
    },
    "Flood Cover": {
        "description": "Insurance covering water damage and financial losses caused by overflowing rivers, heavy rainfall, or rising bodies of water.",
        "keywords": ["flood cover", "flood insurance", "water damage", "inundation"],
        "source": "manually_researched",
    },
    "Theft Cover": {
        "description": "Insurance covering loss of or damage to property resulting from burglary, robbery, or unauthorized forcible entry.",
        "keywords": ["theft cover", "burglary", "robbery", "stolen property"],
        "source": "manually_researched",
    },
    "Medical Expenses": {
        "description": "Costs and fees incurred for necessary medical treatments, hospitalization, doctor consultations, and prescribed medications.",
        "keywords": ["medical expenses", "treatment costs", "hospital bill", "healthcare"],
        "source": "manually_researched",
    },
    "Hospitalization": {
        "description": "Admission to an accredited hospital or healthcare institution as an inpatient for necessary medical treatment or surgery.",
        "keywords": ["hospitalization", "inpatient stay", "admission", "medical treatment"],
        "source": "manually_researched",
    },
    "Pre-existing Disease": {
        "description": "Any medical condition, ailment, or injury diagnosed or treated prior to the effective inception date of the insurance policy.",
        "keywords": ["pre-existing disease", "prior condition", "medical history", "ped"],
        "source": "manually_researched",
    },
    "Critical Illness": {
        "description": "A specified serious medical condition (such as cancer, heart attack, or stroke) that triggers a pre-agreed lump-sum benefit upon diagnosis.",
        "keywords": ["critical illness", "major disease", "dread disease", "lump sum benefit"],
        "source": "manually_researched",
    },
    "Maturity Benefit": {
        "description": "The amount payable to the policyholder upon surviving the full term of a life or endowment insurance policy.",
        "keywords": ["maturity benefit", "policy maturity", "endowment payout", "survival benefit"],
        "source": "manually_researched",
    },
    "Death Benefit": {
        "description": "The contractual amount paid to the designated nominee or beneficiary upon the death of the insured individual.",
        "keywords": ["death benefit", "life cover", "sum assured", "beneficiary payout"],
        "source": "manually_researched",
    },
    "Surrender Value": {
        "description": "The cash amount paid by the insurer to a policyholder who voluntarily terminates a life policy before its maturity.",
        "keywords": ["surrender value", "cash value", "policy termination", "early withdrawal"],
        "source": "manually_researched",
    },
    "Policyholder": {
        "description": "The person or entity that enters into an insurance agreement, owns the policy, and is responsible for premium payments.",
        "keywords": ["policyholder", "policy owner", "insured", "contract holder"],
        "source": "manually_researched",
    },
    "Nominee": {
        "description": "The person legally designated by the policyholder to receive claim proceeds in the event of the insured's demise.",
        "keywords": ["nominee", "beneficiary", "designee", "claimant"],
        "source": "manually_researched",
    },
    "Rider": {
        "description": "An optional supplementary insurance benefit or add-on attached to a base policy providing enhanced coverage.",
        "keywords": ["rider", "add-on", "supplementary benefit", "endorsement"],
        "source": "manually_researched",
    },
    "Loss Assessment": {
        "description": "The structured process of investigating, quantifying, and determining the extent of financial loss from an insured event.",
        "keywords": ["loss assessment", "damage evaluation", "claim assessment", "quantification"],
        "source": "manually_researched",
    },
    "Surveyor": {
        "description": "An independent licensed professional appointed to inspect, investigate, and assess the extent of insured property loss.",
        "keywords": ["surveyor", "loss adjuster", "claims assessor", "inspector"],
        "source": "manually_researched",
    },
    "Settlement": {
        "description": "The formal finalization and financial disbursement of an approved insurance claim by the insurer to the claimant.",
        "keywords": ["settlement", "payout", "claim resolution", "disbursement"],
        "source": "manually_researched",
    },
    "Fraud": {
        "description": "Intentional deception, misrepresentation, or dishonesty committed to obtain illegitimate payouts or advantages under a policy.",
        "keywords": ["fraud", "misrepresentation", "dishonesty", "false claim"],
        "source": "manually_researched",
    },
    "Natural Disaster": {
        "description": "A catastrophic environmental event such as an earthquake, hurricane, flood, or tsunami causing extensive property damage.",
        "keywords": ["natural disaster", "act of god", "catastrophe", "earthquake", "flood"],
        "source": "manually_researched",
    },
    "Property Damage": {
        "description": "Physical destruction, impairment, or loss of tangible real or personal property caused by a covered peril.",
        "keywords": ["property damage", "physical damage", "destruction", "material loss"],
        "source": "manually_researched",
    },
    "Personal Accident": {
        "description": "Insurance coverage offering financial benefits for accidental death, permanent disablement, or bodily injury.",
        "keywords": ["personal accident", "accidental death", "dismemberment", "injury"],
        "source": "manually_researched",
    },
    "Commercial Insurance": {
        "description": "Insurance coverage designed specifically for businesses to protect against operational risks, liabilities, and property damage.",
        "keywords": ["commercial insurance", "business insurance", "enterprise policy"],
        "source": "manually_researched",
    },
    "Travel Insurance": {
        "description": "Insurance designed to cover emergency medical expenses, trip cancellations, lost luggage, and travel disruptions.",
        "keywords": ["travel insurance", "trip cancellation", "medical emergency", "luggage loss"],
        "source": "manually_researched",
    },
    "Subrogation": {
        "description": "The legal right of an insurer to pursue a third party that caused an insurance loss to recover the amount paid to the insured.",
        "keywords": ["subrogation", "recovery", "third party", "recoupment"],
        "source": "manually_researched",
    },
    "Indemnity": {
        "description": "A contractual principle where the insurer compensates the insured to restore them to their financial position prior to the loss.",
        "keywords": ["indemnity", "compensation", "restoration", "reimbursement"],
        "source": "manually_researched",
    },
    "Co-insurance": {
        "description": "A joint assumption of risk between insurer and insured, or among multiple insurers, sharing losses proportionately.",
        "keywords": ["co-insurance", "coinsurance", "risk sharing", "proportional cover"],
        "source": "manually_researched",
    },
    "Peril": {
        "description": "A specific cause of loss or damage to property or persons, such as fire, flood, theft, or collision.",
        "keywords": ["peril", "cause of loss", "hazard", "risk factor"],
        "source": "manually_researched",
    },
    "Hazard": {
        "description": "A condition or circumstance that creates or increases the likelihood or severity of a loss from a peril.",
        "keywords": ["hazard", "danger", "risk factor", "exposure condition"],
        "source": "manually_researched",
    },
    "Actuary": {
        "description": "A mathematical and statistical professional who analyzes financial risks, probabilities, and insurance pricing.",
        "keywords": ["actuary", "actuarial", "risk modeling", "statistics"],
        "source": "manually_researched",
    },
    "Annuity": {
        "description": "A financial product providing regular periodic income payments over a specified period or the recipient's lifetime.",
        "keywords": ["annuity", "periodic payout", "pension", "retirement benefit"],
        "source": "manually_researched",
    },
    "Declaration Page": {
        "description": "The summary page of an insurance policy detailing the policyholder, covered property, limits, and policy period.",
        "keywords": ["declaration page", "dec page", "policy summary", "schedule"],
        "source": "manually_researched",
    },
    "Aggregate Limit": {
        "description": "The maximum cumulative dollar amount an insurer will pay for all covered claims occurring during the policy period.",
        "keywords": ["aggregate limit", "maximum payout", "annual limit", "cap"],
        "source": "manually_researched",
    },
    "Actual Cash Value": {
        "description": "The replacement cost of damaged property minus accumulated physical depreciation and obsolescence.",
        "keywords": ["actual cash value", "acv", "depreciated value", "valuation"],
        "source": "manually_researched",
    },
    "Replacement Cost": {
        "description": "The cost to repair or replace damaged or destroyed property with new materials of like kind and quality without depreciation.",
        "keywords": ["replacement cost", "new for old", "restoration cost", "valuation"],
        "source": "manually_researched",
    },
    "Moratorium": {
        "description": "A temporary suspension or restriction of new policy coverage or underwriting activity during emergency events.",
        "keywords": ["moratorium", "binding suspension", "temporary halt", "restriction"],
        "source": "manually_researched",
    },
    "Reinsurance": {
        "description": "Insurance purchased by an insurance company from another insurer to manage risk exposure and portfolio volatility.",
        "keywords": ["reinsurance", "treaty", "risk transfer", "capacity"],
        "source": "manually_researched",
    },
    "Arbitration": {
        "description": "A formal dispute resolution process where independent arbitrators resolve disagreements between insurer and insured outside court.",
        "keywords": ["arbitration", "dispute resolution", "adjudication", "mediation"],
        "source": "manually_researched",
    },
    "Salvage": {
        "description": "The residual damaged property taken over by an insurer after paying a total loss claim.",
        "keywords": ["salvage", "recovery", "scrap value", "residual property"],
        "source": "manually_researched",
    },
}


def clean_definition(text: str) -> str:
    """Clean and collapse whitespace and newlines inside a definition."""
    text = clean_extracted_text(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text.strip(" .;") + "." if text else ""


def build_keywords(term: str) -> list[str]:
    """Build a search keyword list: term (lowercase) plus individual words."""
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", term) if len(w) > 2]
    keywords = list(dict.fromkeys([term.lower()] + words))
    return keywords


def is_valid_term(term: str) -> bool:
    """Validate that candidate extracted term is a plausible domain term."""
    clean = term.strip().lower()
    if clean in JUNK_TERMS:
        return False
    if len(clean) < 3 or len(clean) > 35:
        return False
    # Reject terms containing suspicious punctuation
    if any(char in clean for char in ["'", '"', ',', ';', ':', '?', '!', '(', ')', '[', ']', '{', '}']):
        return False
    # Reject terms starting with stop words or pronouns
    words = clean.split()
    if words and words[0] in {"this", "any", "that", "these", "those", "if", "when", "where", "what", "who", "which", "per"}:
        return False
    return True


def are_antonyms(term_a: str, term_b: str) -> bool:
    """
    Check if two candidate terms differ by exactly one word that forms
    a known antonym or opposing legal party pair.
    """
    words_a = [w.lower() for w in re.findall(r"[A-Za-z]+", term_a)]
    words_b = [w.lower() for w in re.findall(r"[A-Za-z]+", term_b)]

    if len(words_a) != len(words_b):
        return False

    diffs = []
    for wa, wb in zip(words_a, words_b):
        if wa != wb:
            diffs.append((wa, wb))

    if len(diffs) == 1:
        if tuple(diffs[0]) in ANTONYM_PAIRS:
            return True

    return False


def extract_terms_from_text(text: str) -> dict[str, dict]:
    """
    Scan a block of text for 'Term means/shall mean/refers to definition' sentences.
    """
    terms = {}
    for match in DEFINITION_PATTERN.finditer(text):
        raw_term = match.group("term").strip()
        definition = clean_definition(match.group("definition"))

        if not is_valid_term(raw_term) or len(definition) < 15:
            continue

        term_clean = raw_term.strip(" ,;:-")
        # Format term nicely with title case
        term_clean = " ".join(w.capitalize() for w in term_clean.split())

        terms[term_clean] = {
            "description": definition,
            "keywords": build_keywords(term_clean),
            "source": "extracted_from_document",
        }

    return terms


def deduplicate_terms(raw_terms: dict[str, dict]) -> dict[str, dict]:
    """
    Deduplicate terms case-insensitively. Prefer manually researched definitions
    when available, otherwise retain the longer/more complete definition.
    """
    deduped = {}
    lower_map = {}

    for term, data in raw_terms.items():
        key = term.lower()
        if key in lower_map:
            existing_term = lower_map[key]
            existing_data = deduped[existing_term]

            # If existing is manually researched, prioritize its description & source
            if existing_data.get("source") == "manually_researched":
                for kw in data.get("keywords", []):
                    if kw not in existing_data["keywords"]:
                        existing_data["keywords"].append(kw)
            elif data.get("source") == "manually_researched":
                # Upgrade to manually researched
                del deduped[existing_term]
                deduped[term] = data
                lower_map[key] = term
            else:
                # Both are extracted; keep the longer description
                if len(data["description"]) > len(existing_data["description"]):
                    del deduped[existing_term]
                    deduped[term] = data
                    lower_map[key] = term
                else:
                    for kw in data.get("keywords", []):
                        if kw not in existing_data["keywords"]:
                            existing_data["keywords"].append(kw)
        else:
            deduped[term] = data
            lower_map[key] = term

    return deduped


def group_similar_terms(
    terms_dict: dict[str, dict],
    similarity_threshold: float = 84.0
) -> dict[str, dict]:
    """
    Group similar term names with RapidFuzz token_sort_ratio into canonical clusters
    with an 'aliases' list, respecting explicit forbidden pairs and antonym guards.
    """
    term_names = list(terms_dict.keys())
    grouped_dictionary = {}
    assigned_terms = set()

    for i, term_a in enumerate(term_names):
        if term_a in assigned_terms:
            continue

        cluster_aliases = []
        best_desc = terms_dict[term_a]["description"]
        best_source = terms_dict[term_a].get("source", "extracted_from_document")
        all_keywords = list(terms_dict[term_a].get("keywords", []))

        for j in range(i + 1, len(term_names)):
            term_b = term_names[j]
            if term_b in assigned_terms:
                continue

            # Explicit forbidden groups (e.g. Liability vs Disability)
            pair_set = frozenset({term_a.lower(), term_b.lower()})
            if pair_set in FORBIDDEN_GROUPS:
                continue

            # Antonym guard: Never group if terms differ by an antonym pair
            if are_antonyms(term_a, term_b):
                continue

            score = fuzz.token_sort_ratio(term_a.lower(), term_b.lower())
            if score >= similarity_threshold:
                cluster_aliases.append(term_b)
                assigned_terms.add(term_b)

                # If candidate is manually researched, prioritize it
                if terms_dict[term_b].get("source") == "manually_researched":
                    best_desc = terms_dict[term_b]["description"]
                    best_source = "manually_researched"
                elif best_source != "manually_researched" and len(terms_dict[term_b]["description"]) > len(best_desc):
                    best_desc = terms_dict[term_b]["description"]

                for kw in terms_dict[term_b].get("keywords", []):
                    if kw not in all_keywords:
                        all_keywords.append(kw)

        grouped_dictionary[term_a] = {
            "description": best_desc,
            "keywords": all_keywords,
            "aliases": cluster_aliases,
            "source": best_source,
        }
        assigned_terms.add(term_a)

    return grouped_dictionary


def main():
    logger.info("Starting Task 3 - Build Insurance Dictionary")

    # 1. Initialize with verified foundational terms (source: manually_researched)
    raw_collected_terms = {
        term: dict(details)
        for term, details in MANUALLY_RESEARCHED_TERMS.items()
    }

    # 2. Extract terms dynamically from all document sections (source: extracted_from_document)
    documents = load_documents()
    total_sections_scanned = 0
    extracted_terms_count = 0

    for document in documents:
        sections = extract_sections(document)

        for section in sections:
            total_sections_scanned += 1
            found_terms = extract_terms_from_text(section["text"])
            for term, details in found_terms.items():
                extracted_terms_count += 1
                key = term.lower()
                # Check if it exists in raw_collected
                existing_match = next((k for k in raw_collected_terms if k.lower() == key), None)
                if existing_match:
                    # If manually researched, keep description but enrich keywords
                    for kw in details.get("keywords", []):
                        if kw not in raw_collected_terms[existing_match]["keywords"]:
                            raw_collected_terms[existing_match]["keywords"].append(kw)
                else:
                    raw_collected_terms[term] = details

    # 3. Deduplicate case-insensitively
    deduped_terms = deduplicate_terms(raw_collected_terms)

    # 4. Group similar terms into canonical entries with aliases (decoupling Liability vs Disability)
    grouped_dictionary = group_similar_terms(deduped_terms, similarity_threshold=84.0)

    OUTPUT_DIR.mkdir(exist_ok=True)
    save_json(grouped_dictionary, DICTIONARY_FILE)

    grouped_with_aliases = {
        term: data["aliases"]
        for term, data in grouped_dictionary.items()
        if data.get("aliases")
    }

    manual_count = sum(1 for d in grouped_dictionary.values() if d.get("source") == "manually_researched")
    extracted_count = sum(1 for d in grouped_dictionary.values() if d.get("source") == "extracted_from_document")

    logger.info(
        f"Dictionary saved to {DICTIONARY_FILE} ({len(grouped_dictionary)} entries total: "
        f"{manual_count} manually researched, {extracted_count} extracted from documents)."
    )

    print("\nInsurance Dictionary Build Summary")
    print("-" * 55)
    print(f"Total sections scanned         : {total_sections_scanned}")
    print(f"Candidate extractions found    : {extracted_terms_count}")
    print(f"Total raw terms assembled      : {len(raw_collected_terms)}")
    print(f"Terms after dedup              : {len(deduped_terms)}")
    print(f"Final canonical entries        : {len(grouped_dictionary)}")
    print(f"  - Manually researched        : {manual_count}")
    print(f"  - Extracted from documents   : {extracted_count}")
    print(f"Entries with aliases           : {len(grouped_with_aliases)}")

    if grouped_with_aliases:
        print("\nSample grouped entries with aliases:")
        for term, aliases in list(grouped_with_aliases.items())[:6]:
            print(f"  - {term} -> aliases: {aliases}")


if __name__ == "__main__":
    main()
