"""Load JSON datasets from datasets/reference/ and datasets/community/."""

import json
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_REFERENCE_DIR = _PROJECT_ROOT / "datasets" / "reference"
_COMMUNITY_DIR = _PROJECT_ROOT / "datasets" / "community"


def _load_json(path: Path) -> list | dict:
    """Read a JSON file or return empty list if missing."""
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache
def load_dataset(pipeline: str, name: str) -> list | dict:
    """Load a JSON dataset, merging reference and community layers.

    Reference datasets (checked into git) are loaded first.
    Community datasets (user-editable, gitignored) are merged on top:
    - Lists: community items appended (deduplicated)
    - Dicts: community keys override reference keys

    Args:
        pipeline: Pipeline name ("games" or "maintenance").
        name: Dataset filename without extension
              ("known_titles", "stopwords", "consoles", "hints", "aliases").

    Returns:
        Merged dataset (list or dict), or empty list if missing.
    """
    ref_data = _load_json(_REFERENCE_DIR / pipeline / f"{name}.json")
    comm_data = _load_json(_COMMUNITY_DIR / pipeline / f"{name}.json")

    if not comm_data:
        return ref_data
    if isinstance(ref_data, list) and isinstance(comm_data, list):
        return list(dict.fromkeys(ref_data + comm_data))
    if isinstance(ref_data, dict) and isinstance(comm_data, dict):
        return {**ref_data, **comm_data}
    return comm_data if comm_data else ref_data
