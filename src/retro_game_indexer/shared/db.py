"""SQLite persistence for video metadata and detection results."""

import json
import sqlite3
from pathlib import Path

_DB_PATH = Path(".cache") / "retro_game_indexer.db"
_connection: sqlite3.Connection | None = None

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS videos (
    video_id    TEXT PRIMARY KEY,
    url         TEXT NOT NULL,
    title       TEXT NOT NULL,
    upload_date TEXT,
    duration    REAL,
    live_status TEXT,
    language    TEXT DEFAULT 'pt-BR',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE TABLE IF NOT EXISTS runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id        TEXT NOT NULL REFERENCES videos(video_id) ON DELETE CASCADE,
    pipeline        TEXT NOT NULL,
    threshold       REAL,
    blocklist_json  TEXT,
    aliases_json    TEXT,
    hint            TEXT NOT NULL,
    run_id          TEXT,
    created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%S','now'))
);

CREATE INDEX IF NOT EXISTS idx_runs_video ON runs(video_id);

CREATE TABLE IF NOT EXISTS detections (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    timestamp   REAL NOT NULL,
    confidence  REAL NOT NULL,
    validated   INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_detections_run ON detections(run_id);
CREATE INDEX IF NOT EXISTS idx_detections_name ON detections(name COLLATE NOCASE);
"""


def _migrate(db: sqlite3.Connection) -> None:
    """Apply schema migrations for existing databases."""
    # Add validated column if missing (added in v0.3)
    det_cols = {row[1] for row in db.execute("PRAGMA table_info(detections)")}
    if "validated" not in det_cols:
        db.execute(
            "ALTER TABLE detections ADD COLUMN validated INTEGER NOT NULL DEFAULT 1"
        )

    # Add run_id string column to runs (added in v0.4)
    run_cols = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
    if "run_id" not in run_cols:
        db.execute("ALTER TABLE runs ADD COLUMN run_id TEXT")

    # Add language column to videos (added in v0.4)
    vid_cols = {row[1] for row in db.execute("PRAGMA table_info(videos)")}
    if "language" not in vid_cols:
        db.execute("ALTER TABLE videos ADD COLUMN language TEXT DEFAULT 'pt-BR'")

    db.commit()


def _get_db() -> sqlite3.Connection:
    """Return a singleton database connection, creating tables if needed."""
    global _connection
    if _connection is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(_DB_PATH))
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode = WAL")
        _connection.execute("PRAGMA foreign_keys = ON")
        _connection.executescript(_SCHEMA)
        _migrate(_connection)
    return _connection


# ── Write operations ─────────────────────────────────────────────────


def save_video(
    video_id: str,
    url: str,
    title: str,
    upload_date: str | None = None,
    duration: float | None = None,
    live_status: str | None = None,
) -> None:
    """Insert or update a video record.

    Args:
        video_id: YouTube video ID.
        url: Full YouTube URL.
        title: Video title.
        upload_date: Upload date in YYYYMMDD format.
        duration: Duration in seconds.
        live_status: One of "was_live", "is_live", "not_live", or None.
    """
    db = _get_db()
    db.execute(
        """INSERT INTO videos (video_id, url, title, upload_date, duration, live_status)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(video_id) DO UPDATE SET
               title = excluded.title,
               upload_date = excluded.upload_date,
               duration = excluded.duration,
               live_status = excluded.live_status""",
        (video_id, url, title, upload_date, duration, live_status),
    )
    db.commit()


def save_run(
    video_id: str,
    pipeline: str,
    threshold: float | None,
    blocklist: set[str] | None,
    aliases: dict[str, str] | None,
    hint: str,
    run_id: str | None = None,
) -> int:
    """Record a detection run and return its integer ID.

    Args:
        video_id: YouTube video ID.
        pipeline: Pipeline name ("games" or "maintenance").
        threshold: Confidence threshold used.
        blocklist: Blocklist terms used.
        aliases: Alias mappings used.
        hint: Whisper hint string used.
        run_id: Data lake run identifier (e.g. "20260317_143500_games_a1b2c3d4").

    Returns:
        The auto-generated integer run ID.
    """
    db = _get_db()
    cursor = db.execute(
        """INSERT INTO runs (video_id, pipeline, threshold, blocklist_json, aliases_json, hint, run_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            video_id,
            pipeline,
            threshold,
            json.dumps(sorted(blocklist)) if blocklist else None,
            json.dumps(aliases, ensure_ascii=False) if aliases else None,
            hint,
            run_id,
        ),
    )
    db.commit()
    return cursor.lastrowid


def save_detections(run_id: int, mentions: list[dict]) -> None:
    """Bulk-insert detection results for a run.

    Args:
        run_id: ID of the parent run record.
        mentions: List of mention dicts with "name", "category",
            "timestamp", "confidence", and optional "validated" keys.
    """
    if not mentions:
        return
    db = _get_db()
    db.executemany(
        """INSERT INTO detections (run_id, name, category, timestamp, confidence, validated)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [
            (
                run_id,
                m["name"],
                m["category"],
                m["timestamp"],
                m["confidence"],
                int(m.get("validated", True)),
            )
            for m in mentions
        ],
    )
    db.commit()


# ── Read operations ──────────────────────────────────────────────────


def search_by_name(name: str) -> list[dict]:
    """Find all detections matching a name (case-insensitive).

    Args:
        name: Entity name to search for (partial match with LIKE).

    Returns:
        List of dicts with video and detection info.
    """
    db = _get_db()
    rows = db.execute(
        """SELECT v.title, v.url, d.name, d.category, d.timestamp,
                  d.confidence, d.validated, r.pipeline, r.created_at
           FROM detections d
           JOIN runs r ON d.run_id = r.id
           JOIN videos v ON r.video_id = v.video_id
           WHERE d.name LIKE ? COLLATE NOCASE
           ORDER BY d.confidence DESC""",
        (f"%{name}%",),
    ).fetchall()
    return [dict(row) for row in rows]


def list_processed_videos() -> list[dict]:
    """List all videos that have been analyzed, with detection counts.

    Returns:
        List of dicts with video info and per-pipeline counts.
    """
    db = _get_db()
    rows = db.execute(
        """SELECT v.video_id, v.url, v.title, v.upload_date, v.duration,
                  v.live_status, v.created_at,
                  COUNT(DISTINCT r.id) AS total_runs,
                  COUNT(d.id) AS total_detections
           FROM videos v
           LEFT JOIN runs r ON r.video_id = v.video_id
           LEFT JOIN detections d ON d.run_id = r.id
           GROUP BY v.video_id
           ORDER BY v.created_at DESC""",
    ).fetchall()
    return [dict(row) for row in rows]


def get_latest_detections(video_id: str) -> dict[str, list[dict]]:
    """Get the most recent detection results per pipeline for a video.

    Args:
        video_id: YouTube video ID.

    Returns:
        Dict mapping pipeline name to list of detection dicts.
    """
    db = _get_db()

    # Find the latest run per pipeline
    latest_runs = db.execute(
        """SELECT id, pipeline FROM runs
           WHERE video_id = ?
           AND id IN (
               SELECT MAX(id) FROM runs
               WHERE video_id = ?
               GROUP BY pipeline
           )""",
        (video_id, video_id),
    ).fetchall()

    results: dict[str, list[dict]] = {}
    for run in latest_runs:
        detections = db.execute(
            """SELECT name, category, timestamp, confidence
               FROM detections WHERE run_id = ?
               ORDER BY timestamp""",
            (run["id"],),
        ).fetchall()
        results[run["pipeline"]] = [dict(d) for d in detections]

    return results
