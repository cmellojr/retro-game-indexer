"""Load JSON datasets from data/datasets/."""

import json
from functools import lru_cache
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "datasets"


@lru_cache
def load_dataset(pipeline: str, name: str) -> list[str]:
    """Load a JSON dataset file.

    Reads a JSON array from ``data/datasets/{pipeline}/{name}.json``.
    Returns an empty list if the file does not exist, allowing the
    caller to fall back to inline defaults.

    Args:
        pipeline: Pipeline name ("games" or "maintenance").
        name: Dataset filename without extension
              ("known_titles", "stopwords", "consoles", "hints").

    Returns:
        List of strings from the JSON file, or empty list.
    """
    path = _DATA_DIR / pipeline / f"{name}.json"
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)
