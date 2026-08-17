#!/usr/bin/env python3
"""Deterministically assemble canonical RF frames into each segment master without stretching."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from PIL import Image


def choose_grid(count: int, columns: int) -> tuple[int, int]:
    """Return the fixed-six-column chronological grid with terminal blanks only."""
    if count <= 0:
        raise ValueError("count must be positive")
    if columns <= 0:
        raise ValueError("columns must be positive")
    return columns, math.ceil(count / columns)


def read_map(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"segment_id", "frame_id", "grid_order"}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit("frame-time-map.csv must contain segment_id, frame_id and grid_order")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    args = parser.parse_args()
    root = args.package_dir
    spec = json.loads((root / "plan" / "storyboard-spec.json").read_text(encoding="utf-8"))
    plan = json.loads((root / "plan" / "reference-batches.json").read_text(encoding="utf-8"))
    panel = spec["panel"]
    master = spec.get("master_grid", {})
    panel_w, panel_h = int(panel["width"]), int(panel["height"])
    gap = int(master.get("gap_px", 0))
    master_columns = int(master.get("columns", 6))
    allow_terminal_empty_cells = bool(master.get("allow_terminal_empty_cells", True))
    if panel_w <= 0 or panel_h <= 0 or gap < 0 or master_columns < 1:
        raise SystemExit("Invalid storyboard panel or master-grid dimensions")
    rows = read_map(root / "frame-time-map.csv")
    by_segment: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_segment.setdefault(row["segment_id"], []).append(row)
    batches = plan.get("batches", [])
    for segment_id, segment_rows in by_segment.items():
        expected = [row["frame_id"] for row in sorted(segment_rows, key=lambda row: float(row["grid_order"]))]
        located: dict[str, Path] = {}
        for batch in batches:
            if batch.get("segment_id") != segment_id:
                continue
            if batch.get("status") != "PASS":
                raise SystemExit(f"{segment_id}/{batch.get('id', '<unknown>')} is not PASS")
            frames = batch.get("replacement_frames")
            if not isinstance(frames, list):
                raise SystemExit(f"{segment_id}/{batch.get('id', '<unknown>')} is missing replacement_frames")
            for item in frames:
                if not isinstance(item, dict) or not isinstance(item.get("frame_id"), str) or not isinstance(item.get("path"), str):
                    raise SystemExit(f"{segment_id}/{batch.get('id', '<unknown>')} has invalid replacement_frames")
                frame_id, path = item["frame_id"], root / item["path"]
                if frame_id in located:
                    raise SystemExit(f"Duplicate replacement frame: {frame_id}")
                if not path.is_file():
                    raise SystemExit(f"Missing replacement frame: {item['path']}")
                image = Image.open(path)
                if image.size != (panel_w, panel_h):
                    raise SystemExit(f"{item['path']} is {image.size}; expected {(panel_w, panel_h)}. Refuse to stretch.")
                located[frame_id] = path
        if list(located) and set(located) != set(expected):
            missing = sorted(set(expected) - set(located))
            extra = sorted(set(located) - set(expected))
            raise SystemExit(f"{segment_id} replacement-frame mismatch; missing={missing}, extra={extra}")
        if not located:
            raise SystemExit(f"{segment_id} has no replacement frames to assemble")
        ordered = [Image.open(located[frame_id]).convert("RGB") for frame_id in expected]
        columns, grid_rows = choose_grid(len(ordered), master_columns)
        capacity = columns * grid_rows
        if capacity > len(ordered) and not allow_terminal_empty_cells:
            raise SystemExit(f"{segment_id} needs {capacity - len(ordered)} terminal empty cells, but storyboard-spec forbids them")
        canvas = Image.new("RGB", (columns * panel_w + (columns - 1) * gap, grid_rows * panel_h + (grid_rows - 1) * gap), "white")
        for index, image in enumerate(ordered):
            row, column = divmod(index, columns)
            canvas.paste(image, (column * (panel_w + gap), row * (panel_h + gap)))
        segment_dir = root / "segments" / segment_id
        segment_dir.mkdir(parents=True, exist_ok=True)
        output = segment_dir / "replacement-dynamic-master.png"
        canvas.save(output)
        empty_cells = [
            {"row": (index // columns) + 1, "column": (index % columns) + 1, "fill": "white"}
            for index in range(len(ordered), capacity)
        ]
        manifest = {
            "strategy": "canonical-rf-no-stretch-v1",
            "frame_ids": expected,
            "panel": {"width": panel_w, "height": panel_h, "aspect_ratio": "9:16"},
            "grid": {"columns": columns, "rows": grid_rows, "gap_px": gap, "reading_order": "left-to-right, top-to-bottom", "empty_cells": empty_cells},
            "output": "replacement-dynamic-master.png",
            "output_size": {"width": canvas.width, "height": canvas.height},
        }
        (segment_dir / "assembly-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Assembled {segment_id}: {len(ordered)} frames, {columns}x{grid_rows}, {canvas.size[0]}x{canvas.size[1]}")


if __name__ == "__main__":
    main()
