"""List videos from a YouTube channel or playlist."""

from dataclasses import dataclass
from urllib.parse import urlparse

import yt_dlp


_CHANNEL_TABS = ("/videos", "/streams", "/shorts", "/playlists", "/community")


def resolve_channel(name_or_url: str) -> str:
    """Convert a channel name or handle to a full YouTube URL.

    Accepts any of these formats:
        - Full URL: https://youtube.com/@ChannelName (normalized to /videos)
        - Handle: @ChannelName
        - Plain name: ChannelName

    For channel URLs without a specific tab, ``/videos`` is appended so that
    yt-dlp returns individual video entries instead of channel tabs.

    Args:
        name_or_url: Channel name, @handle, or full URL.

    Returns:
        Full YouTube channel URL ending with a tab path.
    """
    text = name_or_url.strip()

    parsed = urlparse(text)
    if parsed.scheme in ("http", "https"):
        path = parsed.path.rstrip("/")
        is_channel = "/@" in path or "/c/" in path or "/channel/" in path
        has_tab = any(path.endswith(tab) for tab in _CHANNEL_TABS)
        if is_channel and not has_tab:
            return text.rstrip("/") + "/videos"
        return text

    if not text.startswith("@"):
        text = f"@{text}"

    return f"https://www.youtube.com/{text}/videos"


@dataclass
class VideoInfo:
    """Metadata for a YouTube video.

    Attributes:
        url: YouTube video URL.
        title: Video title.
        upload_date: Upload date in YYYYMMDD format.
        duration: Video duration in seconds, or None.
        live_status: One of "is_live", "was_live", "not_live", or None.
    """

    url: str
    title: str
    upload_date: str
    duration: float | None
    live_status: str | None


def list_videos(
    channel_url: str,
    max_videos: int = 10,
    sort_order: str = "newest",
) -> list[VideoInfo]:
    """Return video metadata from a channel or playlist URL.

    Args:
        channel_url: YouTube channel or playlist URL.
        max_videos: Maximum number of videos to return.
        sort_order: Sort order, "newest" or "oldest".

    Returns:
        List of VideoInfo objects sorted by the requested order.

    Raises:
        ValueError: If URL does not contain multiple videos.
    """
    ydl_opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "playlist_items": f"1-{max_videos * 3}",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

    if info is None:
        return []

    entries = info.get("entries")
    if entries is None:
        raise ValueError(
            "URL does not contain multiple videos. Use 'analyze' for a single video."
        )

    videos: list[VideoInfo] = []
    for entry in entries:
        if entry is None or entry.get("url") is None:
            continue
        videos.append(
            VideoInfo(
                url=entry.get("url", ""),
                title=entry.get("title", "Unknown"),
                upload_date=entry.get("upload_date", ""),
                duration=entry.get("duration"),
                live_status=entry.get("live_status"),
            )
        )

    if sort_order == "oldest":
        videos.reverse()

    return videos[:max_videos]
