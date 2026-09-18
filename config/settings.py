"""
Project settings and common paths.
"""

from pathlib import Path

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Dataset Folder
DATASET_DIR = PROJECT_ROOT / "dataset"

# Output Folder
OUTPUT_DIR = PROJECT_ROOT / "output"

# Logs Folder
LOG_DIR = PROJECT_ROOT / "logs"

# Policy Folder
POLICY_DIR = DATASET_DIR / "policy"

# Claim Folder
CLAIM_DIR = DATASET_DIR / "claim"

# Quote Folder
QUOTE_DIR = DATASET_DIR / "quote"

# Schedule Folder
SCHEDULE_DIR = DATASET_DIR / "schedule"