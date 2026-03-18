"""Disk cache for audio files and transcription segments."""

import hashlib
import json
import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse

_CACHE_DIR = Path(".cache")


def _ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def extract_video_id(url: str) -> str:
    """Extract the YouTube video ID from a URL.

    Handles standard, short, and embed URL formats.

    Args:
        url: YouTube video URL.

    Returns:
        Video ID string.

    Raises:
        ValueError: If the video ID cannot be extracted.
    """
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]
        if parsed.path.startswith(("/embed/", "/v/", "/live/")):
            return parsed.path.split("/")[2]

    raise ValueError(f"Cannot extract video ID from URL: {url}")


def _hint_hash(hint: str) -> str:
    """Return a short hash of the transcription hint string."""
    return hashlib.sha256(hint.encode()).hexdigest()[:12]


# ── Audio cache ──────────────────────────────────────────────────────

def get_cached_audio(video_id: str) -> Path | None:
    """Return the cached audio file path, or None if not cached.

    Args:
        video_id: YouTube video ID.

    Returns:
        Path to the cached audio file, or None.
    """
    audio_dir = _CACHE_DIR / "audio"
    if not audio_dir.exists():
        return None
    for path in audio_dir.iterdir():
        if path.stem == video_id and path.is_file():
            return path
    return None


def cache_audio(video_id: str, audio_path: Path) -> Path:
    """Copy an audio file into the cache.

    Args:
        video_id: YouTube video ID.
        audio_path: Path to the downloaded audio file.

    Returns:
        Path to the cached copy.
    """
    dest_dir = _ensure_dir(_CACHE_DIR / "audio")
    dest = dest_dir / f"{video_id}{audio_path.suffix}"
    shutil.copy2(audio_path, dest)
    return dest


# ── Transcript cache ─────────────────────────────────────────────────

def get_cached_transcript(video_id: str, hint: str) -> list[dict] | None:
    """Return cached transcription segments, or None if not cached.

    Checks the bronze data lake first, then falls back to the legacy
    ``.cache/transcripts/`` directory.

    Args:
        video_id: YouTube video ID.
        hint: Whisper transcription hint (affects cache key).

    Returns:
        List of segment dicts, or None.
    """
    # Try bronze layer first (data lake source of truth)
    from retro_game_indexer.shared.datalake import get_bronze_transcript

    segments = get_bronze_transcript(video_id, hint)
    if segments is not None:
        return segments

    # Fall back to legacy .cache/transcripts/ path
    path = _CACHE_DIR / "transcripts" / f"{video_id}_{_hint_hash(hint)}.json"
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cache_transcript(
    video_id: str, hint: str, segments: list[dict]
) -> None:
    """Save transcription segments to the cache.

    Args:
        video_id: YouTube video ID.
        hint: Whisper transcription hint (affects cache key).
        segments: List of segment dicts with "text" and "start" keys.
    """
    dest_dir = _ensure_dir(_CACHE_DIR / "transcripts")
    path = dest_dir / f"{video_id}_{_hint_hash(hint)}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
