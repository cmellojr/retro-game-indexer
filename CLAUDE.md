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

**Shared pipeline:** download audio (cached) → transcribe (cached) → pass segments to detector(s) → display results

Only `cli.py` orchestrates — no module imports another module. Each can be replaced independently.

### Shared modules (`shared/`)

| Module | Responsibility | External dep |
|---|---|---|
| `audio.py` | Download audio from YouTube | yt-dlp |
| `transcriber.py` | Speech-to-text with cached Whisper model | faster-whisper |
| `channel.py` | List videos from channel/playlist without downloading | yt-dlp |
| `config.py` | Load user calibration from `config.toml` | tomllib (stdlib) |
| `cache.py` | Disk cache for audio files and transcription segments | — |
| `db.py` | SQLite persistence for video metadata and detection results | sqlite3 (stdlib) |

### Detection pipelines (`pipelines/`)

| Pipeline | Module | Responsibility | External dep |
|---|---|---|---|
| `base.py` | — | Detector protocol interface | — |
| `games/detector.py` | GameDetector | Zero-shot NER for game names | GLiNER |
| `games/hints.py` | — | Whisper hints for game titles | — |
| `games/filters.py` | — | Stopwords and console name filters | — |
| `maintenance/detector.py` | MaintenanceDetector | NER for tools, components, mods | GLiNER |
| `maintenance/hints.py` | — | Whisper hints for maintenance terms | — |
| `maintenance/filters.py` | — | Stopwords for maintenance context | — |

### Orchestration

| Module | Responsibility | External dep |
|---|---|---|
| `cli.py` | Typer CLI with `list`, `analyze`, `channel`, `search` and `history` commands | typer |

Both `transcriber.py` and detector modules use a global `_get_model()` singleton to cache heavy ML models across calls.

All detectors follow the `Detector` protocol: `detect(segments) -> list[dict]` returning `{name, category, timestamp, confidence}`.

### Calibration (`config.toml`)

User-editable TOML file at the project root. Per-pipeline sections:
- `threshold` — override confidence score (0.0-1.0)
- `blocklist` — terms to reject (false positives)
- `aliases` — map transcription variants to canonical names (e.g. `"Pico Stech" = "PicoStation"`)

## Conventions

- **Style guide**: Google Python Style Guide
- **Docstrings**: Google format with `Args:`, `Returns:`, `Raises:`
- **Type hints**: Python 3.12+ syntax (`list[dict]`, `str | None`)
- **Target**: Python >= 3.12, runs on CPU with int8 quantization (no GPU required)
- **Linter**: ruff
- **Language context**: Videos in Brazilian Portuguese
