#!/usr/bin/env python3
"""Build balanced storyboard masters from accepted current-run batch sheets."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image


PANEL_RATIO = 9 / 16


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def batch_items(value):
    return value["batches"] if isinstance(value, dict) and "batches" in value else value


def balanced_groups(items: list[dict], max_panels: int) -> list[list[dict]]:
    count = len(items)
    master_count = math.ceil(count / max_panels)
    base, remainder = divmod(count, master_count)
    groups, cursor = [], 0
    for index in range(master_count):
        size = base + (1 if index < remainder else 0)
        groups.append(items[cursor : cursor + size])
        cursor += size
    return groups


def grid_shape(frame_count: int) -> tuple[int, int]:
    return (3, 2) if frame_count == 6 else (frame_count, 1)


def load_panels(run: Path, batch: dict, tolerance: float) -> list[tuple[str, Image.Image, str]]:
    batch_id = batch["id"]
    rf_ids = batch["rf_ids"]
    batch_dir = run / "batches" / batch_id
    manifest = read_json(batch_dir / "manifest.json")
    if manifest.get("status") != "PASS":
        raise ValueError(f"{batch_id}: batch manifest is not PASS")

    cols, rows = grid_shape(len(rf_ids))
    image_path = batch_dir / "replacement-contact-sheet.png"
    image = Image.open(image_path).convert("RGB")
    expected_ratio = (cols * 9) / (rows * 16)
    actual_ratio = image.width / image.height
    drift = abs(actual_ratio / expected_ratio - 1)
    if drift > tolerance:
        raise ValueError(
            f"{batch_id}: replacement geometry drift {drift:.1%} exceeds {tolerance:.1%}; regenerate before assembly"
        )

    panels = []
    for index, rf_id in enumerate(rf_ids):
        row, col = divmod(index, cols)
        left = round(col * image.width / cols)
        right = round((col + 1) * image.width / cols)
        top = round(row * image.height / rows)
        bottom = round((row + 1) * image.height / rows)
        panel = image.crop((left, top, right, bottom))
        panel_ratio = panel.width / panel.height
        panel_drift = abs(panel_ratio / PANEL_RATIO - 1)
        if panel_drift > tolerance:
            raise ValueError(f"{batch_id}/{rf_id}: panel geometry drift {panel_drift:.1%} exceeds {tolerance:.1%}")
        panels.append((rf_id, panel.resize((720, 1280), Image.Resampling.LANCZOS), batch_id))
    image.close()
    return panels


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-panels", type=int, default=15)
    parser.add_argument("--columns", type=int, default=5)
    parser.add_argument("--geometry-tolerance", type=float, default=0.05)
    args = parser.parse_args()

    if args.max_panels < 1 or args.columns < 1:
        raise SystemExit("--max-panels and --columns must be positive")
    run = args.run.resolve()
    out = (args.out or run / "masters").resolve()
    planned_batches = batch_items(read_json(run / "plan" / "reference-batches.json"))
    all_panels: list[tuple[str, Image.Image, str]] = []
    for batch in planned_batches:
        all_panels.extend(load_panels(run, batch, args.geometry_tolerance))

    expected_ids = [f"RF{index:02d}" for index in range(1, len(all_panels) + 1)]
    actual_ids = [item[0] for item in all_panels]
    if actual_ids != expected_ids:
        raise SystemExit("RF IDs must be exactly chronological RF01...RFN with no duplicates or omissions")

    groups = balanced_groups(all_panels, args.max_panels)
    out.mkdir(parents=True, exist_ok=True)
    plan = {"valid_rf_count": len(all_panels), "max_panels_per_master": args.max_panels, "masters": []}
    for number, group in enumerate(groups, start=1):
        folder = out / f"Master-{number:02d}"
        folder.mkdir(parents=True, exist_ok=True)
        rows = math.ceil(len(group) / args.columns)
        canvas = Image.new("RGB", (args.columns * 720, rows * 1280), "white")
        for index, (_, panel, _) in enumerate(group):
            canvas.paste(panel, ((index % args.columns) * 720, (index // args.columns) * 1280))
        filename = "master-contact-sheet.png"
        canvas.save(folder / filename)
        rf_ids = [item[0] for item in group]
        batch_ids = list(dict.fromkeys(item[2] for item in group))
        manifest = {"master": number, "rf_ids": rf_ids, "count": len(group), "source_batches": batch_ids}
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (folder / "master-review.md").write_text(
            f"# Master review — PASS\n\nChronological current-run RF coverage: {rf_ids[0]}–{rf_ids[-1]} ({len(group)} frames). "
            f"Source batches: {', '.join(batch_ids)}. No RF is duplicated or omitted.\n",
            encoding="utf-8",
        )
        plan["masters"].append(manifest | {"path": (folder / filename).relative_to(run).as_posix()})

    (run / "plan" / "master-groups.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
