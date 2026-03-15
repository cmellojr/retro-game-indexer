# Usage Guide

## Installation

```bash
pip install -e .
```

## Commands

### `list` — List videos from a channel

Lists videos and/or lives from a YouTube channel without downloading or analyzing anything.

```bash
retro-game-indexer list "@RetroGameCorps"                   # latest 10 videos/lives
retro-game-indexer list "@RetroGameCorps" -t live            # only live streams
retro-game-indexer list "@RetroGameCorps" -t regular         # only regular videos
retro-game-indexer list "@RetroGameCorps" -n 20 -s oldest   # 20 oldest
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `-n, --max-videos` | 10 | Number of videos to list |
| `-s, --sort` | newest | Sort order: `newest` or `oldest` |
| `-t, --type` | all | Filter: `regular`, `live`, or `all` |

**Input formats** (all commands accept these):

```
RetroGameCorps                                    # plain name
@RetroGameCorps                                   # handle
https://www.youtube.com/@RetroGameCorps           # full URL
https://www.youtube.com/playlist?list=PLxxxxx     # playlist URL
```

---

### `analyze` — Analyze a single video

Downloads audio, transcribes, and detects entities from a single YouTube video.

```bash
retro-game-indexer analyze "https://youtube.com/watch?v=..."
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p maintenance
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p all
retro-game-indexer analyze "https://youtube.com/watch?v=..." -l          # with timestamp links
retro-game-indexer analyze "https://youtube.com/watch?v=..." --no-cache  # force reprocess
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `-p, --pipeline` | games | Detection pipeline: `games`, `maintenance`, or `all` |
| `-l, --links` | off | Append timestamped YouTube links to each result |
| `--hint` | (auto) | Custom Whisper hint (overrides pipeline default) |
| `--config` | config.toml | Path to calibration config |
| `--no-cache` | off | Skip cache and reprocess from scratch |

---

### `channel` — Analyze multiple videos from a channel

Same as `analyze`, but processes N videos from a channel in batch.

```bash
retro-game-indexer channel "@RetroGameCorps" -n 3
retro-game-indexer channel "@RetroGameCorps" -n 5 -t live -p maintenance
retro-game-indexer channel "@RetroGameCorps" -n 2 -l --config custom.toml
```

**Options:**

| Flag | Default | Description |
|------|---------|-------------|
| `-n, --max-videos` | 5 | Number of videos to analyze |
| `-s, --sort` | newest | Sort order: `newest` or `oldest` |
| `-t, --type` | all | Filter: `regular`, `live`, or `all` |
| `-p, --pipeline` | games | Detection pipeline: `games`, `maintenance`, or `all` |
| `-l, --links` | off | Append timestamped YouTube links |
| `--hint` | (auto) | Custom Whisper hint |
| `--config` | config.toml | Path to calibration config |
| `--no-cache` | off | Skip cache and reprocess from scratch |

---

## Caching

Audio files and transcription results are cached automatically in `.cache/` at the project root:

```
.cache/
  audio/{video_id}.m4a         # downloaded audio
  transcripts/{video_id}_*.json # transcription segments
```

- **Second runs are fast**: cached audio + cached transcript = only detection runs (~15s instead of ~5min)
- Detection is **never cached** so you can freely tweak `config.toml` and re-run
- Use `--no-cache` to force a full reprocess (e.g. if a video was re-uploaded)

---

## Calibration

Edit `config.toml` to refine detection results without changing code. See [calibration.md](calibration.md) for details.

---

## Pipelines

| Pipeline | What it detects | Example entities |
|----------|----------------|-----------------|
| `games` | Video game titles | Super Mario World, Castlevania, Resident Evil |
| `maintenance` | Repair tools, electronic components, hardware mods | ferro de solda, capacitor, mod RGB |
| `all` | Both pipelines combined | — |
