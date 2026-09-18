# 🛡️ Document Analysis AI – Phase 1, Phase 2 & Phase 3

**An Intelligent Insurance Document Processing and AI Preparation Pipeline**

This repository contains an end-to-end Python pipeline designed to extract, analyze, standardize, classify, chunk, index, and validate complex insurance policies and claim documents. The resulting structured datasets prepare insurance data for seamless integration with downstream enterprise AI systems:
- **Amazon Textract** (Multimodal layout and key-value extraction)
- **Amazon Bedrock** (LLM-based policy reasoning, prompt execution, and advisory generation)
- **OpenSearch** (Vector embeddings, keyword search, and semantic dense retrieval)
- **Policy Comparison Engine** (Side-by-side broker policy comparison & gap analysis)
- **AI Recommendation & Underwriting Engine** (Rules engine and automated broker advisory)

---

## 📂 Project Architecture & Directory Structure

```
analysis-ai/
│
├── dataset/
│   ├── policy/
│   │   ├── policy1.pdf      # Commercial Combined Policy
│   │   ├── policy2.pdf      # Management Liability Policy
│   │   ├── policy3.pdf      # Directors & Officers (D&O) Corporate Policy
│   │   └── policy4.pdf      # International Marine / Commercial Policy
│   └── claim/
│       ├── claim.pdf        # Fidelity Guarantee Insurance Proposal Form
│       ├── claim1.pdf       # Commercial Property Claim Form
│       └── claim2.pdf       # Medical & Casualty Claim Form
│
├── output/
│   # Phase 1 Outputs
│   ├── dataset.csv                  # Task 1: Document metadata & confidence scores
│   ├── sections.json                # Task 2: Extracted structural sections
│   ├── insurance_dictionary.json    # Task 3: Domain ontology & keyword dictionary (96 terms)
│   ├── clauses.json                 # Task 4: Extracted policy clauses (472 clauses)
│   ├── qa_dataset.json              # Task 5: Dynamic Q&A training pairs (89 QA pairs)
│
│   # Phase 2 Outputs
│   ├── policy_metadata.json         # Task 6: Structured policy information
│   ├── coverage_dataset.json        # Task 7: Coverage inclusions & limits dataset
│   ├── policy_comparison.json       # Task 8: Side-by-side policy comparison
│   ├── classified_clauses.json      # Task 9: Categorized clause library (1,127 clauses, 6 categories)
│   ├── entities.json                # Task 10: Named entities & monetary values (171 entities)
│   ├── document_chunks.json         # Task 11: Heading & page-aware semantic chunks (777 chunks)
│   ├── evaluation_dataset.json      # Task 12: Ground-truth AI test benchmark (16 Q&As)
│   ├── policy_summaries.json        # Task 13: Executive policy summaries
│   ├── term_mapping.json            # Task 14: Canonical ontology & synonym mappings (20 terms)
│   ├── validation_report.json       # Task 15: Automated data quality audit report (100% score)
│
│   # Phase 3 Outputs
│   ├── search_keywords.json         # Task 16: Document search keywords dataset
│   ├── coverage_lookup.json         # Task 17: Standardized coverage synonym lookup
│   ├── policy_checklists.json       # Task 18: Broker policy review checklists
│   ├── policy_differences.json      # Task 19: Pairwise policy structural differences
│   ├── coverage_gaps.json           # Task 20: Missing coverage gap analysis
│   ├── recommendations.json         # Task 21: Broker advisory recommendations
│   ├── ai_prompts.json              # Task 22: Reusable Bedrock / LLM prompt templates
│   ├── risk_dataset.json            # Task 23: Insurance risk catalog & coverage mappings
│   ├── document_tags.json           # Task 24: Multi-label document classification tags
│   └── final_ai_dataset.json        # Task 25: Master aggregated AI-ready dataset
│
├── scripts/
│   # Phase 1 Scripts
│   ├── create_dataset.py            # Task 1: Dataset creation & metadata extraction
│   ├── extract_sections.py          # Task 2: Document section parsing
│   ├── build_dictionary.py          # Task 3: Insurance dictionary builder
│   ├── search_dictionary.py         # Task 3: Interactive dictionary search CLI
│   ├── analyze_clauses.py           # Task 4: Multi-column clause extraction
│   ├── create_qa_dataset.py         # Task 5: spaCy NLP Q&A generator
│
│   # Phase 2 Scripts
│   ├── extract_metadata.py          # Task 6 & 7: Policy metadata & coverage extractor
│   ├── compare_policies.py          # Task 8: Dynamic policy comparison engine
│   ├── classify_clauses.py          # Task 9: 6-category clause classifier
│   ├── extract_entities.py          # Task 10: Named entity recognizer (NER)
│   ├── chunk_documents.py           # Task 11: Semantic document chunker
│   ├── validate_documents.py        # Task 15: Document & data quality validator
│
│   # Phase 3 Scripts
│   ├── generate_keywords.py         # Task 16: Search keywords generator
│   ├── build_phase3_datasets.py     # Tasks 17-24: Coverage lookup, checklists, gaps, risks, prompts
│   ├── build_final_dataset.py       # Task 25: Master unified AI dataset builder
│
│   # Verification
│   ├── verify_tasks.py              # Master end-to-end verification suite (Tasks 1-25)
│   └── README.md                    # Script documentation
│
├── config/                          # Centralized headings, patterns, and thresholds
├── utils/                           # Modular PDF readers, loggers, and JSON helpers
├── requirements.txt                 # Project dependencies
└── README.md                        # Master project documentation
```

---

## 🚀 Tasks Overview & Deliverables

### **Phase 1: Foundational Extraction**
- **Task 1 – Dataset Creation (`create_dataset.py` ➔ `output/dataset.csv`)**:
  Extracts document properties, policy names, insurance company names, effective dates, versions, and multi-method confidence scores (0.0 to 1.0).
- **Task 2 – Section Extraction (`extract_sections.py` ➔ `output/sections.json`)**:
  Identifies structural document sections (Definitions, Exclusions, Benefits, Conditions, Claims) with page spans and character offsets.
- **Task 3 – Insurance Dictionary (`build_dictionary.py` ➔ `output/insurance_dictionary.json`)**:
  Extracts industry terminology with contextual descriptions, search keywords, and an interactive query utility (`search_dictionary.py`).
- **Task 4 – Clause Analysis (`analyze_clauses.py` ➔ `output/clauses.json`)**:
  Extracts standalone policy clauses, detects clause titles, and performs fuzzy cross-document similarity matching.
- **Task 5 – Q&A Dataset (`create_qa_dataset.py` ➔ `output/qa_dataset.json`)**:
  Generates 89 domain-specific, verified Q&A pairs covering Definitions, Coverages, Exclusions, Limits, and Claims.

---

### **Phase 2: Structured AI Datasets**
- **Task 6 – Extract Policy Information (`extract_metadata.py` ➔ `output/policy_metadata.json`)**:
  Dynamically extracts policy number, insurer name, policyholder, effective/expiry dates, currency, and premium from raw text.
- **Task 7 – Create Coverage Dataset (`extract_metadata.py` ➔ `output/coverage_dataset.json`)**:
  Compiles a structured matrix of standard commercial insurance covers with boolean inclusion flags and indemnity limits.
- **Task 8 – Compare Two Insurance Policies (`compare_policies.py` ➔ `output/policy_comparison.json`)**:
  Provides a side-by-side comparison between policies across 16 fields.
- **Task 9 – Classify Insurance Clauses (`classify_clauses.py` ➔ `output/classified_clauses.json`)**:
  Classifies 1,127 clauses into 6 core categories (*Coverage, Exclusion, Definition, Condition, Extension, Limitation*).
- **Task 10 – Extract Entities (`extract_entities.py` ➔ `output/entities.json`)**:
  Extracts 171 named entities (Insurers, Limits, Policyholders, Regulatory Bodies, Dates, Channels) with contextual sentences.
- **Task 11 – Document Chunking (`chunk_documents.py` ➔ `output/document_chunks.json`)**:
  Generates 777 semantic chunks formatted for OpenSearch and Bedrock vector retrieval.
- **Task 12 – Create AI Test Questions (`output/evaluation_dataset.json`)**:
  Ground-truth QA dataset with 16 expert-curated evaluation questions and source citations.
- **Task 13 – Create Policy Summary (`output/policy_summaries.json`)**:
  Executive summaries for all documents with policy types, main coverages, and major exclusions.
- **Task 14 – Standardise Insurance Terms (`output/term_mapping.json`)**:
  Ontology mapping 20 canonical insurance concepts to industry synonyms.
- **Task 15 – Validate Insurance Documents (`validate_documents.py` ➔ `output/validation_report.json`)**:
  Audits documents for completeness, structural integrity, and date consistency (100% quality score).

---

### **Phase 3: Search, Gaps, Risks & AI Recommendations**
- **Task 16 – Search Keywords Dataset (`generate_keywords.py` ➔ `output/search_keywords.json`)**:
  Dynamically extracts high-relevance search keywords per document for OpenSearch indexing and keyword search.
- **Task 17 – Coverage Lookup Dataset (`build_phase3_datasets.py` ➔ `output/coverage_lookup.json`)**:
  Standardizes 29 coverage synonyms (e.g., *"General Liability" -> "Public Liability"*, *"D&O Cover" -> "Management Liability"*).
- **Task 18 – Policy Checklist Dataset (`build_phase3_datasets.py` ➔ `output/policy_checklists.json`)**:
  Broker policy review checklists for Commercial, Management Liability, Property & Casualty, and Claims.
- **Task 19 – Policy Difference Dataset (`build_phase3_datasets.py` ➔ `output/policy_differences.json`)**:
  Pairwise comparison dataset highlighting structural differences in limits, exclusions, and coverage inclusions.
- **Task 20 – Coverage Gap Dataset (`build_phase3_datasets.py` ➔ `output/coverage_gaps.json`)**:
  Identifies missing essential insurance covers per policy against comprehensive commercial benchmarks.
- **Task 21 – Broker Recommendations Dataset (`build_phase3_datasets.py` ➔ `output/recommendations.json`)**:
  Tailored advisory recommendations per document highlighting critical gaps and coverage enhancements.
- **Task 22 – AI Prompt Dataset (`build_phase3_datasets.py` ➔ `output/ai_prompts.json`)**:
  8 reusable prompt templates for Bedrock LLM tasks (Summary, Comparison, Extraction, Clause Classification, Risk Analysis, Gap Analysis).
- **Task 23 – Insurance Risk Dataset (`build_phase3_datasets.py` ➔ `output/risk_dataset.json`)**:
  Peril catalog (*Cyber Attack, Fire, Theft, Flood, Equipment Breakdown, Storm, Bodily Injury, Regulatory Investigation*) mapped to related coverages.
- **Task 24 – Document Tags Dataset (`build_phase3_datasets.py` ➔ `output/document_tags.json`)**:
  Multi-label classification tags (*Commercial, Retail, Management Liability, Claim Form, Casualty*) assigned to every document.
- **Task 25 – Final Unified AI Dataset (`build_final_dataset.py` ➔ `output/final_ai_dataset.json`)**:
  Aggregates all multi-phase outputs (metadata, coverages, clauses, summary, keywords, tags, risks, recommendations, questions) into one master AI-ready JSON dataset.

---

## ⚡ Quick Start & Verification

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### **2. Run All Pipeline Tasks & Master Verification**
```bash
python scripts/verify_tasks.py
```

### **Verification Suite Results (83/83 PASS - 100%)**
```text
===========================================================================
DOCUMENT ANALYSIS AI - COMPREHENSIVE VERIFICATION REPORT
===========================================================================
Task 1  - Dataset Creation (Metadata Extraction)       --> 4/4 checks passed
Task 2  - Section Extraction                           --> 3/3 checks passed
Task 3  - Insurance Dictionary (96 terms)              --> 3/3 checks passed
Task 4  - Clause Analysis (472 clauses)                --> 3/3 checks passed
Task 5  - Q&A Dataset (89 verified QA pairs)           --> 4/4 checks passed
Task 6  - Extract Policy Information (4 policies)      --> 4/4 checks passed
Task 7  - Create Coverage Dataset                      --> 3/3 checks passed
Task 8  - Compare Two Insurance Policies (16 fields)   --> 3/3 checks passed
Task 9  - Classify Insurance Clauses (1,127 clauses)   --> 4/4 checks passed
Task 10 - Extract Entities (171 entities)              --> 4/4 checks passed
Task 11 - Document Chunking (777 semantic chunks)      --> 4/4 checks passed
Task 12 - Create AI Test Questions (16 questions)      --> 3/3 checks passed
Task 13 - Create Policy Summary (5 summaries)          --> 3/3 checks passed
Task 14 - Standardise Insurance Terms (20 mappings)    --> 3/3 checks passed
Task 15 - Validate Insurance Documents (100% score)    --> 3/3 checks passed
Task 16 - Create Search Keywords Dataset (7 docs)      --> 4/4 checks passed
Task 17 - Build Coverage Lookup Dataset (29 mappings)  --> 3/3 checks passed
Task 18 - Build Policy Checklist Dataset (4 checklists)--> 3/3 checks passed
Task 19 - Create Policy Difference Dataset (3 pairs)   --> 3/3 checks passed
Task 20 - Create Coverage Gap Dataset (4 policies)     --> 3/3 checks passed
Task 21 - Create Broker Recommendations (4 policies)   --> 3/3 checks passed
Task 22 - Create AI Prompt Dataset (8 prompt templates)--> 3/3 checks passed
Task 23 - Create Insurance Risk Dataset (8 perils)     --> 3/3 checks passed
Task 24 - Create Document Tags (7 documents)           --> 3/3 checks passed
Task 25 - Generate Final AI Dataset (7 master profiles)--> 4/4 checks passed
===========================================================================
OVERALL: 83/83 checks passed (100%)
===========================================================================
```

---

## 🛡️ Data Quality & Cleanliness Guarantee
- **Zero Hardcoded Document Values**: Metadata, coverages, entities, and keywords are dynamically extracted from actual PDF text.
- **Zero Corrupted Font Artifacts**: All text across CSV and JSON outputs is cleansed of `(cid:...)` tokens and encoding errors.
- **Full Provenance & Citation**: All clauses, chunks, and Q&A pairs include document, section, and page citations.
