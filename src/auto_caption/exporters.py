"""Subtitle rendering and timestamp post-processing."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

SubtitleFormat = Literal["srt", "vtt", "txt"]


def tighten_segments(
    segments: Iterable[dict[str, Any]],
    *,
    min_duration: float = 0.2,
    padding: float = 0.05,
) -> list[dict[str, Any]]:
    """Tighten each segment's start/end using word-level timestamps.

    Whisper's default segment timestamps slice the audio contiguously, so the
    ``end`` of one segment often equals the ``start`` of the next and silent
    gaps get absorbed. When ``word_timestamps`` is enabled every segment
    carries a ``words`` list; this function recomputes ``start`` / ``end``
    from those word timings so real silence gaps are preserved. Segments
    without ``words`` are left untouched.
    """
    tightened: list[dict[str, Any]] = []
    for seg in segments:
        new_seg = dict(seg)
        word_times = [
            (float(w["start"]), float(w["end"]))
            for w in (seg.get("words") or [])
            if w.get("start") is not None and w.get("end") is not None
        ]
        if word_times:
            start = max(0.0, min(s for s, _ in word_times) - padding)
            end = max(e for _, e in word_times) + padding
            if end - start < min_duration:
                end = start + min_duration
            new_seg["start"] = start
            new_seg["end"] = end
        tightened.append(new_seg)
    return tightened


def _format_timestamp(seconds: float, *, comma: bool = True) -> str:
    if seconds < 0:
        seconds = 0.0
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1_000)
    sep = "," if comma else "."
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{sep}{milliseconds:03d}"


def segments_to_srt(segments: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, seg in enumerate(segments, start=1):
        start = _format_timestamp(float(seg["start"]), comma=True)
        end = _format_timestamp(float(seg["end"]), comma=True)
        text = str(seg.get("text", "")).strip()
        lines += [str(idx), f"{start} --> {end}", text, ""]
    return "\n".join(lines).rstrip() + "\n"


def segments_to_vtt(segments: Iterable[dict[str, Any]]) -> str:
    lines: list[str] = ["WEBVTT", ""]
    for seg in segments:
        start = _format_timestamp(float(seg["start"]), comma=False)
        end = _format_timestamp(float(seg["end"]), comma=False)
        text = str(seg.get("text", "")).strip()
        lines += [f"{start} --> {end}", text, ""]
    return "\n".join(lines).rstrip() + "\n"


def segments_to_txt(segments: Iterable[dict[str, Any]]) -> str:
    return "\n".join(str(seg.get("text", "")).strip() for seg in segments) + "\n"


_RENDERERS = {
    "srt": segments_to_srt,
    "vtt": segments_to_vtt,
    "txt": segments_to_txt,
}


def export_subtitle(
    segments: Iterable[dict[str, Any]],
    output_path: str | Path,
    fmt: SubtitleFormat = "srt",
) -> Path:
    """Render segments to a subtitle file and return the written path."""
    fmt_l = fmt.lower()
    if fmt_l not in _RENDERERS:
        raise ValueError(f"Unsupported subtitle format: {fmt}")

    output_path = Path(output_path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_RENDERERS[fmt_l](list(segments)), encoding="utf-8")
    return output_path
