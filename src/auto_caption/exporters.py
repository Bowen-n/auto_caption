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
    padding: float = 0.0,
) -> list[dict[str, Any]]:
    """Replace each segment's start/end with the true word-level span.

    Whisper's default segment timestamps slice the audio contiguously: the
    ``end`` of one segment usually equals the ``start`` of the next, and any
    silence between sentences gets absorbed into the neighbouring caption.
    When ``word_timestamps`` is enabled every segment carries a ``words``
    list; this function rebuilds each segment's ``start`` / ``end`` from the
    earliest and latest word timings so only the real speaking interval is
    kept. Segments without a ``words`` list are left untouched.

    Visual overview (time flows left -> right, '#' = voiced, '.' = silence)::

        raw whisper segments (back-to-back, eat silence):
            seg A |###### . . . . ######|
            seg B                        |###### . . ######|
                  ^-- end[A] == start[B], gap lost

        word-level timings inside each segment:
            seg A words:  [###]   [##]         [#####]
            seg B words:                 [####]        [##]

        after tighten_segments (padding=0, min_duration=0):
            seg A |###------#####|
            seg B                       |####-----##|
                                 ^^^^^^^ real silence preserved

        with padding=p (clamped by real silence, so never overlaps):
            seg A |<-p ###------##### p->|
            seg B                  |<-p ####-----## p->|

        with min_duration=d (short captions are stretched to >= d,
        but only as far as the next segment allows):
            short seg: |#|  ->  |#----------|   (length becomes d)

    Parameters
    ----------
    min_duration:
        Minimum on-screen time in seconds for each caption. Acts as a
        readability floor for very short utterances (e.g. single-character
        interjections). The stretch is clamped to the next segment's start
        so it never creates overlaps. Set to ``0`` to disable.
    padding:
        Extra seconds added to both sides of the tight word span. ``0``
        means captions match the exact speaking interval. Raise for a
        smoother reading feel; auto-clamped to the real silence between
        neighbours so adjacent captions never overlap.
    """
    seg_list = [dict(s) for s in segments]

    bounds: list[tuple[float, float] | None] = []
    for seg in seg_list:
        word_times = [
            (float(w["start"]), float(w["end"]))
            for w in (seg.get("words") or [])
            if w.get("start") is not None and w.get("end") is not None
        ]
        bounds.append(
            (min(s for s, _ in word_times), max(e for _, e in word_times))
            if word_times
            else None
        )

    for i, seg in enumerate(seg_list):
        b = bounds[i]
        if b is None:
            continue
        raw_start, raw_end = b

        prev_end = next(
            (bounds[j][1] for j in range(i - 1, -1, -1) if bounds[j] is not None),
            0.0,
        )
        next_start = next(
            (bounds[j][0] for j in range(i + 1, len(seg_list)) if bounds[j] is not None),
            float("inf"),
        )

        left_room = max(0.0, raw_start - prev_end)
        right_room = max(0.0, next_start - raw_end)
        start = max(0.0, raw_start - min(padding, left_room))
        end = raw_end + min(padding, right_room)

        if end - start < min_duration:
            end = min(start + min_duration, next_start)

        seg["start"] = start
        seg["end"] = end

    return seg_list


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
