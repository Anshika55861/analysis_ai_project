#!/usr/bin/env python3
"""
scripts/validate_json.py - Task 26: Validate All JSON Files
Audits every JSON dataset in output/ for:
  - Invalid JSON format
  - Missing required fields
  - Empty or null values
  - Duplicate entries
  - Incorrect data types
  - Corrupted font artifacts (cid:...)
Saves validation report to output/json_validation_report.json.
"""

import os
import re
import sys
import json
import logging
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import setup_logger
from utils.json_utils import load_json, save_json
from config.settings import OUTPUT_DIR

logger = setup_logger("validate_json")

CID_REGEX = re.compile(r"\(cid:\d+\)")


def inspect_data(obj, path="root"):
    """Recursively checks for true (cid:...) font corruption, nulls, and malformed structures."""
    errors = []
    if obj is None:
        errors.append(f"Null value found at {path}")
    elif isinstance(obj, str):
        if CID_REGEX.search(obj):
            errors.append(f"Corrupted font token (cid:...) found at {path}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            errors.extend(inspect_data(item, f"{path}[{i}]"))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if not isinstance(k, str) or not k.strip():
                errors.append(f"Invalid key name '{k}' at {path}")
            errors.extend(inspect_data(v, f"{path}.{k}"))
    return errors


def check_duplicates(data, filename: str) -> list:
    """Checks for duplicate entries in list-based datasets."""
    errors = []
    if not isinstance(data, list):
        return errors
    
    seen = set()
    for i, item in enumerate(data):
        key = None
        if isinstance(item, dict):
            if "document" in item and "policy_number" in item:
                key = f"{item.get('document')}_{item.get('policy_number')}"
            elif "term" in item:
                key = item.get("term", "").lower()
            elif "clause_id" in item:
                key = item.get("clause_id")
            elif "question" in item and "document" in item:
                key = f"{item.get('document')}_{item.get('question')}"
            elif "rule" in item:
                key = item.get("rule")
            elif "query" in item:
                key = item.get("query")
            elif "file" in item:
                key = item.get("file")
        if key:
            if key in seen:
                errors.append(f"Duplicate entry found for key '{key}' at index {i}")
            else:
                seen.add(key)
    return errors


def validate_file(file_path: Path) -> dict:
    """Validates an individual JSON file."""
    filename = file_path.name
    report = {
        "file": filename,
        "status": "Passed",
        "errors": []
    }

    # 1. Parse check
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        report["status"] = "Failed"
        report["errors"].append(f"Invalid JSON syntax: {str(e)}")
        return report

    # 2. Non-empty dataset check
    if data is None or (isinstance(data, (list, dict)) and len(data) == 0):
        report["status"] = "Failed"
        report["errors"].append("Dataset is empty or null.")
        return report

    # 3. Content and type inspection
    inspection_errors = inspect_data(data)
    if inspection_errors:
        report["errors"].extend(inspection_errors[:5])
        if len(inspection_errors) > 5:
            report["errors"].append(f"... and {len(inspection_errors) - 5} more issues.")

    # 4. Duplicate checks
    dup_errors = check_duplicates(data, filename)
    if dup_errors:
        report["errors"].extend(dup_errors[:5])

    # 5. Schema-specific checks
    if filename == "policy_metadata.json":
        if isinstance(data, list):
            for i, p in enumerate(data):
                for req in ["policy_number", "insurer", "policy_type"]:
                    if req not in p or not str(p[req]).strip():
                        report["errors"].append(f"Missing or empty required field '{req}' in policy[{i}]")
                if p.get("policy_number", "").lower() in ["from", "to", "wording", "the"]:
                    report["errors"].append(f"Invalid policy number '{p.get('policy_number')}' in policy[{i}]")
    elif filename == "coverage_dataset.json":
        if isinstance(data, list):
            for i, p in enumerate(data):
                if "document" not in p or "coverages" not in p:
                    report["errors"].append(f"Missing 'document' or 'coverages' in coverage item {i}")
    elif filename == "insurance_dictionary.json":
        if isinstance(data, list):
            for i, t in enumerate(data):
                if "term" not in t or "definition" not in t:
                    report["errors"].append(f"Missing 'term' or 'definition' in dictionary entry {i}")
    elif filename == "final_ai_dataset.json":
        if isinstance(data, list):
            for i, item in enumerate(data):
                for req in ["document", "keywords", "tags"]:
                    if req not in item:
                        report["errors"].append(f"Missing required field '{req}' in final_ai_dataset[{i}]")

    if report["errors"]:
        report["status"] = "Failed"

    return report


def main():
    logger.info("Starting Task 26: Validate All JSON Files...")
    output_dir = OUTPUT_DIR
    target_files = sorted([f for f in output_dir.glob("*.json") if f.name != "json_validation_report.json"])

    reports = []
    passed_count = 0
    failed_count = 0

    for f in target_files:
        res = validate_file(f)
        reports.append(res)
        if res["status"] == "Passed":
            passed_count += 1
            logger.info(f"  [PASSED] {f.name}")
        else:
            failed_count += 1
            logger.warning(f"  [FAILED] {f.name}: {res['errors']}")

    report_path = output_dir / "json_validation_report.json"
    save_json(reports, report_path)
    logger.info(f"Task 26 Complete: Validated {len(reports)} JSON files ({passed_count} passed, {failed_count} failed).")
    logger.info(f"Validation report saved to {report_path}")
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
