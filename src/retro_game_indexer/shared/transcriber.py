"""Transcribe audio to text segments using faster-whisper."""

import sys
from collections.abc import Callable
from pathlib import Path

from faster_whisper import WhisperModel

_model: WhisperModel | None = None
_model_key: tuple[str, str, str] | None = None


def _get_model(
    size: str = "base", device: str = "cpu", compute_type: str = "int8"
) -> WhisperModel:
    """Get or create a cached WhisperModel instance.

    Args:
        size: Model size ("tiny", "base", "small", "medium", "large").
        device: Device to run on ("cpu" or "cuda").
        compute_type: Quantization type ("int8", "float16", "float32").

    Returns:
        Cached WhisperModel instance.
    """
    global _model, _model_key
    key = (size, device, compute_type)
    if _model is None or _model_key != key:
        _model = WhisperModel(size, device=device, compute_type=compute_type)
        _model_key = key
    return _model


def transcribe(
    audio_path: Path | str,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8",
    hint: str = "",
    on_progress: Callable[[float], None] | None = None,
) -> list[dict]:
    """Transcribe audio file to text segments.

    Args:
        audio_path: Path to the audio file.
        model_size: Whisper model size to use.
        device: Device to run on ("cpu" or "cuda").
        compute_type: Quantization type ("int8", "float16", "float32").
        hint: Initial prompt to bias transcription towards known terms.
        on_progress: Optional callback called with progress percentage (0-100).

    Returns:
        List of dicts with "text" and "start" keys for each segment.
    """
    model = _get_model(model_size, device, compute_type)
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
