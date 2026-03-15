"""Transcribe audio to text segments using faster-whisper."""

import sys
from collections.abc import Callable
from pathlib import Path

from faster_whisper import WhisperModel

_model: WhisperModel | None = None


def _get_model(size: str = "base") -> WhisperModel:
    """Get or create a cached WhisperModel instance.

    Args:
        size: Model size ("tiny", "base", "small", "medium", "large").

    Returns:
        Cached WhisperModel instance.
    """
    global _model
    if _model is None or _model.model_size_or_path != size:
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def transcribe(
    audio_path: Path | str,
    model_size: str = "base",
    hint: str = "",
    on_progress: Callable[[float], None] | None = None,
) -> list[dict]:
    """Transcribe audio file to text segments.

    Args:
        audio_path: Path to the audio file.
        model_size: Whisper model size to use.
        hint: Initial prompt to bias transcription towards known terms.
        on_progress: Optional callback called with progress percentage (0-100).

    Returns:
        List of dicts with "text" and "start" keys for each segment.
    """
    model = _get_model(model_size)
    segments_gen, info = model.transcribe(
        audio_path, initial_prompt=hint or None
    )
    duration = info.duration or 0

    result: list[dict] = []
    for seg in segments_gen:
        result.append({"text": seg.text, "start": seg.start})
        if on_progress and duration > 0:
            pct = min(seg.end / duration * 100, 100)
            on_progress(pct)

    if on_progress:
        on_progress(100)

    return result
