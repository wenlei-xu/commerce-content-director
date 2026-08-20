#!/usr/bin/env python3
"""Legacy local composition utility; never use it for final-generation boards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps


def parse_profile(path: Path) -> tuple[int, int, tuple[int, int]]:
    profile = json.loads(path.read_text(encoding="utf-8"))
    storyboard = profile.get("storyboard") or {}
    columns, rows = storyboard.get("columns"), storyboard.get("rows")
    ratio = storyboard.get("panel_ratio")
    if not isinstance(columns, int) or columns < 1 or not isinstance(rows, int) or rows < 1 or not isinstance(ratio, str):
        raise ValueError("profile must define positive storyboard columns, rows, and panel_ratio")
    width, height = (int(part) for part in ratio.split(":", 1))
    if width <= 0 or height <= 0:
        raise ValueError("panel_ratio must be positive")
    panel_width = 1080
    return columns, rows, (panel_width, round(panel_width * height / width))


def load_panel(path: Path, panel_size: tuple[int, int]) -> Image.Image:
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
    except OSError as error:
        raise ValueError(f"cannot open {path}: {error}") from error

    ratio = image.width / image.height
    expected = panel_size[0] / panel_size[1]
    if abs(ratio - expected) > 0.01:
        raise ValueError(
            f"{path} is {image.width}x{image.height}, not a portrait 9:16 panel"
        )
    return ImageOps.fit(image, panel_size, method=Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a legacy local board using a content-system configuration profile."
    )
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("panels", metavar="PANEL", type=Path, nargs="+")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        columns, rows, panel_size = parse_profile(args.profile)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(f"invalid profile: {error}")
    if len(args.panels) != columns * rows:
        parser.error(f"profile requires exactly {columns * rows} panels")

    board = Image.new("RGB", (panel_size[0] * columns, panel_size[1] * rows))
    for index, path in enumerate(args.panels):
        x = (index % columns) * panel_size[0]
        y = (index // columns) * panel_size[1]
        board.paste(load_panel(path, panel_size), (x, y))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    board.save(args.out)
    print(f"Wrote {args.out}: {board.width}x{board.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
