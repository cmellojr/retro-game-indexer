"""Load user configuration for pipeline calibration."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PipelineConfig:
    """Per-pipeline user overrides.

    Attributes:
        threshold: Minimum confidence score override, or None to keep default.
        blocklist: Extra terms to reject (added to built-in stopwords).
        aliases: Map variant spellings to a canonical name.
    """

    threshold: float | None = None
    blocklist: set[str] = field(default_factory=set)
    aliases: dict[str, str] = field(default_factory=dict)


def load_config(path: Path | str = "config.toml") -> dict[str, PipelineConfig]:
    """Load pipeline configs from a TOML file.

    If the file does not exist, returns default (empty) configs so the
    application behaves exactly as before.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        Dict mapping pipeline name ("games", "maintenance") to its config.
    """
    defaults = {
        "games": PipelineConfig(),
        "maintenance": PipelineConfig(),
    }

    filepath = Path(path)
    if not filepath.is_file():
        return defaults

    with open(filepath, "rb") as f:
        raw = tomllib.load(f)

    for name in ("games", "maintenance"):
        section = raw.get(name, {})
        if not section:
            continue

        threshold = section.get("threshold")
        blocklist = {t.lower() for t in section.get("blocklist", [])}
        aliases = {k.lower(): v for k, v in section.get("aliases", {}).items()}

        defaults[name] = PipelineConfig(
            threshold=threshold,
            blocklist=blocklist,
            aliases=aliases,
        )

    return defaults
