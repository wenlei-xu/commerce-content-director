#!/usr/bin/env python3
"""Compose four accepted portrait keyframes into a zero-gutter 2x2 board."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


PANEL_SIZE = (1080, 1920)


def load_panel(path: Path) -> Image.Image:
    try:
        with Image.open(path) as source:
            image = source.convert("RGB")
    except OSError as error:
        raise ValueError(f"cannot open {path}: {error}") from error

    ratio = image.width / image.height
    expected = PANEL_SIZE[0] / PANEL_SIZE[1]
    if abs(ratio - expected) > 0.01:
        raise ValueError(
            f"{path} is {image.width}x{image.height}, not a portrait 9:16 panel"
        )
    return ImageOps.fit(image, PANEL_SIZE, method=Image.Resampling.LANCZOS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a 2x2 zero-gutter final-generation storyboard board."
    )
    parser.add_argument("panels", metavar="PANEL", type=Path, nargs=4)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    board = Image.new("RGB", (PANEL_SIZE[0] * 2, PANEL_SIZE[1] * 2))
    for index, path in enumerate(args.panels):
        x = (index % 2) * PANEL_SIZE[0]
        y = (index // 2) * PANEL_SIZE[1]
        board.paste(load_panel(path), (x, y))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    board.save(args.out)
    print(f"Wrote {args.out}: {board.width}x{board.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
