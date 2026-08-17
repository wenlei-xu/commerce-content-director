#!/usr/bin/env python3
"""Extract rhythm frames from a video at a fixed interval."""

import argparse
import subprocess
from pathlib import Path

from runtime import find_binary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=0.75)
    parser.add_argument("--width", type=int, default=720)
    args = parser.parse_args()

    ffmpeg = find_binary("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found. Install ffmpeg first.")
    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    if args.interval <= 0:
        raise SystemExit("--interval must be positive")

    args.out.mkdir(parents=True, exist_ok=True)
    pattern = args.out / "frame_%04d.jpg"
    fps_expr = f"fps=1/{args.interval},scale={args.width}:-1"
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(args.video),
        "-vf",
        fps_expr,
        "-frame_pts",
        "1",
        "-q:v",
        "2",
        str(pattern),
    ]
    subprocess.run(cmd, check=True)
    frames = sorted(args.out.glob("frame_*.jpg"))
    print(f"extracted {len(frames)} frames to {args.out}")


if __name__ == "__main__":
    main()
