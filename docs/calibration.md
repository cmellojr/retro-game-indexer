# Calibration Guide

The detection results can be refined by editing `config.toml` at the project root. No code changes needed.

## Quick Start

1. Run an analysis:
   ```bash
   retro-game-indexer analyze "https://youtube.com/watch?v=..." -l
   ```

2. Identify false positives in the output (e.g., "React", "King")

3. Edit `config.toml`:
   ```toml
   [games]
   blocklist = ["React", "King", "Big Brother"]
   ```

4. Run the same video again (uses cache — only detection re-runs):
   ```bash
   retro-game-indexer analyze "https://youtube.com/watch?v=..." -l
   ```

5. False positives are gone. Repeat until results look good.

## Configuration Options

### `threshold` — Confidence cutoff

Controls how confident the model must be to report a detection.

```toml
[games]
threshold = 0.85    # stricter: fewer results, less noise

[maintenance]
threshold = 0.5     # looser: more results, more noise
```

| Value | Effect |
|-------|--------|
| 0.5 | Very permissive. Many false positives. |
| 0.7 | Default for games. Good balance. |
| 0.85 | Strict. Only high-confidence detections. |
| 0.95 | Very strict. May miss legitimate results. |

### `blocklist` — Reject false positives

Terms that should never appear as results. Case-insensitive. Added on top of the built-in stopwords.

```toml
[games]
blocklist = [
    "React",
    "Big Brother",
    "let's go",
    "Chris",
    "King",
    "video game",
    "portuguesebr",
]
```

Common false positives to blocklist:
- Generic words the model incorrectly tags as games ("blades", "carregan")
- Names of people or shows ("Big Brother", "Chris")
- Technical terms from the video context ("React", "portuguesebr")

### `aliases` — Fix transcription variants

Maps misspelled or variant transcriptions to the correct canonical name. Case-insensitive keys.

```toml
[games.aliases]
"Pico Stech" = "PicoStation"
"Pico Steixo" = "PicoStation"
"pico-stech" = "PicoStation"
"Resident 3" = "Resident Evil 3"

[maintenance.aliases]
"ferro solda" = "ferro de solda"
"multimetro" = "multímetro"
```

When an alias matches, the canonical name is used for both display and deduplication. This means "Pico Stech" and "PicoStation" won't appear as separate entries.

## Full Example

```toml
[games]
threshold = 0.8
blocklist = [
    "React", "Big Brother", "let's go", "Chris",
    "King", "portuguesebr", "video game", "blades",
]

[games.aliases]
"Pico Stech" = "PicoStation"
"Pico Steixo" = "PicoStation"
"pico-stech" = "PicoStation"
"Pekálicá" = "PicoStation"
"Resident 3" = "Resident Evil 3"
"Rc3" = "Resident Evil 3"
"Rc1" = "Resident Evil"

[maintenance]
threshold = 0.6
blocklist = []

[maintenance.aliases]
```

## Using a Different Config File

```bash
retro-game-indexer analyze URL --config my-custom-config.toml
```

## Datasets

In addition to `config.toml`, you can improve detection accuracy by editing the JSON datasets in `data/datasets/`:

| File | Purpose |
|------|---------|
| `games/known_titles.json` | Known game titles for validation (fuzzy match) |
| `games/stopwords.json` | Words to always reject |
| `games/consoles.json` | Console names to filter out |
| `games/hints.json` | Whisper transcription hints |
| `maintenance/known_terms.json` | Known tools and components for validation |
| `maintenance/stopwords.json` | Words to always reject |
| `maintenance/hints.json` | Whisper transcription hints |

Adding a title to `known_titles.json` helps the validator confirm detections and normalize names. Adding a term to `stopwords.json` rejects it before it reaches the validator.

## Tips

- Start with the default threshold, then increase if you see too much noise
- After the first run, re-runs use cache — only detection runs again (~15s)
- The blocklist and aliases are applied **after** model inference, so they don't affect what the model sees
- Whisper hints (loaded from `data/datasets/*/hints.json`) affect transcription quality; blocklist/aliases affect post-processing
- Entities marked with `[?]` in the output were not found in the known datasets — add them to `known_titles.json` or `known_terms.json` if they are valid
