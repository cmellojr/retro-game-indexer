# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Data lake architecture** — bronze/silver/gold medallion pattern
  - Bronze: immutable raw data (YouTube metadata + Whisper transcripts)
  - Silver: versioned AI outputs with full config snapshots per run
  - Gold: consolidated knowledge (latest confirmed entities per video)
- `shared/datalake.py` — pure JSON I/O for all data lake operations
- `rebuild` CLI command — reconstruct SQLite database entirely from data lake files
- **Two-layer dataset system** — `datasets/reference/` (git-tracked) + `datasets/community/` (user-editable, gitignored)
- Run ID system — `YYYYMMDD_HHMMSS_{pipeline}_{model_hash8}` for detection versioning
- `run_id TEXT` column in SQLite `runs` table
- `language TEXT` column in SQLite `videos` table
- Bronze fallback in transcript cache — reads from bronze first, then legacy `.cache/transcripts/`
- `vector/` directory placeholder for future RAG embeddings
- `CHANGELOG.md`
- `CONTRIBUTING.md` with branching strategy

### Changed

- Datasets moved from `data/datasets/` to `datasets/reference/`
- `datasets.py` now merges reference + community layers (lists: append + dedup; dicts: community overrides reference)
- SQLite role changed from source-of-truth to rebuildable index
- `.gitignore` updated for data lake directories and community datasets
- `CLAUDE.md` updated with data lake architecture documentation
- `docs/roadmap.md` reordered to reflect actual implementation sequence

## [0.2.0] — 2026-03-16

### Added

- **Validation layer** — post-detection fuzzy matching against known datasets
  - `games/validator.py` — normalize game names against `known_titles.json`
  - `maintenance/validator.py` — normalize terms against `known_terms.json`
  - `[?]` marker for unvalidated/uncertain entities in CLI output
- **Configurable ML models** with GPU support
  - Whisper: `model_size` (tiny/base/small/medium/large), `device` (cpu/cuda), `compute_type` (int8/float16/float32)
  - GLiNER: `model_name` (HuggingFace ID), `device` (cpu/cuda)
- **JSON datasets** — user-editable reference data extracted from code
  - Games: `known_titles.json`, `stopwords.json`, `consoles.json`, `hints.json`, `aliases.json`
  - Maintenance: `known_terms.json`, `stopwords.json`, `hints.json`, `aliases.json`
- `datasets.py` module — load JSON datasets with LRU cache
- `validated` column in SQLite detections table
- HuggingFace token support via `.env` file
- Visual game detection technologies documented in `docs/ai.md`
- `docs/roadmap.md` — project evolution plan

### Fixed

- **Case-sensitivity bug in alias lookup** — JSON keys now lowercased to match detector output (`name.lower()`)

### Changed

- Aliases moved from `config.toml` to JSON datasets (`aliases.json`); config.toml kept as quick-override layer

## [0.1.0] — 2026-03-14

### Added

- **Core detection pipeline** — download audio → transcribe → detect entities → display results
- `analyze` command — single video analysis with `-p games/maintenance/all`
- `channel` command — batch analyze N videos from a YouTube channel
- `list` command — browse channel videos/lives without analyzing
- `search` command — query detected entities across all analyzed videos
- `history` command — list previously analyzed videos
- **Games pipeline** — zero-shot NER for retro game titles via GLiNER
- **Maintenance pipeline** — NER for tools, components, and mods via GLiNER
- Whisper hints — domain-specific vocabulary for improved transcription accuracy
- Disk caching — audio files and transcription segments
- SQLite persistence — video metadata and detection results
- `config.toml` — per-pipeline calibration (threshold, blocklist, aliases)
- Timestamped YouTube links (`-l` / `--links` flag)
- Transcription progress bar
- CLI built with Typer
- Documentation: `docs/usage.md`, `docs/ai.md`, `docs/calibration.md`

[Unreleased]: https://github.com/cmellojr/retro-game-indexer/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/cmellojr/retro-game-indexer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/cmellojr/retro-game-indexer/releases/tag/v0.1.0
