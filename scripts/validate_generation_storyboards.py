#!/usr/bin/env python3
"""Validate portrait-panel Flow2API storyboard boards before Feishu upload."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


PANEL_RATIO = 9 / 16
GRID_COLUMNS = 2
GRID_ROWS = 2
TOLERANCE = 0.01


def validate_image(path: Path) -> tuple[int, int, int, int]:
    """Return validated board and panel dimensions, or raise ValueError."""
    try:
        with Image.open(path) as image:
            width, height = image.size
    except OSError as error:
        raise ValueError(f"cannot open image: {error}") from error

    if width % GRID_COLUMNS or height % GRID_ROWS:
        raise ValueError(
            f"{width}x{height} cannot form an equal {GRID_COLUMNS}x{GRID_ROWS} panel grid"
        )
    panel_width, panel_height = width // GRID_COLUMNS, height // GRID_ROWS
    panel_ratio = panel_width / panel_height
    if abs(panel_ratio - PANEL_RATIO) > TOLERANCE:
        raise ValueError(
            f"panel ratio is {panel_ratio:.3f}:1, expected portrait 9:16 ({PANEL_RATIO:.3f}:1)"
        )
    return width, height, panel_width, panel_height


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a 2x2 board with four equal portrait 9:16 panels."
    )
    parser.add_argument("boards", metavar="BOARD", type=Path, nargs="+")
    args = parser.parse_args()

    errors: list[str] = []
    for path in args.boards:
        try:
            width, height, panel_width, panel_height = validate_image(path)
        except ValueError as error:
            errors.append(f"FAIL {path}: {error}")
        else:
            print(
                f"PASS {path}: board={width}x{height}; "
                f"panels=4 x {panel_width}x{panel_height} (portrait 9:16)"
            )
    if errors:
        print("Generation storyboard validation failed:")
        print("\n".join(errors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
