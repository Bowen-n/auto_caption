"""Thin wrapper around mlx-whisper for video/audio transcription."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TranscribeResult:
    """Transcription result.

    ``segments`` mirrors the structure returned by mlx-whisper. Each entry
    contains at least ``start`` / ``end`` / ``text``, and also ``words`` when
    ``word_timestamps`` was enabled.
    """

    text: str
    segments: list[dict[str, Any]] = field(default_factory=list)
    language: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


def transcribe_video(
    media_path: str | Path,
    *,
    model: str = "mlx-community/whisper-large-v3-turbo",
    language: str | None = "zh",
    initial_prompt: str | None = None,
    word_timestamps: bool = False,
    verbose: bool | None = False,
    temperature: float | tuple[float, ...] = 0.0,
    condition_on_previous_text: bool = True,
) -> TranscribeResult:
    """Transcribe a video or audio file.

    Pass ``language=None`` to let the model auto-detect. ``model`` accepts a
    Hugging Face repo id or a local directory. All other arguments are
    forwarded to ``mlx_whisper.transcribe``.
    """
    import mlx_whisper

    media_path = Path(media_path).expanduser().resolve()
    if not media_path.exists():
        raise FileNotFoundError(f"Media file not found: {media_path}")

    result: dict[str, Any] = mlx_whisper.transcribe(
        str(media_path),
        path_or_hf_repo=model,
        language=language,
        initial_prompt=initial_prompt,
        word_timestamps=word_timestamps,
        verbose=verbose,
        temperature=temperature,
        condition_on_previous_text=condition_on_previous_text,
    )

    return TranscribeResult(
        text=result.get("text", "").strip(),
        segments=list(result.get("segments", [])),
        language=result.get("language", language or ""),
        raw=result,
    )
