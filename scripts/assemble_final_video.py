#!/usr/bin/env python3
"""Concatenate segment videos in order and burn an SRT subtitle track once."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from runtime import find_binary


def concat_entry(path: Path) -> str:
    return "file '" + path.resolve().as_posix().replace("'", r"'\\''") + "'\n"


def subtitle_filter(path: Path, font_name: str, margin_v: int) -> str:
    escaped = path.resolve().as_posix().replace("'", r"\'").replace(":", r"\:")
    style = (
        f"FontName={font_name},Bold=-1,FontSize=14,PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV={margin_v}"
    )
    return f"subtitles=filename='{escaped}':charenc=UTF-8:force_style='{style}'"


def has_audio_stream(ffprobe: str, path: Path) -> bool:
    """Return whether a segment contains an audio stream.

    Video models may legitimately return silent clips.  In that case the final
    narration is still a complete audio track and must not make assembly fail.
    """
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("videos", nargs="+", type=Path, help="Segment videos in chronological order")
    parser.add_argument("--subtitles", required=True, type=Path)
    parser.add_argument("--voiceover", type=Path, help="Aligned narration track from align_voiceover.py")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path, help="content-system-config-snapshot.json")
    parser.add_argument("--font-name", default="Microsoft YaHei", help="Default: Microsoft YaHei Bold")
    parser.add_argument("--subtitle-margin-v", type=int, default=95, help="Bottom subtitle margin in pixels; smaller is lower")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8"))
        target_duration = int(profile["target_duration_seconds"])
        allowed = {int(value) for value in profile["allowed_durations_seconds"]}
        if target_duration <= 0 or target_duration not in allowed:
            raise ValueError("target_duration_seconds must be one of allowed_durations_seconds")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"Invalid content-system configuration profile: {error}") from error

    ffmpeg, ffprobe = find_binary("ffmpeg"), find_binary("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg/ffprobe were not found; run scripts/preflight.py")
    videos = [path.resolve() for path in args.videos]
    missing = [str(path) for path in videos if not path.is_file()]
    if missing:
        raise SystemExit("Missing segment video(s): " + ", ".join(missing))
    subtitles = args.subtitles.resolve()
    if not subtitles.is_file():
        raise SystemExit(f"Missing subtitle file: {subtitles}")
    output = args.out.resolve()
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Output exists: {output}. Pass --overwrite to replace it.")
    output.parent.mkdir(parents=True, exist_ok=True)
    voiceover = args.voiceover.resolve() if args.voiceover else None
    if voiceover and not voiceover.is_file():
        raise SystemExit(f"Missing voiceover file: {voiceover}")

    list_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", prefix="concat-", dir=output.parent, delete=False
        ) as handle:
            list_path = Path(handle.name)
            handle.writelines(concat_entry(path) for path in videos)
        command = [
            ffmpeg,
            "-hide_banner",
            "-y" if args.overwrite else "-n",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
        ]
        has_bed = all(has_audio_stream(ffprobe, path) for path in videos)
        if voiceover and has_bed:
            command.extend([
                "-i", str(voiceover),
                "-filter_complex",
                f"[0:v]{subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v)}[video];"
                "[0:a]volume=0.18[bed];[1:a]volume=1.0[narration];"
                "[bed][narration]amix=inputs=2:duration=first:normalize=0[audio]",
                "-map", "[video]", "-map", "[audio]",
            ])
        elif voiceover:
            command.extend([
                "-i", str(voiceover),
                "-filter_complex",
                f"[0:v]{subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v)}[video];"
                "[1:a]volume=1.0[audio]",
                "-map", "[video]", "-map", "[audio]",
            ])
        else:
            command.extend(["-map", "0:v:0", "-map", "0:a?", "-vf", subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v)])
        command.extend([
            "-c:v", "libx264", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
        ])
        command[-1:-1] = ["-t", str(target_duration)]
        subprocess.run(command, check=True)
    finally:
        if list_path and list_path.exists():
            list_path.unlink()
    print(f"Wrote final subtitled video: {output}")


if __name__ == "__main__":
    main()
