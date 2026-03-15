"""CLI entry point for retro-game-indexer."""

import os
import sys
import tempfile
import warnings
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings("ignore", message=".*resume_download.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*unauthenticated.*", category=UserWarning)

import typer

from retro_game_indexer.pipelines.games.detector import GameDetector
from retro_game_indexer.pipelines.games.hints import DEFAULT_HINTS as GAME_HINTS
from retro_game_indexer.pipelines.maintenance.detector import MaintenanceDetector
from retro_game_indexer.pipelines.maintenance.hints import (
    DEFAULT_HINTS as MAINTENANCE_HINTS,
)
from retro_game_indexer.shared.audio import download_audio
from retro_game_indexer.shared.cache import (
    cache_audio,
    cache_transcript,
    extract_video_id,
    get_cached_audio,
    get_cached_transcript,
)
from retro_game_indexer.shared.channel import VideoInfo, list_videos, resolve_channel
from retro_game_indexer.shared.config import PipelineConfig, load_config
from retro_game_indexer.shared.db import (
    list_processed_videos,
    save_detections,
    save_run,
    save_video,
    search_by_name,
)
from retro_game_indexer.shared.transcriber import transcribe

app = typer.Typer()


def _get_hint(pipeline: str) -> str:
    """Return the appropriate transcription hint for the pipeline.

    Args:
        pipeline: Pipeline name ("games", "maintenance", or "all").

    Returns:
        Hint string for Whisper transcription.
    """
    if pipeline == "games":
        return GAME_HINTS
    if pipeline == "maintenance":
        return MAINTENANCE_HINTS
    return f"{GAME_HINTS}, {MAINTENANCE_HINTS}"


def _get_detectors(
    pipeline: str, config: dict[str, PipelineConfig] | None = None
) -> list[tuple[str, object]]:
    """Create detector instances for the selected pipeline.

    Args:
        pipeline: Pipeline name ("games", "maintenance", or "all").
        config: Per-pipeline user configuration from config.toml.

    Returns:
        List of (label, detector) tuples.
    """
    config = config or {}
    detectors: list[tuple[str, object]] = []

    if pipeline in ("games", "all"):
        cfg = config.get("games", PipelineConfig())
        kwargs: dict = {"blocklist": cfg.blocklist, "aliases": cfg.aliases}
        if cfg.threshold is not None:
            kwargs["threshold"] = cfg.threshold
        detectors.append(("games", GameDetector(**kwargs)))

    if pipeline in ("maintenance", "all"):
        cfg = config.get("maintenance", PipelineConfig())
        kwargs = {"blocklist": cfg.blocklist, "aliases": cfg.aliases}
        if cfg.threshold is not None:
            kwargs["threshold"] = cfg.threshold
        detectors.append(("maintenance", MaintenanceDetector(**kwargs)))

    return detectors


def _analyze_single_video(
    url: str,
    hint: str,
    tmp_dir: Path,
    detectors: list[tuple[str, object]],
    use_cache: bool = True,
) -> dict[str, list[dict]]:
    """Analyze one video and return mentions from all detectors.

    Args:
        url: YouTube video URL.
        hint: Transcription hint for Whisper.
        tmp_dir: Temporary directory for audio files.
        detectors: List of (label, detector) tuples.
        use_cache: If True, use disk cache for audio and transcription.

    Returns:
        Dict mapping pipeline label to list of mention dicts.
    """
    video_id = extract_video_id(url)

    # Audio: check cache first
    audio = get_cached_audio(video_id) if use_cache else None
    if audio is not None:
        print("  Using cached audio.")
    else:
        print("  Downloading audio...")
        audio = download_audio(url, tmp_dir)
        if use_cache:
            cache_audio(video_id, audio)

    # Transcription: check cache first
    segments = get_cached_transcript(video_id, hint) if use_cache else None
    if segments is not None:
        print("  Using cached transcript.")
    else:
        print("  Transcribing...", flush=True)

        def _progress(pct: float) -> None:
            bar_len = 30
            filled = int(bar_len * pct / 100)
            bar = "█" * filled + "░" * (bar_len - filled)
            sys.stdout.write(f"\r  Transcribing... [{bar}] {pct:5.1f}%")
            sys.stdout.flush()
            if pct >= 100:
                print()

        segments = transcribe(audio, hint=hint, on_progress=_progress)
        if use_cache:
            cache_transcript(video_id, hint, segments)

    # Detection: always runs (depends on config.toml calibration)
    results: dict[str, list[dict]] = {}
    for label, detector in detectors:
        print(f"  Detecting ({label})...")
        results[label] = detector.detect(segments)

    return results


def _timestamp_url(video_url: str, seconds: float) -> str:
    """Build a YouTube URL that jumps to a specific timestamp.

    Args:
        video_url: Base YouTube video URL.
        seconds: Timestamp in seconds.

    Returns:
        URL with ``&t=`` or ``?t=`` parameter appended.
    """
    sep = "&" if "?" in video_url else "?"
    return f"{video_url}{sep}t={int(seconds)}s"


def _print_mentions(
    mentions: list[dict], video_url: str = "", links: bool = False
) -> None:
    """Print mentions in formatted output.

    Args:
        mentions: List of mention dicts with standardized keys.
        video_url: YouTube video URL (used when *links* is True).
        links: If True, append a timestamped YouTube link to each mention.
    """
    for m in mentions:
        line = (
            f"  {m['timestamp']:.1f}s  {m['name']}  "
            f"[{m['category']}]  score={m['confidence']:.2f}"
        )
        if links and video_url:
            line += f"  {_timestamp_url(video_url, m['timestamp'])}"
        print(line)


def _tab_urls_for_type(channel_url: str, video_type: str) -> list[str]:
    """Return YouTube tab URL(s) to fetch based on the video type filter.

    YouTube separates regular uploads (``/videos``) and live streams
    (``/streams``) into different tabs.  This helper maps ``-t`` values to
    the correct tab URL(s).

    Args:
        channel_url: Resolved channel URL (typically ending in ``/videos``).
        video_type: One of "regular", "live", or "all".

    Returns:
        List of tab URLs to fetch.
    """
    if "/videos" not in channel_url:
        return [channel_url]

    if video_type == "live":
        return [channel_url.replace("/videos", "/streams")]
    if video_type == "all":
        return [channel_url, channel_url.replace("/videos", "/streams")]
    return [channel_url]


def _sort_and_trim(
    videos: list[VideoInfo], sort_order: str, max_videos: int
) -> list[VideoInfo]:
    """Sort merged video lists and trim to max_videos.

    Args:
        videos: List of VideoInfo objects (possibly from multiple tabs).
        sort_order: "newest" or "oldest".
        max_videos: Maximum number of videos to keep.

    Returns:
        Sorted and trimmed list of VideoInfo objects.
    """
    reverse = sort_order != "oldest"
    videos.sort(key=lambda v: v.upload_date or "", reverse=reverse)
    return videos[:max_videos]


def _fetch_videos(
    name_or_url: str, video_type: str, max_videos: int, sort: str
) -> list[VideoInfo]:
    """Resolve a channel URL, fetch videos from the correct tab(s) and trim.

    Args:
        name_or_url: Channel name, @handle, or full URL.
        video_type: One of "regular", "live", or "all".
        max_videos: Maximum number of videos to return.
        sort: Sort order, "newest" or "oldest".

    Returns:
        Sorted list of VideoInfo objects.
    """
    url = resolve_channel(name_or_url)
    tab_urls = _tab_urls_for_type(url, video_type)

    print(f"Listing videos from {tab_urls[0]}...")
    videos: list[VideoInfo] = []
    for tab_url in tab_urls:
        videos.extend(
            list_videos(tab_url, max_videos=max_videos * 2, sort_order=sort)
        )
    return _sort_and_trim(videos, sort, max_videos)


def _format_duration(seconds: float | None) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS.

    Args:
        seconds: Duration in seconds, or None.

    Returns:
        Formatted duration string or "?" if unknown.
    """
    if seconds is None:
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _format_date(upload_date: str) -> str:
    """Format YYYYMMDD date to YYYY-MM-DD.

    Args:
        upload_date: Date in YYYYMMDD format, or empty string.

    Returns:
        Formatted date or "?" if unknown.
    """
    if len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    return upload_date or "?"


@app.command(name="list")
def list_cmd(
    name_or_url: str = typer.Argument(
        help="Channel name, @handle, or full YouTube URL"
    ),
    max_videos: int = typer.Option(10, "--max-videos", "-n", help="Number of videos"),
    sort: str = typer.Option("newest", "--sort", "-s", help="newest or oldest"),
    video_type: str = typer.Option(
        "all", "--type", "-t", help="regular, live, or all"
    ),
) -> None:
    """List videos and lives from a YouTube channel without analyzing.

    Accepts a channel name, @handle, or full URL. Examples:
        retro-game-indexer list RetroGameCorps
        retro-game-indexer list @RetroGameCorps -t live
        retro-game-indexer list "https://youtube.com/@RetroGameCorps" -n 20

    Args:
        name_or_url: Channel name, @handle, or full YouTube URL.
        max_videos: Maximum number of videos to list.
        sort: Sort order, "newest" or "oldest".
        video_type: Filter by "regular", "live", or "all".
    """
    videos = _fetch_videos(name_or_url, video_type, max_videos, sort)

    if not videos:
        print("No videos found.")
        raise typer.Exit(1)

    type_label = {"live": "lives", "regular": "videos", "all": "videos/lives"}
    print(f"\n{len(videos)} {type_label.get(video_type, 'videos')}:\n")

    for i, v in enumerate(videos, 1):
        date = _format_date(v.upload_date)
        dur = _format_duration(v.duration)
        tag = " [LIVE]" if v.live_status in ("was_live", "is_live") else ""
        print(f"  {i:>3}. [{date}] {v.title}  ({dur}){tag}")
        print(f"       {v.url}")


@app.command()
def analyze(
    url: str,
    pipeline: str = typer.Option(
        "games", "--pipeline", "-p", help="Pipeline: games, maintenance, or all"
    ),
    hint: str = typer.Option("", help="Custom hint for Whisper (overrides default)"),
    links: bool = typer.Option(
        False, "--links", "-l", help="Show timestamped YouTube links"
    ),
    config: str = typer.Option(
        "config.toml", "--config", help="Path to config.toml for calibration"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Skip cache and reprocess from scratch"
    ),
) -> None:
    """Analyze a single YouTube video.

    Args:
        url: YouTube video URL.
        pipeline: Detection pipeline to use.
        hint: Custom transcription hint for Whisper.
        links: If True, show timestamped YouTube links.
        config: Path to config.toml for calibration overrides.
        no_cache: If True, skip cache and reprocess from scratch.
    """
    effective_hint = hint or _get_hint(pipeline)
    tmp_dir = Path(tempfile.mkdtemp(prefix="rgi_"))
    cfg = load_config(config)
    detectors = _get_detectors(pipeline, cfg)

    results = _analyze_single_video(
        url, effective_hint, tmp_dir, detectors, use_cache=not no_cache
    )

    # Persist to database
    video_id = extract_video_id(url)
    save_video(video_id, url, title=url)
    for label, mentions in results.items():
        pipeline_cfg = cfg.get(label, PipelineConfig())
        run_id = save_run(
            video_id, label, pipeline_cfg.threshold,
            pipeline_cfg.blocklist, pipeline_cfg.aliases, effective_hint,
        )
        save_detections(run_id, mentions)

    for label, mentions in results.items():
        print(f"\n[{label.upper()}] {len(mentions)} items found:\n")
        _print_mentions(mentions, video_url=url, links=links)


@app.command()
def channel(
    name_or_url: str = typer.Argument(
        help="Channel name, @handle, or full YouTube URL"
    ),
    max_videos: int = typer.Option(5, "--max-videos", "-n", help="Number of videos"),
    sort: str = typer.Option("newest", "--sort", "-s", help="newest or oldest"),
    video_type: str = typer.Option(
        "all", "--type", "-t", help="regular, live, or all"
    ),
    pipeline: str = typer.Option(
        "games", "--pipeline", "-p", help="Pipeline: games, maintenance, or all"
    ),
    hint: str = typer.Option("", help="Custom hint for Whisper (overrides default)"),
    links: bool = typer.Option(
        False, "--links", "-l", help="Show timestamped YouTube links"
    ),
    config: str = typer.Option(
        "config.toml", "--config", help="Path to config.toml for calibration"
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", help="Skip cache and reprocess from scratch"
    ),
) -> None:
    """Analyze multiple videos from a YouTube channel or playlist.

    Accepts a channel name, @handle, or full URL. Examples:
        retro-game-indexer channel RetroGameCorps
        retro-game-indexer channel @RetroGameCorps
        retro-game-indexer channel "https://youtube.com/@RetroGameCorps"

    Args:
        name_or_url: Channel name, @handle, or full YouTube URL.
        max_videos: Maximum number of videos to analyze.
        sort: Sort order, "newest" or "oldest".
        video_type: Filter by "regular", "live", or "all".
        pipeline: Detection pipeline to use.
        hint: Custom transcription hint for Whisper.
        links: If True, show timestamped YouTube links.
        config: Path to config.toml for calibration overrides.
        no_cache: If True, skip cache and reprocess from scratch.
    """
    effective_hint = hint or _get_hint(pipeline)
    videos = _fetch_videos(name_or_url, video_type, max_videos, sort)

    if not videos:
        print("No videos found.")
        raise typer.Exit(1)

    print(f"\nFound {len(videos)} videos:\n")
    for i, v in enumerate(videos, 1):
        date = v.upload_date or "?"
        print(f"  {i}. {v.title} ({date})")

    tmp_root = Path(tempfile.mkdtemp(prefix="rgi_"))
    cfg = load_config(config)
    detectors = _get_detectors(pipeline, cfg)
    all_results: list[dict] = []

    for i, video in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {video.title}")
        sub_dir = tmp_root / f"video_{i}"

        try:
            results = _analyze_single_video(
                video.url, effective_hint, sub_dir, detectors,
                use_cache=not no_cache,
            )

            # Persist to database
            vid = extract_video_id(video.url)
            save_video(
                vid, video.url, video.title,
                video.upload_date, video.duration, video.live_status,
            )
            for label, mentions in results.items():
                pipeline_cfg = cfg.get(label, PipelineConfig())
                run_id = save_run(
                    vid, label, pipeline_cfg.threshold,
                    pipeline_cfg.blocklist, pipeline_cfg.aliases, effective_hint,
                )
                save_detections(run_id, mentions)

            total = sum(len(m) for m in results.values())
            print(f"  Found {total} items.")
            all_results.append({"video": video, "results": results})
        except Exception as exc:
            print(f"  ERROR: Skipping - {exc}")
            all_results.append(
                {"video": video, "results": {l: [] for l, _ in detectors}}
            )

    # Final report
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)

    unique_names: dict[str, set[str]] = {l: set() for l, _ in detectors}

    for result in all_results:
        video = result["video"]
        results = result["results"]
        print(f"\n--- {video.title} ---")
        has_any = False
        for label, mentions in results.items():
            if mentions:
                has_any = True
                print(f"  [{label.upper()}]")
                _print_mentions(mentions, video_url=video.url, links=links)
                unique_names[label].update(m["name"] for m in mentions)
        if not has_any:
            print("  No items detected.")

    print()
    for label, names in unique_names.items():
        print(f"Total [{label}]: {len(names)} unique items across {len(videos)} videos.")


@app.command()
def search(
    name: str = typer.Argument(help="Entity name to search for"),
) -> None:
    """Search for a game or term across all analyzed videos.

    Examples:
        retro-game-indexer search "Castlevania"
        retro-game-indexer search "capacitor"

    Args:
        name: Entity name (partial match, case-insensitive).
    """
    rows = search_by_name(name)

    if not rows:
        print(f"No results found for \"{name}\".")
        raise typer.Exit(1)

    print(f"\n{len(rows)} results for \"{name}\":\n")

    current_video = None
    for row in rows:
        if row["title"] != current_video:
            current_video = row["title"]
            print(f"  --- {current_video} ---")
        line = (
            f"    {row['timestamp']:.1f}s  {row['name']}  "
            f"[{row['category']}]  score={row['confidence']:.2f}"
        )
        print(line)


@app.command()
def history() -> None:
    """List all previously analyzed videos with detection counts.

    Examples:
        retro-game-indexer history
    """
    rows = list_processed_videos()

    if not rows:
        print("No videos analyzed yet.")
        raise typer.Exit(1)

    print(f"\n{len(rows)} videos analyzed:\n")

    for row in rows:
        date = _format_date(row["upload_date"] or "")
        dur = _format_duration(row["duration"])
        tag = ""
        if row["live_status"] in ("was_live", "is_live"):
            tag = " [LIVE]"
        print(
            f"  [{date}] {row['title']}  ({dur}){tag}"
            f"  — {row['total_runs']} runs, {row['total_detections']} detections"
        )
        print(f"           {row['url']}")


if __name__ == "__main__":
    app()
