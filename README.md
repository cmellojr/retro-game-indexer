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

## Usage

### Single video

```bash
retro-game-indexer analyze "https://youtube.com/watch?v=..."
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p maintenance
retro-game-indexer analyze "https://youtube.com/watch?v=..." -p all
```

### Channel or playlist

```bash
retro-game-indexer channel "https://youtube.com/@ChannelName" -n 5
retro-game-indexer channel "https://youtube.com/@ChannelName" -n 10 --sort oldest
retro-game-indexer channel "https://youtube.com/@ChannelName" -n 5 --type live
retro-game-indexer channel "https://youtube.com/@ChannelName" -n 5 -p maintenance
retro-game-indexer channel "https://youtube.com/playlist?list=..." -n 3 -p all
```

Options:
- `-n, --max-videos` — number of videos to analyze (default: 5)
- `-s, --sort` — `newest` or `oldest` (default: newest)
- `-t, --type` — `regular`, `live`, or `all` (default: all)
- `-p, --pipeline` — `games`, `maintenance`, or `all` (default: games)
- `--hint` — custom Whisper transcription hint (overrides default)

### Run as module

```bash
python -m retro_game_indexer analyze "https://youtube.com/watch?v=..."
python -m retro_game_indexer channel "https://youtube.com/@ChannelName" -n 5
```
