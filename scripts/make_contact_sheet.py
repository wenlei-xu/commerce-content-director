#!/usr/bin/env python3
"""Create labeled evidence sheets or plain source contact sheets from frames."""

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frame_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--thumb-width", type=int, default=360)
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Create a zero-gutter sheet without frame labels or borders for image generation input.",
    )
    args = parser.parse_args()

    frames = sorted(args.frame_dir.glob("*.jpg")) + sorted(args.frame_dir.glob("*.png"))
    if not frames:
        raise SystemExit(f"No frames found in {args.frame_dir}")
    if args.cols <= 0:
        raise SystemExit("--cols must be positive")

    thumbs = []
    for idx, path in enumerate(frames, start=1):
        img = Image.open(path).convert("RGB")
        w, h = img.size
        new_h = max(1, int(h * args.thumb_width / w))
        img = img.resize((args.thumb_width, new_h))
        thumbs.append((idx, path.name, img))

    label_h = 0 if args.plain else 30
    cell_w = args.thumb_width
    cell_h = max(img.height for _, _, img in thumbs) + label_h
    rows = math.ceil(len(thumbs) / args.cols)
    sheet = Image.new("RGB", (cell_w * args.cols, cell_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for i, (idx, name, img) in enumerate(thumbs):
        row, col = divmod(i, args.cols)
        x = col * cell_w
        y = row * cell_h
        sheet.paste(img, (x, y + label_h))
        if not args.plain:
            draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(180, 180, 180))
            draw.text((x + 6, y + 8), f"{idx:02d} {name}", fill=(0, 0, 0), font=font)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.out)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
