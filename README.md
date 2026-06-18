# retro-game-indexer

Detect and index retro gaming content from YouTube videos using local
speech-to-text and zero-shot named entity recognition.

The current pipeline is audio-based: download audio, transcribe with Whisper,
detect game names with GLiNER, validate them against local datasets, then
persist results to a JSON data lake and SQLite.

## Current status

- Python 3.12+
- Version: `0.3.0`
- Default models: `faster-whisper` base with INT8, `urchade/gliner_base`
- Pipeline: `games` (games pipeline only)
- Persistence: bronze/silver/gold data lake plus rebuildable SQLite index
- Datasets: `datasets/reference/games/` with optional
  `datasets/community/games/` overrides

## Pipeline

- **games** — retro game titles mentioned in speech

## Stack

| Component | Technology | Purpose |
|---|---|---|
| CLI | Typer | Commands for analyze, list, channel, search, history, and rebuild |
| Audio | yt-dlp | Downloads YouTube audio |
| Transcription | faster-whisper | Converts audio to timestamped text segments |
| NER | GLiNER | Zero-shot entity detection |
| Data lake | JSON files | Bronze, silver, and gold layers under `data/` |
| Database | SQLite | Rebuildable secondary index under `.cache/` |

## Setup

```bash
git clone https://github.com/cmellojr/retro-game-indexer.git
cd retro-game-indexer
python -m venv .venv
.venv/bin/activate        # macOS/Linux
.venv\Scripts\activate    # Windows
pip install -e .
```

On first run, the ML models are downloaded and cached locally. Keep the default
CPU settings unless you have a CUDA-capable GPU.

Optionally create a `.env` file at the project root:

```text
HF_TOKEN=hf_xxxxx
```

The token is loaded automatically through `python-dotenv` and can reduce
HuggingFace rate limiting during model downloads.

## Usage

### Analyze a single video

```bash
retro-game-indexer analyze "https://youtube.com/watch?v=..."
retro-game-indexer analyze "https://youtube.com/watch?v=..." -l
retro-game-indexer analyze "https://youtube.com/watch?v=..." --no-cache
```

Output includes timestamp, name, category, confidence, and a `[?]` marker when
the entity was not validated against the known datasets.

### List videos from a channel

```bash
retro-game-indexer list "@RetroGameCorps" -n 20
retro-game-indexer list "@RetroGameCorps" -t live
retro-game-indexer list "@RetroGameCorps" -t regular
retro-game-indexer list "@RetroGameCorps" -s oldest
```

The `list` command only fetches video metadata. It does not download audio or
run detection.

Accepted inputs include channel names, handles, channel URLs, playlist URLs, and
live URLs.

### Analyze multiple videos

```bash
retro-game-indexer channel "@RetroGameCorps" -n 5
retro-game-indexer channel "@RetroGameCorps" -n 5 -l
```

The `channel` command lists matching videos, analyzes each one, persists the
results, then prints an aggregated report.

### Search and history

```bash
retro-game-indexer search "Castlevania"
retro-game-indexer history
```

`search` performs a case-insensitive partial match across analyzed videos.
`history` lists analyzed videos with run and detection counts.

### Rebuild SQLite from the data lake

```bash
retro-game-indexer rebuild
```

The data lake is the source of truth. SQLite is a secondary index and can be
recreated from bronze metadata and silver detection files at any time.

### Run as a Python module

```bash
python -m retro_game_indexer analyze "https://youtube.com/watch?v=..."
python -m retro_game_indexer list "@RetroGameCorps"
python -m retro_game_indexer search "Mario"
```

## Common options

| Flag | Default | Applies to | Description |
|---|---:|---|---|
| `-l, --links` | off | `analyze`, `channel` | Append timestamped YouTube links |
| `-n, --max-videos` | 10 / 5 | `list`, `channel` | Maximum number of videos |
| `-s, --sort` | `newest` | `list`, `channel` | `newest` or `oldest` |
| `-t, --type` | `all` | `list`, `channel` | `regular`, `live`, or `all` |
| `--hint` | auto | `analyze`, `channel` | Custom Whisper hint |
| `--config` | `config.toml` | most commands | Configuration file path |
| `--no-cache` | off | `analyze`, `channel` | Reprocess audio and transcription |

The `-p, --pipeline` flag defaults to `games` and has no other value.

## Data lake

The JSON data lake lives under `data/` and follows a medallion pattern.

| Layer | Path | Contents | Mutability |
|---|---|---|---|
| Bronze | `data/bronze/{video_id}/` | Raw YouTube metadata and Whisper transcripts | Append-only |
| Silver | `data/silver/{video_id}/` | Detection results and config snapshot per run | Versioned |
| Gold | `data/gold/{video_id}.json` | Latest confirmed entities per pipeline | Overwritten |

Run IDs use this format:

```text
YYYYMMDD_HHMMSS_{pipeline}_{model_hash8}
```

Silver files include the threshold, blocklist, aliases, hint, GLiNER model, and
Whisper model used for that run. Gold files store only validated entities and
reference the source silver run IDs.

## Datasets

Datasets are loaded from two layers:

| Layer | Path | Purpose |
|---|---|---|
| Reference | `datasets/reference/games/` | Git-tracked default datasets |
| Community | `datasets/community/games/` | User-editable overrides, gitignored |

Merging rules:

- Lists are appended and deduplicated.
- Dict keys from community override reference keys.

| File | Purpose |
|---|---|
| `known_titles.json` | Known game titles for validation |
| `stopwords.json` | Words to always reject |
| `consoles.json` | Console names to filter out |
| `hints.json` | Whisper transcription hints |
| `aliases.json` | Variant spelling normalization |

Prefer stable dataset entries in JSON. Use `config.toml` only for temporary
calibration overrides while reviewing results.

## Validation

After GLiNER detects entities, each candidate is normalized and validated:

1. Stopwords, console names, and blocklist terms are rejected.
2. Aliases map transcription variants to canonical names.
3. Exact dataset matches are confirmed.
4. Fuzzy matches at 80% similarity or higher are confirmed with adjusted score.
5. Unknown entities are kept but marked with `[?]`.

Validated entities are written to gold. Unvalidated entities remain visible in
silver and CLI output so they can be reviewed and added to datasets if needed.

## Configuration

Edit `config.toml` to configure models and calibrate detection.

```toml
[whisper]
model_size = "base"          # tiny, base, small, medium, large
device = "cpu"               # cpu or cuda
compute_type = "int8"        # int8, float16, float32

[gliner]
model_name = "urchade/gliner_base"
device = "cpu"               # cpu or cuda

[games]
threshold = 0.8
blocklist = ["React", "Big Brother"]

[games.aliases]
"Pico Stech" = "PicoStation"
```

Pipeline thresholds are detection cutoffs before validation. Blocklists are
case-insensitive and are applied after model inference. Aliases are applied
before deduplication and validation.

## Caching

Audio and transcripts are cached automatically.

```text
.cache/
  audio/{video_id}.{extension}
  transcripts/{video_id}_{hint_hash}.json
  retro_game_indexer.db
```

Transcript cache keys include the Whisper hint, so different pipelines or custom
hints keep separate transcript entries. The bronze layer is checked before the
legacy transcript cache.

Detection is not cached. This allows fast calibration loops: after the first
run, editing `config.toml` and re-running analysis reuses audio and transcripts
while recalculating detections.

Use `--no-cache` only when you need to force a full re-download and
re-transcription.

## Development

```bash
ruff check src/
python -m retro_game_indexer analyze "https://youtube.com/watch?v=..."
retro-game-indexer rebuild
```

The project uses Python 3.12 type hints and Google Python style. Public modules,
classes, and functions should include docstrings.

## Documentation

- [docs/usage.md](docs/usage.md) — full usage guide with examples
- [docs/calibration.md](docs/calibration.md) — threshold, blocklist, and alias
  tuning guide
- [docs/ai.md](docs/ai.md) — Whisper, GLiNER, and future visual detection notes
- [docs/roadmap.md](docs/roadmap.md) — implementation roadmap
- [CHANGELOG.md](CHANGELOG.md) — release notes
