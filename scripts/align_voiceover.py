#!/usr/bin/env python3
"""Align generated narration clips to the validated storyboard timeline."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from runtime import find_binary


EMPTY_CAPTIONS = {"", "none", "null", "n/a", "无", "无字幕", "无口播", "无对白"}


def caption_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.lower() in EMPTY_CAPTIONS else text


def resolve_inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes package directory: {value}") from exc
    return path


def manifest_paths(segment: dict) -> list[str]:
    values = segment.get("manifests")
    if values is None and segment.get("manifest"):
        values = [segment["manifest"]]
    if not isinstance(values, list) or not values:
        raise ValueError(f"{segment.get('id', '?')} has no manifests")
    return values


def cues_from_package(package_dir: Path) -> tuple[float, list[dict]]:
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    cues: list[dict] = []
    for segment in package["segments"]:
        for manifest_value in manifest_paths(segment):
            manifest = json.loads(resolve_inside(package_dir, manifest_value).read_text(encoding="utf-8"))
            narration_cues = manifest.get("narration_cues")
            if narration_cues is not None:
                for cue in narration_cues:
                    text = caption_text(cue.get("text"))
                    if text:
                        cues.append({"id": str(cue["id"]), "start": float(cue["start"]), "end": float(cue["end"])})
            else:
                # Legacy package fallback: narration used to live on every SB.
                for panel in manifest.get("panels", []):
                    text = caption_text(panel.get("dialogue")) or caption_text(panel.get("subtitle"))
                    if text:
                        cues.append({"id": str(panel["id"]), "start": float(panel["start"]), "end": float(panel["end"])})
    return float(package["total_duration_seconds"]), sorted(cues, key=lambda item: (item["start"], item["end"]))


def parse_clips(values: list[str]) -> dict[str, Path]:
    clips: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid --clip {value!r}; use VO-ID=audio-path")
        cue_id, raw_path = value.split("=", 1)
        cue_id, path = cue_id.strip(), Path(raw_path).expanduser().resolve()
        if not cue_id or not path.is_file():
            raise ValueError(f"Invalid --clip {value!r}")
        if cue_id in clips:
            raise ValueError(f"Duplicate audio for {cue_id}")
        clips[cue_id] = path
    return clips


def duration_seconds(ffprobe: str, path: Path) -> float:
    output = subprocess.check_output(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    ).strip()
    return float(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--clip", action="append", default=[], metavar="VO-ID=AUDIO")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    ffmpeg, ffprobe = find_binary("ffmpeg"), find_binary("ffprobe")
    if not ffmpeg or not ffprobe:
        raise SystemExit("ffmpeg/ffprobe were not found; run scripts/preflight.py")
    total_duration, cues = cues_from_package(args.package_dir.resolve())
    clips = parse_clips(args.clip)
    expected = {cue["id"] for cue in cues}
    if not expected:
        raise SystemExit("No non-empty narration cues or legacy Dialogue / Subtitle fields were found.")
    if set(clips) != expected:
        missing, extra = sorted(expected - set(clips)), sorted(set(clips) - expected)
        details = ([f"missing: {', '.join(missing)}"] if missing else []) + ([f"unexpected: {', '.join(extra)}"] if extra else [])
        raise SystemExit("Clip mapping does not match narration cues (" + "; ".join(details) + ")")
    output = args.out.resolve()
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Output exists: {output}. Pass --overwrite to replace it.")
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [ffmpeg, "-hide_banner", "-y" if args.overwrite else "-n"]
    for cue in cues:
        command.extend(["-i", str(clips[cue["id"]])])
    filters = [f"anullsrc=r=32000:cl=mono,atrim=duration={total_duration:.3f}[base]"]
    labels = ["[base]"]
    for index, cue in enumerate(cues):
        duration = duration_seconds(ffprobe, clips[cue["id"]])
        slot = cue["end"] - cue["start"]
        if duration > slot + 0.05:
            raise SystemExit(f"{cue['id']} narration is {duration:.2f}s but its storyboard slot is {slot:.2f}s; shorten and regenerate it.")
        delay_ms = round(cue["start"] * 1000)
        filters.append(f"[{index}:a]adelay={delay_ms}:all=1,atrim=duration={cue['end']:.3f}[cue{index}]")
        labels.append(f"[cue{index}]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=first:normalize=0,loudnorm=I=-16:LRA=7:TP=-1.5[voice]")
    command.extend([
        "-filter_complex", ";".join(filters), "-map", "[voice]", "-t", f"{total_duration:.3f}",
        "-c:a", "libmp3lame", "-b:a", "192k", str(output),
    ])
    subprocess.run(command, check=True)
    print(f"Wrote aligned voiceover: {output}")


if __name__ == "__main__":
    main()
