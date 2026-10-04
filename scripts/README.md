# 📜 Scripts Documentation – Document Analysis AI

This folder contains the complete suite of modular Python scripts for **Phase 1**, **Phase 2**, and **Phase 3** of the Document Analysis AI pipeline.

---

## 🛠️ Script Reference

### Phase 1 Scripts:
1. `create_dataset.py` (Task 1): Extracts document page counts, policy names, insurance companies, and confidence scores into `output/dataset.csv`.
2. `extract_sections.py` (Task 2): Scans PDFs for headings and extracts section spans into `output/sections.json`.
3. `build_dictionary.py` (Task 3): Extracts insurance terms, definitions, and keywords into `output/insurance_dictionary.json`.
4. `search_dictionary.py` (Task 3): Interactive command-line utility to query the insurance dictionary.
5. `analyze_clauses.py` (Task 4): Unwraps multi-column lines, detects numbered clauses, and analyzes fuzzy similarity into `output/clauses.json`.
6. `create_qa_dataset.py` (Task 5): Extracts clean, verified Q&A pairs using spaCy NLP into `output/qa_dataset.json`.

---

### Phase 2 Scripts:

#### 1. `extract_metadata.py` (Tasks 6 & 7)
- **Purpose**: Extracts structured policy information (Policy Number, Policy Holder, Insurer, Broker, Policy Type, Start Date, Expiry Date, Premium, Currency) and coverage inclusion/exclusion details.
- **Outputs**:
  - `output/policy_metadata.json`
  - `output/coverage_dataset.json`
- **Run**:
  ```bash
  python scripts/extract_metadata.py
  ```

#### 2. `compare_policies.py` (Task 8)
- **Purpose**: Compares two insurance policies across coverage scope, policy limits, deductibles, premiums, exclusions, territorial limits, and add-ons.
- **CLI Arguments**:
  - `--policy_a`: First policy file name (default: `policy2.pdf`)
  - `--policy_b`: Second policy file name (default: `policy3.pdf`)
  - `--output`: Output file name (default: `policy_comparison.json`)
- **Output**:
  - `output/policy_comparison.json`
- **Run**:
  ```bash
  python scripts/compare_policies.py --policy_a policy2.pdf --policy_b policy3.pdf
  ```

#### 3. `classify_clauses.py` (Task 9)
- **Purpose**: Categorizes insurance clauses into 6 standard categories: `Coverage`, `Exclusion`, `Definition`, `Condition`, `Extension`, `Limitation`.
- **Output**:
  - `output/classified_clauses.json`
- **Run**:
  ```bash
  python scripts/classify_clauses.py
  ```

#### 4. `extract_entities.py` (Task 10)
- **Purpose**: Named entity recognition (NER) extracting Insurers, Brokers, Policyholders, Policy Numbers, Limits, Deductibles, Regulators, Dates, Addresses, and Contact Helplines.
- **Output**:
  - `output/entities.json`
- **Run**:
  ```bash
  python scripts/extract_entities.py
  ```

#### 5. `chunk_documents.py` (Task 11)
- **Purpose**: Splits policy documents into semantic chunks (~500–1000 characters with natural sentence boundary preservation and overlap) optimized for LLM embeddings, Amazon Bedrock, and OpenSearch.
- **Output**:
  - `output/document_chunks.json`
- **Run**:
  ```bash
  python scripts/chunk_documents.py
  ```

#### 6. `validate_documents.py` (Task 15)
- **Purpose**: Audits extracted data for completeness, missing fields (policy number, premium, dates), duplicate clauses, and coverage presence, outputting a data quality score.
- **Output**:
  - `output/validation_report.json`
- **Run**:
  ```bash
  python scripts/validate_documents.py
  ```

---

### Phase 3 Scripts:

#### 1. `generate_keywords.py` (Task 16)
- **Purpose**: Dynamically extracts high-relevance search keywords per document for OpenSearch keyword indexing and dense search.
- **Output**:
  - `output/search_keywords.json`
- **Run**:
  ```bash
  python scripts/generate_keywords.py
  ```

#### 2. `build_phase3_datasets.py` (Tasks 17 to 24)
- **Purpose**: Generates auxiliary and recommendation datasets:
  - **Task 17**: `output/coverage_lookup.json` (Coverage synonym lookup)
  - **Task 18**: `output/policy_checklists.json` (Broker review checklists)
  - **Task 19**: `output/policy_differences.json` (Pairwise policy differences)
  - **Task 20**: `output/coverage_gaps.json` (Missing coverage gap analysis)
  - **Task 21**: `output/recommendations.json` (Broker advisory recommendations)
  - **Task 22**: `output/ai_prompts.json` (Reusable Bedrock / LLM prompt templates)
  - **Task 23**: `output/risk_dataset.json` (Risk perils mapped to covers)
  - **Task 24**: `output/document_tags.json` (Document classification tags)
- **Run**:
  ```bash
  python scripts/build_phase3_datasets.py
  ```

#### 3. `build_final_dataset.py` (Task 25)
- **Purpose**: Aggregates all outputs across Phase 1, Phase 2, and Phase 3 into one comprehensive master AI JSON dataset.
- **Output**:
  - `output/final_ai_dataset.json`
- **Run**:
  ```bash
  python scripts/build_final_dataset.py
  ```

---

### Phase 4 Scripts:

#### 1. `validate_json.py` (Task 26)
- **Purpose**: Validates all JSON files in `output/` for format correctness, schema completeness, data types, and absence of corrupted `(cid:...)` tokens.
- **Output**: `output/json_validation_report.json`
- **Run**: `python scripts/validate_json.py`

#### 2. `find_duplicates.py` (Task 27)
- **Purpose**: Detects duplicate and shared data across documents (clauses, policy numbers, coverages, recommendations).
- **Output**: `output/duplicate_report.json`
- **Run**: `python scripts/find_duplicates.py`

#### 3. `create_search_tests.py` (Task 28)
- **Purpose**: Generates 36 realistic search queries with expected document matches for testing search engines.
- **Output**: `output/search_test_dataset.json`
- **Run**: `python scripts/create_search_tests.py`

#### 4. `create_ai_evaluations.py` (Task 29)
- **Purpose**: Ground-truth AI evaluation test cases across 5 tasks (Summary, Coverage, Clause Explanation, Comparison, Risk).
- **Output**: `output/ai_evaluation.json`
- **Run**: `python scripts/create_ai_evaluations.py`

#### 5. `create_rules.py` (Task 30)
- **Purpose**: Creates 16 business decision rules for underwriting, coverage gaps, limit adequacy, and renewals.
- **Output**: `output/rules_dataset.json`
- **Run**: `python scripts/create_rules.py`

#### 6. `build_knowledge_base.py` (Task 31)
- **Purpose**: Consolidates insurance terms, common clauses, risks, coverages, and recommendations into one central repository.
- **Output**: `output/insurance_knowledge_base.json`
- **Run**: `python scripts/build_knowledge_base.py`

#### 7. `create_test_scenarios.py` (Task 32)
- **Purpose**: Formulates 5 end-to-end business scenarios for testing the future AI system.
- **Output**: `output/ai_test_scenarios.json`
- **Run**: `python scripts/create_test_scenarios.py`

#### 8. `statistics.py` (Task 33)
- **Purpose**: Generates holistic project-wide dataset metrics (documents, pages, clauses, coverages, questions, risks).
- **Output**: `output/dataset_statistics.json`
- **Run**: `python scripts/statistics.py`

#### 9. `build_report.py` (Task 34)
- **Purpose**: Generates the final executive summary project report in Markdown.
- **Output**: `output/project_report.md`
- **Run**: `python scripts/build_report.py`

---

## 🧪 Master Verification Script

Run all Phase 1, Phase 2, Phase 3, and Phase 4 tasks end-to-end with 123 automated verification checks (100% pass rate):

```bash
python scripts/verify_tasks.py
```