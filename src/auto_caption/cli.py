"""auto-caption command-line interface."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from auto_caption.exporters import export_subtitle, tighten_segments
from auto_caption.transcriber import transcribe_video

app = typer.Typer(
    add_completion=False,
    help="Automatic video subtitle generator powered by mlx-whisper (Chinese by default).",
    no_args_is_help=True,
)
console = Console()

_VALID_FORMATS = {"srt", "vtt", "txt"}


@app.command()
def main(
    media: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
            help="Path to the input video or audio file.",
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            "-o",
            help="Output subtitle file path. Defaults to the source path with the new extension.",
        ),
    ] = None,
    fmt: Annotated[
        str,
        typer.Option(
            "--format",
            "-f",
            help="Subtitle format: srt / vtt / txt.",
            case_sensitive=False,
        ),
    ] = "srt",
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="mlx-whisper model name, Hugging Face repo id, or local directory.",
        ),
    ] = "mlx-community/whisper-large-v3-turbo",
    language: Annotated[
        str,
        typer.Option(
            "--language",
            "-l",
            help="Language code, e.g. 'zh' for Chinese. Use 'auto' to detect.",
        ),
    ] = "zh",
    prompt: Annotated[
        str | None,
        typer.Option(
            "--prompt",
            "-p",
            help="Initial prompt to bias recognition toward proper nouns and context.",
        ),
    ] = None,
    word_timestamps: Annotated[
        bool,
        typer.Option(
            "--word-timestamps/--no-word-timestamps",
            help="Produce word-level timestamps (required for --tight-timestamps).",
        ),
    ] = True,
    tight_timestamps: Annotated[
        bool,
        typer.Option(
            "--tight-timestamps/--loose-timestamps",
            help="Tighten segment start/end to word-level timings so real silence gaps are kept.",
        ),
    ] = True,
    padding: Annotated[
        float,
        typer.Option(
            "--padding",
            min=0.0,
            help=(
                "Seconds of cushion added to each subtitle's start and end on top of "
                "the tight word-level span. 0 means caption timing covers exactly the "
                "speaking interval - nothing more, nothing less (recommended for "
                "maximal accuracy). Raise to e.g. 0.05 if subtitles feel like they "
                "flash in/out too abruptly and you want them to appear slightly "
                "earlier and linger slightly longer. The value is auto-clamped to "
                "the real silence between neighbouring segments, so increasing it "
                "will never cause overlapping captions. Only takes effect with "
                "--tight-timestamps."
            ),
        ),
    ] = 0.0,
    min_duration: Annotated[
        float,
        typer.Option(
            "--min-duration",
            min=0.0,
            help=(
                "Minimum on-screen time for each caption, in seconds. Very short "
                "utterances (single-character interjections like 'yeah' / 'hmm' / "
                "'嗯') may only last ~100-200ms - faithfully using their exact "
                "duration makes them flash by before a viewer can read them. This "
                "floor stretches such captions so they stay visible long enough. "
                "The stretch never crosses into the next caption's start, so it "
                "will not cause overlaps. Default 0.2 is a mild readability guard; "
                "set to 0 for strictly exact speech-interval timing. Only takes "
                "effect with --tight-timestamps."
            ),
        ),
    ] = 0.2,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose/--quiet",
            help="Print mlx-whisper's verbose progress logs.",
        ),
    ] = True,
    also_txt: Annotated[
        bool,
        typer.Option(
            "--also-txt",
            help="Also emit a plain-text transcript next to the subtitle file.",
        ),
    ] = False,
) -> None:
    """Generate a subtitle file for MEDIA."""
    fmt_l = fmt.lower()
    if fmt_l not in _VALID_FORMATS:
        raise typer.BadParameter(f"Unsupported subtitle format: {fmt}", param_hint="--format")

    lang_arg: str | None = None if language.lower() == "auto" else language
    if output is None:
        output = media.with_suffix(f".{fmt_l}")

    console.print(
        Panel.fit(
            f"[bold cyan]Input   [/bold cyan]: {media}\n"
            f"[bold cyan]Model   [/bold cyan]: {model}\n"
            f"[bold cyan]Language[/bold cyan]: {lang_arg or 'auto-detect'}\n"
            f"[bold cyan]Output  [/bold cyan]: {output} ([green]{fmt_l}[/green])",
            title="auto-caption",
            border_style="cyan",
        )
    )

    with console.status("[bold green]Running mlx-whisper...", spinner="dots"):
        result = transcribe_video(
            media,
            model=model,
            language=lang_arg,
            initial_prompt=prompt,
            word_timestamps=word_timestamps or tight_timestamps,
            verbose=verbose,
        )

    if not result.segments:
        console.print(
            "[yellow]Warning: no segments produced; the audio may be empty "
            "or transcription failed.[/yellow]"
        )
        raise typer.Exit(code=1)

    segments = (
        tighten_segments(result.segments, padding=padding, min_duration=min_duration)
        if tight_timestamps
        else result.segments
    )
    written = export_subtitle(segments, output, fmt=fmt_l)
    console.print(f"[bold green]Subtitle written[/bold green]: {written}")

    if also_txt and fmt_l != "txt":
        txt_path = output.with_suffix(".txt")
        export_subtitle(segments, txt_path, fmt="txt")
        console.print(f"[bold green]Transcript written[/bold green]: {txt_path}")

    console.print(f"[dim]language: {result.language} | segments: {len(segments)}[/dim]")


if __name__ == "__main__":
    app()
