#!/usr/bin/env python3
"""Normalize a generated six-view board to an exact 2048x2048 white PNG."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps


SIZE = (2048, 2048)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if not args.image.is_file():
        raise SystemExit(f"Image not found: {args.image}")
    with Image.open(args.image) as source:
        source = source.convert("RGB")
        fitted = ImageOps.contain(source, SIZE, method=Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", SIZE, "white")
        canvas.paste(fitted, ((SIZE[0] - fitted.width) // 2, (SIZE[1] - fitted.height) // 2))
        args.out.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(args.out, format="PNG", optimize=True)
    print(f"Normalized six-view: {args.out} ({SIZE[0]}x{SIZE[1]})")


if __name__ == "__main__":
    main()
