#!/usr/bin/env python3
"""Validate single portrait GPT Image 2.5 first frames before Feishu upload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


TOLERANCE = 0.01


def parse_ratio(value: str) -> float:
    left, right = value.split(":", 1)
    ratio = float(left) / float(right)
    if ratio <= 0:
        raise ValueError("first_frame_ratio must be positive")
    return ratio


def load_profile(path: Path) -> float:
    profile = json.loads(path.read_text(encoding="utf-8"))
    layout = profile.get("first_frame_layout") or {}
    ratio = layout.get("aspect_ratio")
    if not isinstance(ratio, str):
        raise ValueError("profile first_frame_layout.aspect_ratio must be a string such as 9:16")
    parsed = parse_ratio(ratio)
    if abs(parsed - 9 / 16) > TOLERANCE:
        raise ValueError("first-frame aspect ratio must be 9:16")
    return parsed


def validate_image(path: Path, first_frame_ratio: float = 9 / 16) -> tuple[int, int]:
    """Return validated first-frame and image dimensions, or raise ValueError."""
    try:
        with Image.open(path) as image:
            width, height = image.size
    except OSError as error:
        raise ValueError(f"cannot open image: {error}") from error

    actual_ratio = width / height
    if abs(actual_ratio - first_frame_ratio) > TOLERANCE:
        raise ValueError(
            f"image ratio is {actual_ratio:.3f}:1, expected {first_frame_ratio:.3f}:1"
        )
    return width, height


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a first-frame image against a content-system configuration snapshot."
    )
    parser.add_argument("--profile", type=Path, required=True, help="content-system-config-snapshot.json")
    parser.add_argument("first_frames", metavar="FIRST_FRAME", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        first_frame_ratio = load_profile(args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(f"invalid profile: {error}")

    errors: list[str] = []
    for path in args.first_frames:
        try:
            width, height = validate_image(path, first_frame_ratio)
        except ValueError as error:
            errors.append(f"FAIL {path}: {error}")
        else:
            print(
                f"PASS {path}: first_frame={width}x{height}; "
                f"portrait={width}x{height} (ratio {first_frame_ratio:.3f}:1)"
            )
    if errors:
        print("First-frame validation failed:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
