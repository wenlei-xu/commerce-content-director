#!/usr/bin/env python3
"""Concatenate segment videos and burn an SRT or ASS subtitle track once."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from runtime import find_binary


def concat_entry(path: Path) -> str:
    return "file '" + path.resolve().as_posix().replace("'", r"'\\''") + "'\n"


def subtitle_filter(path: Path, font_name: str, margin_v: int, font_weight: str = "regular") -> str:
    escaped = path.resolve().as_posix().replace("'", r"\'").replace(":", r"\:")
    if path.suffix.lower() == ".ass":
        return f"subtitles=filename='{escaped}':charenc=UTF-8"
    bold = "-1" if font_weight == "bold" else "0"
    style = (
        f"FontName={font_name},Bold={bold},FontSize=14,PrimaryColour=&H00FFFFFF,"
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_background_music_gate(background_music: Path, gate_path: Path) -> None:
    """Require proof that the selected BGM stem contains no detected source speech."""
    try:
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read background-music gate: {error}") from error
    if gate.get("schema") != "commerce-source-bgm-gate-v1" or gate.get("status") != "passed":
        raise ValueError("background-music gate must have schema commerce-source-bgm-gate-v1 and status=passed")
    if gate.get("background_music_sha256") != sha256_file(background_music):
        raise ValueError("background-music gate hash does not match the selected BGM stem")
    if gate.get("residual_speech_detected") is not False:
        raise ValueError("background-music gate must explicitly report residual_speech_detected=false")


def chinese_audio_filter(subtitles: Path, font_name: str, margin_v: int, font_weight: str, target_duration: int, has_environment: bool) -> str:
    environment = (
        f"[0:a]volume=0.45,apad,atrim=duration={target_duration},asetpts=PTS-STARTPTS[environment]"
        if has_environment
        else f"anullsrc=r=48000:cl=stereo,atrim=duration={target_duration}[environment]"
    )
    return (
        f"[0:v]{subtitle_filter(subtitles, font_name, margin_v, font_weight)}[video];"
        f"{environment};"
        f"[1:a]volume=1.0,apad,atrim=duration={target_duration},asetpts=PTS-STARTPTS,asplit=2[voice_mix][voice_key];"
        f"[2:a]volume=0.22,atrim=duration={target_duration},asetpts=PTS-STARTPTS[bgm];"
        "[bgm][voice_key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[ducked_bgm];"
        "[environment][ducked_bgm][voice_mix]amix=inputs=3:duration=first:normalize=0[audio]"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("videos", nargs="+", type=Path, help="Segment videos in chronological order")
    parser.add_argument("--subtitles", required=True, type=Path)
    parser.add_argument("--voiceover", type=Path, help="Aligned narration track from align_voiceover.py")
    parser.add_argument("--background-music", type=Path, help="Speech-free BGM stem separated from the approved reference video")
    parser.add_argument("--background-music-gate", type=Path, help="Passed residual-speech gate for --background-music")
    parser.add_argument(
        "--audio-policy",
        choices=["legacy", "chinese_external_tts"],
        default="legacy",
        help="Use chinese_external_tts for Omni environment + separated BGM + Doubao voiceover",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path, help="content-system-config-snapshot.json")
    parser.add_argument("--font-name", default="Microsoft YaHei", help="Default: Microsoft YaHei Bold")
    parser.add_argument(
        "--subtitle-font-weight",
        choices=["regular", "bold"],
        default="bold",
        help="Font weight for ordinary SRT subtitles; ignored for ASS tracks",
    )
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
    background_music = args.background_music.resolve() if args.background_music else None
    background_music_gate = args.background_music_gate.resolve() if args.background_music_gate else None
    if args.audio_policy == "chinese_external_tts":
        if not voiceover:
            raise SystemExit("chinese_external_tts requires --voiceover from aligned Doubao TTS")
        if not background_music or not background_music.is_file():
            raise SystemExit("chinese_external_tts requires an existing --background-music stem")
        if not background_music_gate or not background_music_gate.is_file():
            raise SystemExit("chinese_external_tts requires --background-music-gate")
        try:
            validate_background_music_gate(background_music, background_music_gate)
        except ValueError as error:
            raise SystemExit(f"Invalid background-music gate: {error}") from error

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
        if args.audio_policy == "chinese_external_tts":
            command.extend([
                "-i", str(voiceover),
                "-stream_loop", "-1", "-i", str(background_music),
                "-filter_complex",
                chinese_audio_filter(
                    subtitles, args.font_name, args.subtitle_margin_v,
                    args.subtitle_font_weight, target_duration, has_bed,
                ),
                "-map", "[video]", "-map", "[audio]",
            ])
        elif voiceover and has_bed:
            command.extend([
                "-i", str(voiceover),
                "-filter_complex",
                f"[0:v]{subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v, args.subtitle_font_weight)}[video];"
                "[0:a]volume=0.18[bed];[1:a]volume=1.0[narration];"
                "[bed][narration]amix=inputs=2:duration=first:normalize=0[audio]",
                "-map", "[video]", "-map", "[audio]",
            ])
        elif voiceover:
            command.extend([
                "-i", str(voiceover),
                "-filter_complex",
                f"[0:v]{subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v, args.subtitle_font_weight)}[video];"
                "[1:a]volume=1.0[audio]",
                "-map", "[video]", "-map", "[audio]",
            ])
        else:
            command.extend([
                "-map", "0:v:0", "-map", "0:a?", "-vf",
                subtitle_filter(subtitles, args.font_name, args.subtitle_margin_v, args.subtitle_font_weight),
            ])
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
