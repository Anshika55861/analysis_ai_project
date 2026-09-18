"""
Task 1 - Create Insurance Document Dataset

Reads every PDF under the dataset folder and builds a structured CSV
containing key metadata and confidence scores for each document using
the multi-method metadata extractor.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from config.settings import DATASET_DIR, OUTPUT_DIR
from utils.logger import setup_logger
from utils.pdf_reader import read_pdf
from utils.metadata_extractor import extract_metadata

logger = setup_logger()


def main():
    logger.info("Starting Dataset Creation...")

    dataset = []

    for category_folder in sorted(DATASET_DIR.iterdir()):
        if not category_folder.is_dir():
            continue

        logger.info(f"Reading folder: {category_folder.name}")

        pdf_files = sorted(category_folder.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDFs found in {category_folder.name}")
            continue

        for pdf_file in pdf_files:
            document = read_pdf(pdf_file)

            if not document["success"]:
                logger.error(
                    f"Skipping {pdf_file.name} - could not be opened "
                    f"({document['error']})"
                )
                continue

            metadata = extract_metadata(document, category_folder.name)
            dataset.append(metadata)

    df = pd.DataFrame(dataset)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "dataset.csv"

    df.to_csv(output_file, index=False)
    logger.info(f"Dataset saved to {output_file}")

    print("\nDataset Preview\n")
    print(df[["File Name", "Policy Name", "Insurance Company Name", "Policy Name Confidence", "Insurance Company Name Confidence", "Policy Type"]])


if __name__ == "__main__":
    main()
