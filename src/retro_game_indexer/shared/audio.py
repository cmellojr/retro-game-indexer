"""Download audio from YouTube videos using yt-dlp."""

from pathlib import Path

import yt_dlp


def download_audio(url: str, output_dir: Path) -> Path:
    """Download audio from a YouTube video.

    Args:
        url: YouTube video URL.
        output_dir: Directory to save the audio file.

    Returns:
        Path to the downloaded audio file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "audio.%(ext)s"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(output_file),
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return Path(filename)
