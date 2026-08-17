#!/usr/bin/env python3
"""Probe a video with ffprobe and emit compact JSON metadata."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional

from runtime import find_binary


def run_ffprobe(path: Path) -> dict:
    ffprobe = find_binary("ffprobe")
    if not ffprobe:
        raise SystemExit("ffprobe not found. Install ffmpeg/ffprobe first.")
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def ratio(width: int, height: int) -> str:
    import math

    if not width or not height:
        return ""
    g = math.gcd(width, height)
    return f"{width // g}:{height // g}"


def fps(value: str) -> Optional[float]:
    if not value or value == "0/0":
        return None
    num, _, den = value.partition("/")
    try:
        return round(float(num) / float(den), 3)
    except (ValueError, ZeroDivisionError):
        return None


def compact(raw: dict) -> dict:
    streams = raw.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    duration = raw.get("format", {}).get("duration") or video.get("duration")
    return {
        "duration_seconds": round(float(duration), 3) if duration else None,
        "width": width or None,
        "height": height or None,
        "aspect_ratio": ratio(width, height),
        "fps": fps(video.get("avg_frame_rate") or video.get("r_frame_rate") or ""),
        "video_codec": video.get("codec_name"),
        "audio_streams": len(audio),
        "has_audio": bool(audio),
        "audio_codecs": sorted({s.get("codec_name") for s in audio if s.get("codec_name")}),
        "format_name": raw.get("format", {}).get("format_name"),
        "bit_rate": raw.get("format", {}).get("bit_rate"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    data = compact(run_ffprobe(args.video))
    text = json.dumps(data, ensure_ascii=False, indent=2)
    if args.out:
        args.out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
