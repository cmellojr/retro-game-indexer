"""Read and write data lake files (bronze/silver/gold layers).

Bronze: raw, immutable, append-only (YouTube metadata + transcripts).
Silver: AI outputs, versioned by run_id (detections + config snapshot).
Gold: consolidated knowledge, overwritable (latest confirmed entities).
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_BRONZE_DIR = _DATA_DIR / "bronze"
_SILVER_DIR = _DATA_DIR / "silver"
_GOLD_DIR = _DATA_DIR / "gold"


def _ensure_dir(path: Path) -> Path:
    """Create directory tree if needed and return it."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _utcnow() -> str:
    """Return current UTC time in ISO 8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hint_hash(hint: str) -> str:
    """Return a short hash of the hint string (matches cache.py logic)."""
    return hashlib.sha256(hint.encode()).hexdigest()[:12]


def _write_json(path: Path, data: dict) -> Path:
    """Write dict as formatted JSON."""
    _ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def _read_json(path: Path) -> dict | None:
    """Read JSON file or return None if missing."""
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Run ID ─────────────────────────────────────────────────────────


def generate_run_id(pipeline: str, model_name: str) -> str:
    """Generate a unique run ID.

    Format: ``YYYYMMDD_HHMMSS_{pipeline}_{model_hash8}``

    Args:
        pipeline: Pipeline name ("games" or "maintenance").
        model_name: Model identifier (e.g. "urchade/gliner_base").

    Returns:
        Run ID string.
    """
    now = datetime.now(timezone.utc)
    model_hash = hashlib.sha256(model_name.encode()).hexdigest()[:8]
    return f"{now.strftime('%Y%m%d_%H%M%S')}_{pipeline}_{model_hash}"


# ── Bronze layer (immutable, append-only) ──────────────────────────


def save_bronze_metadata(
    video_id: str,
    url: str,
    title: str,
    upload_date: str | None = None,
    duration: float | None = None,
    live_status: str | None = None,
    language: str = "pt-BR",
) -> Path:
    """Save raw YouTube metadata to bronze layer.

    Writes only if the file does not already exist (immutable).

    Args:
        video_id: YouTube video ID.
        url: Full YouTube URL.
        title: Video title.
        upload_date: Upload date in YYYYMMDD format.
        duration: Duration in seconds.
        live_status: "was_live", "is_live", "not_live", or None.
        language: ISO language code for the video content.

    Returns:
        Path to the metadata file.
    """
    path = _BRONZE_DIR / video_id / "metadata.json"
    if path.is_file():
        return path
    return _write_json(path, {
        "schema_version": "1.0",
        "video_id": video_id,
        "url": url,
        "title": title,
        "upload_date": upload_date,
        "duration": duration,
        "live_status": live_status,
        "language": language,
        "fetched_at": _utcnow(),
    })


def save_bronze_transcript(
    video_id: str,
    hint: str,
    segments: list[dict],
    whisper_model: str = "base",
    language: str = "pt-BR",
) -> Path:
    """Save raw transcript to bronze layer.

    Writes only if the file does not already exist (immutable).

    Args:
        video_id: YouTube video ID.
        hint: Whisper hint used for transcription.
        segments: List of segment dicts with "text" and "start" keys.
        whisper_model: Whisper model size used.
        language: ISO language code.

    Returns:
        Path to the transcript file.
    """
    h = _hint_hash(hint)
    path = _BRONZE_DIR / video_id / f"transcript_{h}.json"
    if path.is_file():
        return path
    return _write_json(path, {
        "schema_version": "1.0",
        "video_id": video_id,
        "hint": hint,
        "hint_hash": h,
        "whisper_model": whisper_model,
        "language": language,
        "transcribed_at": _utcnow(),
        "segments": segments,
    })


def get_bronze_transcript(video_id: str, hint: str) -> list[dict] | None:
    """Read raw transcript segments from bronze layer.

    Args:
        video_id: YouTube video ID.
        hint: Whisper hint (determines file variant).

    Returns:
        List of segment dicts, or None if not found.
    """
    h = _hint_hash(hint)
    data = _read_json(_BRONZE_DIR / video_id / f"transcript_{h}.json")
    if data is None:
        return None
    return data.get("segments")


def get_bronze_metadata(video_id: str) -> dict | None:
    """Read video metadata from bronze layer.

    Args:
        video_id: YouTube video ID.

    Returns:
        Metadata dict, or None if not found.
    """
    return _read_json(_BRONZE_DIR / video_id / "metadata.json")


# ── Silver layer (versioned AI outputs) ────────────────────────────


def save_silver_detections(
    video_id: str,
    run_id: str,
    pipeline: str,
    detections: list[dict],
    config_snapshot: dict,
    language: str = "pt-BR",
) -> Path:
    """Save detection results to silver layer.

    Args:
        video_id: YouTube video ID.
        run_id: Unique run identifier from generate_run_id().
        pipeline: Pipeline name.
        detections: List of detection dicts from validator.
        config_snapshot: Dict with threshold, blocklist, aliases, hint,
            gliner_model, whisper_model used for this run.
        language: ISO language code.

    Returns:
        Path to the silver file.
    """
    validated = sum(1 for d in detections if d.get("validated", True))
    return _write_json(_SILVER_DIR / video_id / f"{run_id}.json", {
        "schema_version": "1.0",
        "run_id": run_id,
        "video_id": video_id,
        "pipeline": pipeline,
        "language": language,
        "created_at": _utcnow(),
        "config": config_snapshot,
        "detections": detections,
        "summary": {
            "total": len(detections),
            "validated": validated,
            "unvalidated": len(detections) - validated,
        },
    })


def list_silver_runs(video_id: str) -> list[str]:
    """List all run IDs for a video, sorted oldest first.

    Args:
        video_id: YouTube video ID.

    Returns:
        List of run_id strings.
    """
    video_dir = _SILVER_DIR / video_id
    if not video_dir.is_dir():
        return []
    return sorted(p.stem for p in video_dir.glob("*.json"))


def get_silver_run(video_id: str, run_id: str) -> dict | None:
    """Read a specific silver run file.

    Args:
        video_id: YouTube video ID.
        run_id: Run identifier.

    Returns:
        Full run dict, or None if not found.
    """
    return _read_json(_SILVER_DIR / video_id / f"{run_id}.json")


# ── Gold layer (consolidated knowledge) ────────────────────────────


def save_gold_entities(
    video_id: str,
    entities: dict[str, list[dict]],
    url: str = "",
    title: str = "",
    source_runs: dict[str, str] | None = None,
    language: str = "pt-BR",
) -> Path:
    """Save consolidated entity knowledge for a video.

    Overwrites on each run (gold is the latest truth).

    Args:
        video_id: YouTube video ID.
        entities: Dict mapping pipeline name to list of validated entities.
        url: Video URL for reference.
        title: Video title for reference.
        source_runs: Dict mapping pipeline name to run_id that produced it.
        language: ISO language code.

    Returns:
        Path to the gold file.
    """
    return _write_json(_GOLD_DIR / f"{video_id}.json", {
        "schema_version": "1.0",
        "video_id": video_id,
        "title": title,
        "url": url,
        "language": language,
        "updated_at": _utcnow(),
        "source_runs": source_runs or {},
        "entities": entities,
    })


def get_gold_entities(video_id: str) -> dict | None:
    """Read consolidated entities for a video.

    Args:
        video_id: YouTube video ID.

    Returns:
        Gold file dict, or None if not found.
    """
    return _read_json(_GOLD_DIR / f"{video_id}.json")


def build_gold_from_silver(video_id: str) -> dict[str, list[dict]]:
    """Rebuild gold layer from the latest silver run per pipeline.

    Args:
        video_id: YouTube video ID.

    Returns:
        Dict mapping pipeline name to list of confirmed entities.
    """
    runs = list_silver_runs(video_id)
    latest_by_pipeline: dict[str, dict] = {}
    for run_id in runs:
        data = get_silver_run(video_id, run_id)
        if data:
            latest_by_pipeline[data["pipeline"]] = data

    entities: dict[str, list[dict]] = {}
    for pipeline, data in latest_by_pipeline.items():
        entities[pipeline] = [
            d for d in data.get("detections", []) if d.get("validated", True)
        ]
    return entities


# ── Lake-wide operations ───────────────────────────────────────────


def list_all_videos() -> list[str]:
    """List all video IDs that have bronze data.

    Returns:
        List of video_id strings.
    """
    if not _BRONZE_DIR.is_dir():
        return []
    return sorted(
        p.name for p in _BRONZE_DIR.iterdir()
        if p.is_dir() and (p / "metadata.json").is_file()
    )


def rebuild_db_from_lake() -> int:
    """Rebuild the SQLite database from bronze + silver files.

    Reads all bronze metadata and silver detection files,
    then repopulates the videos, runs, and detections tables.

    Returns:
        Number of videos processed.
    """
    # Import here to avoid circular imports
    from retro_game_indexer.shared.db import (
        save_detections,
        save_run,
        save_video,
        _get_db,
    )

    db = _get_db()
    db.execute("DELETE FROM detections")
    db.execute("DELETE FROM runs")
    db.execute("DELETE FROM videos")
    db.commit()

    video_ids = list_all_videos()
    for video_id in video_ids:
        meta = get_bronze_metadata(video_id)
        if not meta:
            continue

        save_video(
            video_id,
            meta.get("url", ""),
            meta.get("title", ""),
            meta.get("upload_date"),
            meta.get("duration"),
            meta.get("live_status"),
        )

        for run_id in list_silver_runs(video_id):
            run_data = get_silver_run(video_id, run_id)
            if not run_data:
                continue
            cfg = run_data.get("config", {})
            int_id = save_run(
                video_id,
                run_data.get("pipeline", ""),
                cfg.get("threshold"),
                set(cfg.get("blocklist", [])),
                cfg.get("aliases", {}),
                cfg.get("hint", ""),
                run_id=run_id,
            )
            save_detections(int_id, run_data.get("detections", []))

    return len(video_ids)
