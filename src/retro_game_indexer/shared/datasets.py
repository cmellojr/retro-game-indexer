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

    Args:
        pipeline: Pipeline name (e.g. "games").
        name: Dataset filename without extension.

    Returns:
        Merged dataset (list or dict), or empty list if missing.
    """
    ref_path = _REFERENCE_DIR / pipeline / f"{name}.json"
    comm_path = _COMMUNITY_DIR / pipeline / f"{name}.json"
    ref_data = _load_json(ref_path)
    comm_data = _load_json(comm_path)

    if not comm_data:
        return ref_data
    if isinstance(ref_data, list) and isinstance(comm_data, list):
        return list(dict.fromkeys(ref_data + comm_data))
    if isinstance(ref_data, dict) and isinstance(comm_data, dict):
        return {**ref_data, **comm_data}
    return comm_data if comm_data else ref_data
