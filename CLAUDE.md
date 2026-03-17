# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
pip install -e .                                                          # install in dev mode
retro-game-indexer analyze "https://youtube.com/watch?v=..."              # single video (games)
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p maintenance  # maintenance pipeline
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p all       # both pipelines
retro-game-indexer list "https://youtube.com/@Channel" -n 10              # list videos/lives
retro-game-indexer list "https://youtube.com/@Channel" -t live            # list only lives
retro-game-indexer channel "https://youtube.com/@Channel" -n 5            # analyze channel videos
retro-game-indexer search "Castlevania"                                   # search across all analyzed videos
retro-game-indexer history                                                # list analyzed videos
python -m retro_game_indexer analyze "URL"                                # run as module
```

## Architecture

Two detection pipelines with shared infrastructure:

**Shared pipeline:** download audio (cached) → transcribe (cached) → detect entities → validate against datasets → display results

Only `cli.py` orchestrates — no module imports another module. Each can be replaced independently.

### Shared modules (`shared/`)

| Module | Responsibility | External dep |
|---|---|---|
| `audio.py` | Download audio from YouTube | yt-dlp |
| `transcriber.py` | Speech-to-text with cached Whisper model | faster-whisper |
| `channel.py` | List videos from channel/playlist without downloading | yt-dlp |
| `config.py` | Load model settings and pipeline calibration from `config.toml` | tomllib (stdlib) |
| `cache.py` | Disk cache for audio files and transcription segments | — |
| `db.py` | SQLite persistence for video metadata and detection results | sqlite3 (stdlib) |
| `datasets.py` | Load JSON datasets from `data/datasets/` | json (stdlib) |

### Detection pipelines (`pipelines/`)

| Pipeline | Module | Responsibility | External dep |
|---|---|---|---|
| `base.py` | — | Detector and Validator protocol interfaces | — |
| `games/detector.py` | GameDetector | Zero-shot NER for game names | GLiNER |
| `games/validator.py` | GameValidator | Fuzzy match against known titles dataset | difflib (stdlib) |
| `games/hints.py` | — | Whisper hints for game titles (from JSON) | — |
| `games/filters.py` | — | Stopwords and console name filters (from JSON) | — |
| `maintenance/detector.py` | MaintenanceDetector | NER for tools, components, mods | GLiNER |
| `maintenance/validator.py` | MaintenanceValidator | Fuzzy match against known terms dataset | difflib (stdlib) |
| `maintenance/hints.py` | — | Whisper hints for maintenance terms (from JSON) | — |
| `maintenance/filters.py` | — | Stopwords for maintenance context (from JSON) | — |

### Orchestration

| Module | Responsibility | External dep |
|---|---|---|
| `cli.py` | Typer CLI with `list`, `analyze`, `channel`, `search` and `history` commands | typer |

Both `transcriber.py` and detector modules use a global `_get_model()` singleton to cache heavy ML models across calls.

All detectors follow the `Detector` protocol: `detect(segments) -> list[dict]` returning `{name, category, timestamp, confidence}`.

All validators follow the `Validator` protocol: `validate(candidates) -> list[dict]` adding `{validated}` key and normalizing names via fuzzy matching against JSON datasets in `data/datasets/`.

### Datasets (`data/datasets/`)

User-editable JSON files for stopwords, hints, console names, and known entities:
- `data/datasets/games/` — `known_titles.json`, `stopwords.json`, `consoles.json`, `hints.json`
- `data/datasets/maintenance/` — `known_terms.json`, `stopwords.json`, `hints.json`

Filters and hints modules load from JSON with inline fallback if files are missing.

### Configuration (`config.toml`)

User-editable TOML file at the project root.

**Model settings** — configurable for GPU/larger models:
- `[whisper]` — `model_size` (tiny/base/small/medium/large), `device` (cpu/cuda), `compute_type` (int8/float16/float32)
- `[gliner]` — `model_name` (HuggingFace ID), `device` (cpu/cuda)

**Pipeline calibration** — per-pipeline sections (`[games]`, `[maintenance]`):
- `threshold` — override confidence score (0.0-1.0)
- `blocklist` — terms to reject (false positives)
- `aliases` — map transcription variants to canonical names (e.g. `"Pico Stech" = "PicoStation"`)

## Conventions

- **Style guide**: Google Python Style Guide
- **Docstrings**: Google format with `Args:`, `Returns:`, `Raises:`
- **Type hints**: Python 3.12+ syntax (`list[dict]`, `str | None`)
- **Target**: Python >= 3.12, defaults to CPU with int8 quantization (GPU configurable via config.toml)
- **Linter**: ruff
- **Language context**: Videos in Brazilian Portuguese
