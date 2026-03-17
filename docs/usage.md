# Usage Guide

## Installation

```bash
git clone https://github.com/cmellojr/retro-game-indexer.git
cd retro-game-indexer
pip install -e .
```

On first run, the tool downloads two ML models (~500 MB total):
- **faster-whisper** (base) — speech-to-text
- **GLiNER** (gliner_base) — named entity recognition

Subsequent runs reuse the cached models.

---

## Quick Start

Analyze a YouTube video for retro game mentions:

```bash
retro-game-indexer analyze "https://www.youtube.com/watch?v=abc123"
```

Output:

```
  Downloading audio...
  Transcribing... [████████████████████████████████] 100.0%
  Detecting (games)...
  Validating (games)...

[GAMES] 5 items found:

  12.3s  Super Mario World  [video game]  score=0.92
  45.7s  Castlevania  [video game]  score=0.88
  78.1s  Mega Man X  [video game]  score=0.85
  102.5s  Chrono Trigger  [video game]  score=0.79
  130.0s  Retroarch  [video game]  score=0.71 [?]
```

The `[?]` marker means the entity was not found in the known titles dataset — it may be a valid detection or a false positive.

---

## Commands

### `analyze` — Analyze a single video

```bash
# Default: detect video games
retro-game-indexer analyze "https://youtube.com/watch?v=..."

# Detect maintenance items (tools, components, mods)
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p maintenance

# Run both pipelines at once
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p all

# Show timestamped YouTube links (click to jump to the moment)
retro-game-indexer analyze "https://youtube.com/watch?v=..." -l

# Force reprocess (ignore cache)
retro-game-indexer analyze "https://youtube.com/watch?v=..." --no-cache
```

| Flag | Default | Description |
|------|---------|-------------|
| `-p, --pipeline` | games | `games`, `maintenance`, or `all` |
| `-l, --links` | off | Append timestamped YouTube links |
| `--hint` | (auto) | Custom Whisper transcription hint |
| `--config` | config.toml | Path to configuration file |
| `--no-cache` | off | Skip cache and reprocess from scratch |

---

### `list` — List videos from a channel

Lists videos without downloading or analyzing anything.

```bash
# Latest 10 videos and lives
retro-game-indexer list "@RetroGameCorps"

# Only live streams
retro-game-indexer list "@RetroGameCorps" -t live

# Only regular uploads
retro-game-indexer list "@RetroGameCorps" -t regular

# 20 oldest videos
retro-game-indexer list "@RetroGameCorps" -n 20 -s oldest
```

| Flag | Default | Description |
|------|---------|-------------|
| `-n, --max-videos` | 10 | Number of videos to list |
| `-s, --sort` | newest | `newest` or `oldest` |
| `-t, --type` | all | `regular`, `live`, or `all` |

**Accepted input formats** (all commands):

```
RetroGameCorps                                    # plain name
@RetroGameCorps                                   # handle
https://www.youtube.com/@RetroGameCorps           # full URL
https://www.youtube.com/playlist?list=PLxxxxx     # playlist URL
https://www.youtube.com/live/HKL7n9jKKNo         # live URL
```

---

### `channel` — Analyze multiple videos from a channel

Batch-analyzes N videos from a channel, then shows an aggregated report.

```bash
# Analyze 3 latest videos for games
retro-game-indexer channel "@RetroGameCorps" -n 3

# Analyze 5 latest lives for maintenance items
retro-game-indexer channel "@RetroGameCorps" -n 5 -t live -p maintenance

# Analyze 10 videos with timestamped links
retro-game-indexer channel "@RetroGameCorps" -n 10 -l
```

| Flag | Default | Description |
|------|---------|-------------|
| `-n, --max-videos` | 5 | Number of videos to analyze |
| `-s, --sort` | newest | `newest` or `oldest` |
| `-t, --type` | all | `regular`, `live`, or `all` |
| `-p, --pipeline` | games | `games`, `maintenance`, or `all` |
| `-l, --links` | off | Append timestamped YouTube links |
| `--hint` | (auto) | Custom Whisper transcription hint |
| `--config` | config.toml | Path to configuration file |
| `--no-cache` | off | Skip cache and reprocess from scratch |

---

### `search` — Search across all analyzed videos

Query the database for a game or term detected in previous analyses.

```bash
# Find all videos that mention Castlevania
retro-game-indexer search "Castlevania"

# Search for a maintenance term
retro-game-indexer search "capacitor"

# Partial match works (case-insensitive)
retro-game-indexer search "mario"
```

Example output:

```
3 results for "Castlevania":

  --- Retro Games Review Episode 12 ---
    45.7s  Castlevania  [video game]  score=0.88
    89.2s  Super Castlevania IV  [video game]  score=0.82
  --- SNES Hidden Gems ---
    120.3s  Castlevania: Bloodlines  [video game]  score=0.76
```

---

### `history` — List all analyzed videos

Shows all previously analyzed videos with run counts and detection totals.

```bash
retro-game-indexer history
```

Example output:

```
3 videos analyzed:

  [2024-11-15] Retro Games Review Episode 12  (1:23:45) [LIVE]  — 2 runs, 15 detections
               https://www.youtube.com/watch?v=abc123
  [2024-11-10] SNES Hidden Gems  (45:30)  — 1 runs, 8 detections
               https://www.youtube.com/watch?v=def456
  [2024-11-05] Console Repair Stream  (2:10:00) [LIVE]  — 1 runs, 22 detections
               https://www.youtube.com/watch?v=ghi789
```

---

## Pipelines

| Pipeline | What it detects | Example entities |
|----------|----------------|-----------------|
| `games` | Video game titles | Super Mario World, Castlevania, Mega Man X |
| `maintenance` | Repair tools, components, hardware mods | ferro de solda, capacitor, mod RGB |
| `all` | Both pipelines combined | — |

---

## Validation

After GLiNER detects entities, a validation layer compares each candidate against known datasets:

```
GLiNER → candidate entities → Validator (fuzzy match) → confirmed entities
```

- **Exact match** against `known_titles.json` → confirmed, name normalized to canonical form
- **Fuzzy match** (>80% similarity) → confirmed with adjusted confidence score
- **No match** → kept but marked with `[?]` in output

### Customizing datasets

Edit the JSON files in `data/datasets/` to improve validation:

```bash
# Add a game that the validator doesn't recognize
# Edit data/datasets/games/known_titles.json and add the title to the list
```

| File | Purpose |
|------|---------|
| `data/datasets/games/known_titles.json` | Known game titles for validation |
| `data/datasets/games/stopwords.json` | Words to always reject |
| `data/datasets/games/consoles.json` | Console names to filter out |
| `data/datasets/games/hints.json` | Whisper transcription hints |
| `data/datasets/maintenance/known_terms.json` | Known tools and components |
| `data/datasets/maintenance/stopwords.json` | Words to always reject |
| `data/datasets/maintenance/hints.json` | Whisper transcription hints |

---

## Caching

Audio files and transcriptions are cached automatically in `.cache/`:

```
.cache/
  audio/{video_id}.webm           # downloaded audio
  transcripts/{video_id}_*.json   # transcription segments (hint-aware)
  retro_game_indexer.db           # SQLite database with all results
```

- **Second runs are fast**: cached audio + cached transcript = only detection runs
- Detection is **never cached** — freely tweak `config.toml` and re-run
- Use `--no-cache` to force a full reprocess
- The transcript cache key includes the Whisper hint, so different pipelines produce separate cache entries

---

## Configuration

Edit `config.toml` at the project root to configure models and calibrate detection.

### Model settings (GPU support)

```toml
[whisper]
model_size = "medium"     # tiny, base, small, medium, large
device = "cuda"           # cpu or cuda
compute_type = "float16"  # int8, float16, float32

[gliner]
model_name = "urchade/gliner_base"
device = "cuda"           # cpu or cuda
```

Defaults (CPU, base model, int8 quantization) work on any machine. Use `cuda` and larger models on machines with a compatible GPU.

### Pipeline calibration

```toml
[games]
threshold = 0.8
blocklist = ["React", "Big Brother", "King"]

[games.aliases]
"Pico Stech" = "PicoStation"
"Resident 3" = "Resident Evil 3"

[maintenance]
threshold = 0.6
blocklist = []

[maintenance.aliases]
"ferro solda" = "ferro de solda"
```

See [calibration.md](calibration.md) for a detailed calibration guide.

---

## Typical Workflow

1. **Discover videos** — list a channel to find interesting content
   ```bash
   retro-game-indexer list "@RetroGameCorps" -n 20 -t live
   ```

2. **Analyze a video** — run detection on a specific video
   ```bash
   retro-game-indexer analyze "https://youtube.com/watch?v=..." -l
   ```

3. **Calibrate** — review output, add false positives to blocklist, add aliases for misspellings
   ```bash
   # Edit config.toml, then re-run (uses cache — only detection runs again)
   retro-game-indexer analyze "https://youtube.com/watch?v=..." -l
   ```

4. **Expand datasets** — add new game titles or maintenance terms to `data/datasets/` to improve validation

5. **Batch analyze** — once calibration looks good, process multiple videos
   ```bash
   retro-game-indexer channel "@RetroGameCorps" -n 10 -l
   ```

6. **Search** — query across all analyzed videos
   ```bash
   retro-game-indexer search "Castlevania"
   retro-game-indexer history
   ```

---

## Running as a Python module

```bash
python -m retro_game_indexer analyze "https://youtube.com/watch?v=..."
python -m retro_game_indexer list "@RetroGameCorps"
python -m retro_game_indexer search "Mario"
```

---

## Environment Variables

Create a `.env` file at the project root (optional):

```
HF_TOKEN=hf_xxxxx           # HuggingFace token (avoids rate limiting)
```

The token is loaded automatically on startup via `python-dotenv`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Models download on first run | Normal — Whisper (~150 MB) and GLiNER (~350 MB) are cached after first download |
| Slow transcription | Use `tiny` model in `config.toml` for speed, or `medium`/`large` for accuracy |
| Too many false positives | Add terms to `blocklist` in `config.toml` — see [calibration.md](calibration.md) |
| Misspelled detections | Add entries to `[games.aliases]` or `[maintenance.aliases]` in `config.toml` |
| Unvalidated entities `[?]` | Add the title to `data/datasets/games/known_titles.json` |
| YouTube URL not recognized | Supported formats: `/watch?v=`, `/live/`, `/embed/`, `/v/`, `youtu.be/`, `shorts/` |
| Cache issues | Use `--no-cache` to force reprocessing, or delete `.cache/` to start fresh |
| GPU not detected | Set `device = "cuda"` in `config.toml` and ensure CUDA drivers are installed |
