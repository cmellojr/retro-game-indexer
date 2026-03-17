# retro-game-indexer

Detect and index retro gaming content from YouTube videos using speech-to-text and named entity recognition.

## Pipelines

- **games** — detect video game names mentioned in videos
- **maintenance** — detect repair tools, electronic components, and hardware modifications

## Stack

- **yt-dlp** — download audio from YouTube
- **faster-whisper** — speech-to-text (Whisper)
- **GLiNER** — zero-shot named entity recognition

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -e .
```

On first run, two ML models are downloaded (~500 MB total) and cached for subsequent runs.

Optionally create a `.env` file at the project root:

```
HF_TOKEN=hf_xxxxx           # HuggingFace token (avoids rate limiting)
```

## Usage

### Single video

```bash
retro-game-indexer analyze "https://youtube.com/watch?v=..."
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p maintenance
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p all
retro-game-indexer analyze "https://youtube.com/watch?v=..." -l          # timestamped links
retro-game-indexer analyze "https://youtube.com/watch?v=..." --no-cache  # force reprocess
```

### List videos from a channel

```bash
retro-game-indexer list "@RetroGameCorps" -n 20
retro-game-indexer list "@RetroGameCorps" -t live
retro-game-indexer list "@RetroGameCorps" -s oldest
```

### Channel batch analysis

```bash
retro-game-indexer channel "@RetroGameCorps" -n 5
retro-game-indexer channel "@RetroGameCorps" -n 10 -t live -p maintenance
retro-game-indexer channel "@RetroGameCorps" -n 5 -l
```

### Search and history

```bash
retro-game-indexer search "Castlevania"      # search across all analyzed videos
retro-game-indexer search "capacitor"         # partial match, case-insensitive
retro-game-indexer history                    # list all analyzed videos
```

### Run as module

```bash
python -m retro_game_indexer analyze "https://youtube.com/watch?v=..."
python -m retro_game_indexer list "@RetroGameCorps"
python -m retro_game_indexer search "Mario"
```

### Common options

| Flag | Default | Description |
|------|---------|-------------|
| `-p, --pipeline` | games | `games`, `maintenance`, or `all` |
| `-l, --links` | off | Append timestamped YouTube links |
| `-n, --max-videos` | 5/10 | Number of videos (channel/list) |
| `-s, --sort` | newest | `newest` or `oldest` |
| `-t, --type` | all | `regular`, `live`, or `all` |
| `--hint` | (auto) | Custom Whisper transcription hint |
| `--config` | config.toml | Path to configuration file |
| `--no-cache` | off | Skip cache and reprocess from scratch |

## Validation

After GLiNER detects entities, a validation layer compares each candidate against known datasets (`data/datasets/`):

- **Exact match** → confirmed, name normalized to canonical form
- **Fuzzy match** (>80% similarity) → confirmed with adjusted confidence
- **No match** → kept but marked with `[?]` in output

Edit the JSON files in `data/datasets/` to improve validation accuracy.

## Configuration

Edit `config.toml` to configure models and calibrate detection. See [docs/calibration.md](docs/calibration.md) for details.

```toml
[whisper]
model_size = "medium"     # tiny, base, small, medium, large
device = "cuda"           # cpu or cuda
compute_type = "float16"  # int8, float16, float32

[gliner]
device = "cuda"           # cpu or cuda

[games]
threshold = 0.8
blocklist = ["React", "Big Brother"]

[games.aliases]
"Pico Stech" = "PicoStation"
```

## Documentation

- [docs/usage.md](docs/usage.md) — full usage guide with examples
- [docs/calibration.md](docs/calibration.md) — calibration and tuning guide
- [docs/ai.md](docs/ai.md) — AI technologies explained
