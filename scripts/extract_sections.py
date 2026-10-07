"""
Task 2 - Section Extraction

Extract complete insurance sections from all PDF documents
and save them to sections.json using layout-aware heading detection.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path when running scripts directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DATASET_DIR, OUTPUT_DIR
from utils.logger import setup_logger
from utils.pdf_reader import read_pdf
from utils.section_extractor import extract_sections
from utils.json_utils import save_json

logger = setup_logger()


def load_documents():
    """
    Read every PDF from every dataset folder.

    Returns
    -------
    list
        List of document dictionaries.
    """
    documents = []

    for category in sorted(DATASET_DIR.iterdir()):
        if not category.is_dir():
            continue

        logger.info(f"Reading folder: {category.name}")

        pdf_files = sorted(category.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {category.name}")
            continue

        for pdf_file in pdf_files:
            logger.info(f"Reading {pdf_file.name}")
            try:
                document = read_pdf(pdf_file)
                document["category"] = category.name
                documents.append(document)
            except Exception as error:
                logger.error(f"Failed to read {pdf_file.name}: {error}")

    logger.info(f"Successfully loaded {len(documents)} documents.")
    return documents


def process_documents(documents):
    """
    Extract sections from every loaded document.

    Parameters
    ----------
    documents : list

    Returns
    -------
    dict
    """
    results = {}

    for document in documents:
        logger.info(f"Extracting sections from {document['file_name']}")
        sections = extract_sections(document)
        results[document["file_name"]] = sections

    return results


def print_summary(results):
    """
    Display extraction summary.
    """
    print("\n" + "=" * 60)
    print("SECTION EXTRACTION SUMMARY")
    print("=" * 60)

    total_sections = 0

    for filename, sections in results.items():
        print(f"\n{filename}")
        if not sections:
            print("  No sections found.")
            continue

        print(f"  Sections Extracted : {len(sections)}")
        for section in sections[:10]:
            method = section.get("detection_method", "keyword")
            print(
                f"   - [{method:7s}] {section['section'][:45]} "
                f"(Page {section['page']})"
            )
        if len(sections) > 10:
            print(f"   ... and {len(sections) - 10} more")

        total_sections += len(sections)

    print("\n" + "=" * 60)
    print(f"Documents Processed : {len(results)}")
    print(f"Sections Extracted  : {total_sections}")
    print("=" * 60)


def main():
    """
    Task 2 Entry Point.
    """
    logger.info("Starting Task 2 - Section Extraction")

    documents = load_documents()
    results = process_documents(documents)

    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "sections.json"

    save_json(results, output_file)
    logger.info(f"Results saved to {output_file}")

    print_summary(results)
    logger.info("Task 2 completed successfully.")


if __name__ == "__main__":
    main()