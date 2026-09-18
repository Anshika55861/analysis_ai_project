"""
Utility functions for JSON files.
"""

import json
from pathlib import Path


def save_json(data, output_path: Path) -> None:
    """
    Save Python object to JSON.
    """

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def load_json(input_path: Path):
    """
    Load JSON file.
    """

    with open(
        input_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)