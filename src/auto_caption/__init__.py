"""auto_caption: automatic video subtitle generator powered by mlx-whisper."""

from auto_caption.exporters import export_subtitle, tighten_segments
from auto_caption.transcriber import TranscribeResult, transcribe_video

__all__ = [
    "TranscribeResult",
    "export_subtitle",
    "tighten_segments",
    "transcribe_video",
]
__version__ = "0.1.0"
