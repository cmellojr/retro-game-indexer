"""Load user configuration for pipeline calibration and model parameters."""

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


@dataclass
class WhisperConfig:
    """Whisper model parameters.

    Attributes:
        model_size: Model size ("tiny", "base", "small", "medium", "large").
        device: Device to run on ("cpu" or "cuda").
        compute_type: Quantization type ("int8", "float16", "float32").
    """

    model_size: str = "base"
    device: str = "cpu"
    compute_type: str = "int8"


@dataclass
class GlinerConfig:
    """GLiNER model parameters.

    Attributes:
        model_name: HuggingFace model identifier.
        device: Device to run on ("cpu" or "cuda").
    """

    model_name: str = "urchade/gliner_base"
    device: str = "cpu"


@dataclass
class AppConfig:
    """Top-level application configuration.

    Attributes:
        whisper: Whisper transcription model settings.
        gliner: GLiNER NER model settings.
        games: Games pipeline calibration overrides.
        maintenance: Maintenance pipeline calibration overrides.
    """

    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    gliner: GlinerConfig = field(default_factory=GlinerConfig)
    games: PipelineConfig = field(default_factory=PipelineConfig)
    maintenance: PipelineConfig = field(default_factory=PipelineConfig)


def load_config(path: Path | str = "config.toml") -> AppConfig:
    """Load application config from a TOML file.

    If the file does not exist, returns default config so the
    application behaves exactly as before.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        AppConfig with model and pipeline settings.
    """
    config = AppConfig()

    filepath = Path(path)
    if not filepath.is_file():
        return config

    with open(filepath, "rb") as f:
        raw = tomllib.load(f)

    # Model configs
    whisper_raw = raw.get("whisper", {})
    if whisper_raw:
        config.whisper = WhisperConfig(
            model_size=whisper_raw.get("model_size", "base"),
            device=whisper_raw.get("device", "cpu"),
            compute_type=whisper_raw.get("compute_type", "int8"),
        )

    gliner_raw = raw.get("gliner", {})
    if gliner_raw:
        config.gliner = GlinerConfig(
            model_name=gliner_raw.get("model_name", "urchade/gliner_base"),
            device=gliner_raw.get("device", "cpu"),
        )

    # Pipeline configs
    for name in ("games", "maintenance"):
        section = raw.get(name, {})
        if not section:
            continue

        threshold = section.get("threshold")
        blocklist = {t.lower() for t in section.get("blocklist", [])}
        aliases = {k.lower(): v for k, v in section.get("aliases", {}).items()}

        setattr(
            config,
            name,
            PipelineConfig(
                threshold=threshold,
                blocklist=blocklist,
                aliases=aliases,
            ),
        )

    return config
