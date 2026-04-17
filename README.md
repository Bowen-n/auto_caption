# auto-caption

Automatic video subtitle generator powered by
[mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper).
Runs locally on Apple Silicon (MLX).

## Features

- Accepts `.mp4` / `.mov` / `.mp3` / `.wav` and more, decoded via ffmpeg.
- Default model `mlx-community/whisper-large-v3-turbo`: fast with solid quality.
- Exports `srt` / `vtt` / `txt`; can also emit a plain-text transcript.
- Tightens each segment to real word-level timestamps so silence gaps are preserved.
- Managed with [uv](https://github.com/astral-sh/uv); uses the Aliyun PyPI mirror by default.

## Prerequisites

- macOS on Apple Silicon (MLX requires Apple Silicon)
- [`uv`](https://github.com/astral-sh/uv) and [`ffmpeg`](https://ffmpeg.org/)

```bash
brew install ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Install

```bash
make install
```

## Usage

```bash
# emit an SRT next to the video with the same base name
uv run auto-caption path/to/video.mp4

# also write a plain-text transcript
uv run auto-caption path/to/video.mp4 --also-txt
```

### CLI options

| Option | Default | Description |
| --- | --- | --- |
| `-o, --output` | next to source | Output subtitle file path |
| `-f, --format` | `srt` | Subtitle format: `srt` / `vtt` / `txt` |
| `-m, --model` | `mlx-community/whisper-large-v3-turbo` | mlx-whisper model name, HF repo id, or local dir |
| `-l, --language` | `zh` | Language code; `auto` to detect |
| `-p, --prompt` | — | Initial prompt for proper nouns / context |
| `--word-timestamps / --no-word-timestamps` | on | Produce word-level timestamps |
| `--tight-timestamps / --loose-timestamps` | on | Tighten segments to word-level timings |
| `--verbose / --quiet` | `verbose` | Print mlx-whisper logs |
| `--also-txt` | off | Also emit a `.txt` transcript |

### Python API

```python
from auto_caption import export_subtitle, tighten_segments, transcribe_video

result = transcribe_video("video.mp4", language="zh", word_timestamps=True)
export_subtitle(tighten_segments(result.segments), "video.srt", fmt="srt")
```

## Development

```bash
make install       # sync runtime + dev dependencies
make check         # ruff lint + format check
make fix           # auto-fix lint issues and format
make format        # format only
make lint          # lint only
```

## License

MIT
