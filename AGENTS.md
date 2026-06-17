# AGENTS.md

Entrypoint for AI agents working on this repository. Read this first.

## Project Overview

retro-game-indexer detects retro video game mentions in YouTube videos and
lives. It downloads audio, transcribes it with Whisper, extracts game names
with GLiNER NER, validates them against known datasets, and persists results
to a data lake (bronze/silver/gold) plus SQLite.

## Build & Run

```bash
pip install -e .                                                          # dev install
retro-game-indexer analyze "https://youtube.com/watch?v=..."              # single video
retro-game-indexer list "https://youtube.com/@Channel" -n 10              # list videos/lives
retro-game-indexer list "https://youtube.com/@Channel" -t live            # list only lives
retro-game-indexer channel "https://youtube.com/@Channel" -n 5            # batch analyze
retro-game-indexer search "Castlevania"                                   # search entities
retro-game-indexer history                                                # list analyzed
retro-game-indexer rebuild                                                # rebuild SQLite
ruff check src/                                                           # lint
```

## Tech Stack

| Component | Technology | Notes |
|---|---|---|
| Runtime | Python >= 3.12 | Type hints with `list[X]`, `X \| None` |
| CLI | Typer | Commands: analyze, list, channel, search, history, rebuild |
| Audio | yt-dlp | YouTube audio download |
| Transcription | faster-whisper (base, INT8) | CPU default, CUDA optional |
| NER | GLiNER (gliner_base) | Zero-shot entity recognition |
| Database | SQLite (stdlib) | Videos, runs, detections tables |
| Data Lake | JSON files | Bronze/silver/gold medallion pattern |
| Linter | ruff | Google Python Style |

## Architecture

One detection pipeline with shared infrastructure and a data-first persistence
model.

**Flow:** download audio (cached) → transcribe (cached) → detect game names
→ validate against known titles → persist to data lake + SQLite →
display results.

Only `cli.py` orchestrates — no module imports another module. Each can be
replaced independently.

### Data Lake (`data/`)

Data lake is the source of truth. SQLite is a secondary index, rebuildable
via `retro-game-indexer rebuild`.

| Layer | Path | Contents | Mutability |
|---|---|---|---|
| **Bronze** | `data/bronze/{video_id}/` | Raw YouTube metadata + Whisper transcripts | Immutable (append-only) |
| **Silver** | `data/silver/{video_id}/` | Detection results + config snapshot per run | Versioned (one file per run_id) |
| **Gold** | `data/gold/{video_id}.json` | Consolidated confirmed entities | Overwritable (latest truth) |

Run IDs follow the format: `YYYYMMDD_HHMMSS_{pipeline}_{model_hash8}`.

### Shared Modules

| Module | Responsibility | External dep |
|---|---|---|
| `audio.py` | Download audio from YouTube | yt-dlp |
| `transcriber.py` | Speech-to-text with cached Whisper model | faster-whisper |
| `channel.py` | List videos from channel/playlist | yt-dlp |
| `config.py` | Load model settings from config.toml | tomllib (stdlib) |
| `cache.py` | Disk cache for audio and transcripts | — |
| `db.py` | SQLite index for video metadata and results | sqlite3 (stdlib) |
| `datasets.py` | Load JSON datasets (reference + community) | json (stdlib) |
| `datalake.py` | Read/write bronze, silver, gold layers | json (stdlib) |

### Detection Pipeline

| Module | Responsibility | External dep |
|---|---|---|
| `pipelines/base.py` | Detector and Validator protocol interfaces | — |
| `pipelines/games/detector.py` | GameDetector — zero-shot NER for game names | GLiNER |
| `pipelines/games/validator.py` | GameValidator — fuzzy match against known titles | difflib (stdlib) |
| `pipelines/games/hints.py` | Whisper hints for game titles (from JSON) | — |
| `pipelines/games/filters.py` | Stopwords and console name filters (from JSON) | — |

## Code Style

Follow the Google Python Style Guide
(https://google.github.io/styleguide/pyguide.html):

- **Line length:** 80 characters maximum
- **Indentation:** 4 spaces, no tabs
- **Naming:** `snake_case` for functions/variables, `CapWords` for classes,
  `UPPER_CASE` for constants, `_leading_underscore` for internal/private
- **Imports:** stdlib, third-party, local — each group separated by a blank
  line
- **Docstrings:** Google format with `Args:`, `Returns:`, `Raises:` sections.
  Required for every module, public class, and public function.
- **Type hints:** Python 3.12+ syntax (`list[dict]`, `str | None`,
  `X | Y`). Strongly encouraged on all function signatures.
- **Inline comments:** Do not add inline comments. Docstrings are the
  documentation mechanism. If code needs a comment to be understood, make the
  code itself clearer.
- **Linter:** `ruff check src/` — run before committing.

## Git Commits

- **Subject line:** ≤ 50 characters, capitalized, imperative mood, no trailing
  period. Example: `Add visual detection pipeline`
- **Body:** Blank line after subject, wrapped at 72 characters. Explain
  **what** and **why**, not **how**.
- **Branch naming:** Descriptive, kebab-case (`fix-login-timeout`,
  `feat-visual-detection`). Prefixes are optional.

## Debugging

- **Root cause first:** Investigate fully before proposing any fix. Reading
  errors, reproducing, checking recent changes, tracing data flow — all
  mandatory before code changes.
- **One fix at a time:** Each fix attempt is a single, isolated change. No
  "while I'm here" improvements during debugging.
- **Three-strike rule:** After three failed fix attempts, stop and question
  the approach. Escalate to the user.
- **Anti-rationalization:** Treat these as red flags:
  - "Should work now" — confidence is not evidence. Run the test.
  - "Already tested earlier" — code changed since then. Test again.
  - "Trivial change" — trivial changes break production. Verify.
  - "Quick fix for now, investigate later" — later never comes.
  - "I see the problem" — seeing symptoms is not root cause. Trace the data.
  - "It's probably X" — confirm before fixing.

## Quality

- **KISS:** Choose the simplest solution that fully solves the problem.
- **DRY:** Each piece of knowledge has a single, unambiguous representation.
- **SRP:** Functions, modules, and files have one reason to change.
- **Error handling:** Errors MUST always be logged. Never swallow silently.
- **Data trust boundary:** External data (user input, API responses, file
  contents) MUST be validated before use in business logic.
- **Schema changes:** Database schema modifications MUST be explicitly stated
  in any handoff or commit summary.

## Datasets

Two-layer system under `datasets/`:

- **`datasets/reference/games/`** — git-tracked, contains:
  `known_titles.json`, `stopwords.json`, `consoles.json`, `hints.json`,
  `aliases.json`
- **`datasets/community/games/`** — gitignored, overrides/extends reference
  datasets at load time

Lists are merged (appended + deduplicated). Dicts are merged (community keys
override reference keys).

## Configuration

User-editable `config.toml` at project root. All values are optional.

```toml
[whisper]
# model_size = "base"       # tiny, base, small, medium, large
# device = "cpu"            # cpu or cuda
# compute_type = "int8"     # int8, float16, float32

[gliner]
# model_name = "urchade/gliner_base"
# device = "cpu"

[games]
# threshold = 0.7           # confidence cutoff (0.0–1.0)
# blocklist = []            # terms to always reject
# [games.aliases]           # quick overrides for variant spellings
```
