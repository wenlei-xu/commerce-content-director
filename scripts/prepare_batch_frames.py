#!/usr/bin/env python3
"""Split a reviewed batch grid into canonical storyboard frames without stretching."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageOps


def load_spec(batch_dir: Path) -> dict:
    for parent in (batch_dir, *batch_dir.parents):
        candidate = parent / "plan" / "storyboard-spec.json"
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8"))
    raise SystemExit("Cannot find plan/storyboard-spec.json above batch directory")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("batch_dir", type=Path)
    parser.add_argument("--frame-ids", required=True, help="Comma-separated RF IDs in grid reading order")
    parser.add_argument("--contact-sheet", type=Path, help="Defaults to batch_dir/replacement-contact-sheet.png")
    parser.add_argument("--gutter-px", type=int, help="Overrides the spec grid gutter")
    args = parser.parse_args()

    frame_ids = [value.strip() for value in args.frame_ids.split(",") if value.strip()]
    if not frame_ids or len(frame_ids) > 6:
        raise SystemExit("--frame-ids must contain one to six IDs")
    spec = load_spec(args.batch_dir)
    panel = spec.get("panel", {})
    grid = spec.get("batch_grid", {})
    width, height = int(panel.get("width", 0)), int(panel.get("height", 0))
    columns = int(grid.get("columns", 0))
    max_crop = float(panel.get("max_crop_fraction", 0.0))
    gutter = args.gutter_px if args.gutter_px is not None else int(grid.get("gutter_px", 0))
    if width <= 0 or height <= 0 or columns != 2 or gutter < 0:
        raise SystemExit("storyboard-spec.json must define positive panel dimensions, two batch columns, and a non-negative gutter")
    rows = math.ceil(len(frame_ids) / columns)
    sheet_path = args.contact_sheet or args.batch_dir / "replacement-contact-sheet.png"
    if not sheet_path.is_file():
        raise SystemExit(f"Missing replacement contact sheet: {sheet_path}")
    sheet = Image.open(sheet_path).convert("RGB")
    cell_width = (sheet.width - gutter * (columns - 1)) / columns
    cell_height = (sheet.height - gutter * (rows - 1)) / rows
    if cell_width <= 0 or cell_height <= 0:
        raise SystemExit("Contact sheet dimensions are incompatible with the declared grid")

    target_aspect = width / height
    source_aspect = cell_width / cell_height
    retained_fraction = min(target_aspect / source_aspect, source_aspect / target_aspect)
    crop_fraction = 1 - retained_fraction
    if crop_fraction > max_crop + 1e-6:
        raise SystemExit(
            f"Batch grid cell aspect {source_aspect:.4f} requires {crop_fraction:.1%} crop; "
            f"spec allows at most {max_crop:.1%}. Regenerate this fixed batch."
        )

    output_dir = args.batch_dir / "replacement-frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    crops = []
    for index, frame_id in enumerate(frame_ids):
        row, column = divmod(index, columns)
        left = round(column * (cell_width + gutter))
        top = round(row * (cell_height + gutter))
        right = round(left + cell_width)
        bottom = round(top + cell_height)
        source = sheet.crop((left, top, right, bottom))
        # ImageOps.fit crops symmetrically but never distorts pixels.
        normalized = ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        destination = output_dir / f"{frame_id}.png"
        normalized.save(destination)
        crops.append({
            "frame_id": frame_id,
            "source_box": [left, top, right, bottom],
            "source_aspect_ratio": round(source_aspect, 6),
            "target_aspect_ratio": round(target_aspect, 6),
            "crop_fraction": round(crop_fraction, 6),
            "output": str(destination.relative_to(args.batch_dir.parent.parent.parent.parent)),
        })
    (args.batch_dir / "frame-crops.json").write_text(
        json.dumps({"contact_sheet": str(sheet_path), "frame_ids": frame_ids, "crops": crops}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(frame_ids)} canonical frames in {output_dir}")


if __name__ == "__main__":
    main()
