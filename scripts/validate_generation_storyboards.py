#!/usr/bin/env python3
"""Validate portrait-panel Flow2API storyboard boards before Feishu upload."""

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
        raise ValueError("panel_ratio must be positive")
    return ratio


def load_profile(path: Path) -> tuple[int, int, float]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    storyboard = profile.get("storyboard") or {}
    columns = storyboard.get("columns")
    rows = storyboard.get("rows")
    ratio = storyboard.get("panel_ratio")
    if not isinstance(columns, int) or columns < 1 or not isinstance(rows, int) or rows < 1:
        raise ValueError("profile storyboard columns and rows must be positive integers")
    if not isinstance(ratio, str):
        raise ValueError("profile storyboard panel_ratio must be a string such as 9:16")
    return columns, rows, parse_ratio(ratio)


def validate_image(path: Path, columns: int = 2, rows: int = 2, panel_ratio: float = 9 / 16) -> tuple[int, int, int, int]:
    """Return validated board and panel dimensions, or raise ValueError."""
    try:
        with Image.open(path) as image:
            width, height = image.size
    except OSError as error:
        raise ValueError(f"cannot open image: {error}") from error

    if width % columns or height % rows:
        raise ValueError(
            f"{width}x{height} cannot form an equal {columns}x{rows} panel grid"
        )
    panel_width, panel_height = width // columns, height // rows
    actual_ratio = panel_width / panel_height
    if abs(actual_ratio - panel_ratio) > TOLERANCE:
        raise ValueError(
            f"panel ratio is {actual_ratio:.3f}:1, expected {panel_ratio:.3f}:1"
        )
    return width, height, panel_width, panel_height


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a storyboard board against a content-system configuration snapshot."
    )
    parser.add_argument("--profile", type=Path, required=True, help="content-system-config-snapshot.json")
    parser.add_argument("boards", metavar="BOARD", type=Path, nargs="+")
    args = parser.parse_args()
    try:
        columns, rows, panel_ratio = load_profile(args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(f"invalid profile: {error}")

    errors: list[str] = []
    for path in args.boards:
        try:
            width, height, panel_width, panel_height = validate_image(path, columns, rows, panel_ratio)
        except ValueError as error:
            errors.append(f"FAIL {path}: {error}")
        else:
            print(
                f"PASS {path}: board={width}x{height}; "
                f"panels={columns * rows} x {panel_width}x{panel_height} (ratio {panel_ratio:.3f}:1)"
            )
    if errors:
        print("Generation storyboard validation failed:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
