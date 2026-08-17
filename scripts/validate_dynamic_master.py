#!/usr/bin/env python3
"""Validate the required artifact shape for dynamic-master-replacement packages."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from PIL import Image


REQUIRED_ROOT = (
    "dynamic-master-breakdown-report.md",
    "frame-time-map.csv",
    "subtitles.en.srt",
    "package.json",
    "quality-report.md",
    "references/product_six_view_2k.png",
    "plan/storyboard-spec.json",
)
REQUIRED_SEGMENT = (
    "replacement-dynamic-master.png",
    "replacement-master-image-prompt.md",
    "dynamic-master-review.md",
    "seeddance-prompt.md",
    "manifest.json",
    "assembly-manifest.json",
)
REQUIRED_MAP_COLUMNS = {
    "segment_id", "frame_id", "grid_order", "source_start", "source_end",
    "source_representative_time", "target_start", "target_end", "source_frame",
    "replacement_description", "transition_to_next",
}
TIMED_SCRIPT_COLUMNS = {"timed_script_ids", "timed_script_ranges", "panel_labels"}


def validate_tail_trim(root: Path, rows: list[dict[str, str]], errors: list[str]) -> None:
    """Validate an optional, terminal no-content tail trim."""
    trim_path = root / "evidence" / "tail-trim.json"
    if not trim_path.is_file():
        return
    try:
        trim = json.loads(trim_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"Invalid evidence/tail-trim.json: {error}")
        return
    required = {
        "status", "original_duration", "effective_source_start", "effective_source_end",
        "trimmed_source_start", "trimmed_source_end", "reason", "evidence_frame_paths",
    }
    if not isinstance(trim, dict) or not required.issubset(trim):
        errors.append("evidence/tail-trim.json is missing required fields")
        return
    if trim["status"] != "trimmed" or not isinstance(trim["reason"], str) or not trim["reason"].strip():
        errors.append("evidence/tail-trim.json must record a non-empty trimmed reason")
    if not isinstance(trim["evidence_frame_paths"], list) or not trim["evidence_frame_paths"]:
        errors.append("evidence/tail-trim.json must record evidence_frame_paths")
    try:
        original_end = float(trim["original_duration"])
        effective_start = float(trim["effective_source_start"])
        effective_end = float(trim["effective_source_end"])
        trimmed_start = float(trim["trimmed_source_start"])
        trimmed_end = float(trim["trimmed_source_end"])
    except (TypeError, ValueError):
        errors.append("evidence/tail-trim.json has invalid time values")
        return
    if not (
        0 <= effective_start <= effective_end < trimmed_end <= original_end + 0.01
        and abs(effective_end - trimmed_start) <= 0.01
    ):
        errors.append("evidence/tail-trim.json must describe one terminal range after effective content")
    for row in rows:
        try:
            source_end = float(row["source_end"])
        except (TypeError, ValueError):
            continue
        if source_end > trimmed_start + 0.01:
            errors.append(f"frame-time-map.csv retains trimmed tail frame {row['frame_id']}")


def validate_storyboard_spec(root: Path, errors: list[str]) -> dict | None:
    path = root / "plan" / "storyboard-spec.json"
    if not path.is_file():
        return None
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"Invalid plan/storyboard-spec.json: {error}")
        return None
    panel = spec.get("panel") if isinstance(spec, dict) else None
    grid = spec.get("batch_grid") if isinstance(spec, dict) else None
    if not isinstance(panel, dict) or not isinstance(grid, dict):
        errors.append("storyboard-spec.json must define panel and batch_grid")
        return None
    try:
        width, height = int(panel.get("width")), int(panel.get("height"))
        if width <= 0 or height <= 0 or abs(width / height - 9 / 16) > 0.001:
            errors.append("storyboard-spec.json panel must be a positive 9:16 canvas")
    except (TypeError, ValueError):
        errors.append("storyboard-spec.json panel must define numeric width and height")
    if grid.get("columns") != 2 or grid.get("reading_order") != "left-to-right, top-to-bottom":
        errors.append("storyboard-spec.json batch_grid must be two-column row-major")
    try:
        if not 0 <= float(panel.get("max_crop_fraction")) <= 0.10:
            errors.append("storyboard-spec.json max_crop_fraction must be between 0 and 0.10")
    except (TypeError, ValueError):
        errors.append("storyboard-spec.json must define numeric max_crop_fraction")
    return spec


def validate_reference_batches(root: Path, rows: list[dict[str, str]], errors: list[str], spec: dict | None) -> None:
    """Require complete fixed-six-frame batches for reference-video packages."""
    if not (root / "evidence" / "master-frames").is_dir():
        return

    plan_path = root / "plan" / "reference-batches.json"
    if not plan_path.is_file():
        errors.append("Reference-video package is missing plan/reference-batches.json")
        return
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        errors.append(f"Invalid plan/reference-batches.json: {error}")
        return

    batches = plan.get("batches") if isinstance(plan, dict) else None
    if not isinstance(batches, list) or not batches:
        errors.append("plan/reference-batches.json has no batches")
        return

    expected = {row["frame_id"] for row in rows}
    seen: set[str] = set()
    tail_batches: dict[str, list[list[str]]] = {}
    for index, batch in enumerate(batches, start=1):
        label = f"reference batch {index}"
        if not isinstance(batch, dict):
            errors.append(f"{label} is not an object")
            continue
        frame_ids = batch.get("frame_ids")
        mode = batch.get("mode")
        segment_id = batch.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id.strip():
            errors.append(f"{label} is missing segment_id")
            segment_id = "<missing>"
        if not isinstance(frame_ids, list) or not frame_ids:
            errors.append(f"{label} must contain frame_ids")
            continue
        if len(frame_ids) > 6:
            errors.append(f"{label} must not contain more than six frame_ids")
        elif len(frame_ids) < 6 and batch.get("tail_batch") is not True:
            errors.append(f"{label} with fewer than six frame_ids must set tail_batch to true")
        elif len(frame_ids) == 6 and batch.get("tail_batch") is True:
            errors.append(f"{label} must not mark a complete six-frame batch as tail_batch")
        if len(frame_ids) < 6:
            tail_batches.setdefault(segment_id, []).append(frame_ids)
        if mode not in {"generate", "preserve"}:
            errors.append(f"{label} mode must be generate or preserve")
        for frame_id in frame_ids:
            if frame_id not in expected:
                errors.append(f"{label} references unmapped frame_id {frame_id!r}")
            elif frame_id in seen:
                errors.append(f"frame_id {frame_id!r} appears in more than one reference batch")
            else:
                seen.add(frame_id)
        if not isinstance(batch.get("continuity_basis"), str) or not batch["continuity_basis"].strip():
            errors.append(f"{label} is missing continuity_basis")
        if mode == "generate":
            source_path: Path | None = None
            review_path: Path | None = None
            for key in ("source_contact_sheet", "replacement_contact_sheet", "review"):
                value = batch.get(key)
                if not isinstance(value, str) or not value:
                    errors.append(f"{label} is missing {key}")
                elif not (root / value).is_file():
                    errors.append(f"{label} asset is missing: {value}")
                elif key == "source_contact_sheet":
                    source_path = root / value
                elif key == "review":
                    review_path = root / value
            if batch.get("status") != "PASS":
                errors.append(f"{label} must record status PASS before delivery")
            if source_path is not None:
                batch_dir = source_path.parent
                for filename in ("batch-image-prompt.md", "batch-review.md", "manifest.json", "frame-crops.json"):
                    if not (batch_dir / filename).is_file():
                        errors.append(f"{label} is missing {batch_dir.name}/{filename}")
                manifest_path = batch_dir / "manifest.json"
                if manifest_path.is_file():
                    try:
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        if manifest.get("frame_ids") != frame_ids:
                            errors.append(f"{label} manifest frame_ids do not match the batch plan")
                    except json.JSONDecodeError as error:
                        errors.append(f"Invalid {batch_dir.name}/manifest.json: {error}")
            replacement_frames = batch.get("replacement_frames")
            if not isinstance(replacement_frames, list) or len(replacement_frames) != len(frame_ids):
                errors.append(f"{label} replacement_frames must map every frame_id exactly once")
            else:
                mapped_ids: list[str] = []
                for item in replacement_frames:
                    if not isinstance(item, dict) or not isinstance(item.get("frame_id"), str) or not isinstance(item.get("path"), str):
                        errors.append(f"{label} has an invalid replacement_frames entry")
                        continue
                    mapped_ids.append(item["frame_id"])
                    path = root / item["path"]
                    if not path.is_file():
                        errors.append(f"{label} replacement frame is missing: {item['path']}")
                    elif spec is not None:
                        try:
                            dimensions = Image.open(path).size
                            expected_dimensions = (int(spec["panel"]["width"]), int(spec["panel"]["height"]))
                            if dimensions != expected_dimensions:
                                errors.append(f"{label} replacement frame {item['frame_id']} is {dimensions}, expected {expected_dimensions}")
                        except OSError as error:
                            errors.append(f"{label} cannot open replacement frame {item['path']}: {error}")
                if mapped_ids != frame_ids:
                    errors.append(f"{label} replacement_frames must retain frame_ids order")
            if review_path is not None and review_path.is_file():
                review_text = review_path.read_text(encoding="utf-8")
                if "PASS" not in review_text.upper():
                    errors.append(f"{label} review does not record PASS")
                missing_review_ids = [frame_id for frame_id in frame_ids if frame_id not in review_text]
                if missing_review_ids:
                    errors.append(
                        f"{label} review lacks per-frame evidence for: "
                        + ", ".join(missing_review_ids)
                    )
        elif not isinstance(batch.get("preserve_reason"), str) or not batch["preserve_reason"].strip():
            errors.append(f"{label} preserve batch is missing preserve_reason")
    missing = expected - seen
    if missing:
        errors.append(f"reference batches do not cover mapped frames: {', '.join(sorted(missing))}")
    for segment_id, tails in tail_batches.items():
        if len(tails) > 1:
            errors.append(f"{segment_id} has more than one fixed-six tail_batch")
            continue
        ordered_rows = sorted(
            (row for row in rows if row["segment_id"] == segment_id),
            key=lambda row: float(row["grid_order"]),
        )
        expected_tail = [row["frame_id"] for row in ordered_rows[-len(tails[0]):]]
        if tails[0] != expected_tail:
            errors.append(f"{segment_id} tail_batch must cover the final mapped frames in order")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_dynamic_master.py <package-dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    errors: list[str] = []
    for relative in REQUIRED_ROOT:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")
    package_path = root / "package.json"
    package: dict = {}
    if package_path.is_file():
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"Invalid package.json: {error}")
    if package and package.get("generation_strategy") != "dynamic-master-replacement":
        errors.append("package.json generation_strategy must be dynamic-master-replacement")

    map_path = root / "frame-time-map.csv"
    rows: list[dict[str, str]] = []
    if map_path.is_file():
        with map_path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames or not REQUIRED_MAP_COLUMNS.issubset(reader.fieldnames):
                errors.append("frame-time-map.csv is missing required columns")
            else:
                rows = list(reader)
                if not rows:
                    errors.append("frame-time-map.csv has no frame rows")

    timed_script_path = root / "plan" / "timed-script.json"
    if timed_script_path.is_file() and map_path.is_file():
        with map_path.open(encoding="utf-8-sig", newline="") as file:
            columns = set(csv.DictReader(file).fieldnames or [])
        if not TIMED_SCRIPT_COLUMNS.issubset(columns):
            errors.append("frame-time-map.csv is missing timed-script mapping columns")

    spec = validate_storyboard_spec(root, errors)
    if rows:
        validate_tail_trim(root, rows, errors)
        validate_reference_batches(root, rows, errors, spec)

    segments_root = root / "segments"
    segments = sorted(path for path in segments_root.glob("Segment-*") if path.is_dir())
    if not segments:
        errors.append("No Segment-* directories found")
    for segment in segments:
        for relative in REQUIRED_SEGMENT:
            if not (segment / relative).is_file():
                errors.append(f"Missing {segment.name}/{relative}")
        review = segment / "dynamic-master-review.md"
        if review.is_file() and "PASS" not in review.read_text(encoding="utf-8").upper():
            errors.append(f"{segment.name}/dynamic-master-review.md does not record PASS")
        if review.is_file() and rows:
            review_text = review.read_text(encoding="utf-8")
            expected_frame_ids = [row["frame_id"] for row in rows if row["segment_id"] == segment.name]
            missing_review_ids = [frame_id for frame_id in expected_frame_ids if frame_id not in review_text]
            if missing_review_ids:
                errors.append(
                    f"{segment.name}/dynamic-master-review.md lacks per-frame evidence for: "
                    + ", ".join(missing_review_ids)
                )
        manifest = segment / "manifest.json"
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                frames = data.get("replacement_frames", [])
                if not frames:
                    errors.append(f"{segment.name}/manifest.json has no replacement_frames")
            except json.JSONDecodeError as error:
                errors.append(f"Invalid {segment.name}/manifest.json: {error}")
        assembly = segment / "assembly-manifest.json"
        if assembly.is_file() and rows and spec is not None:
            try:
                data = json.loads(assembly.read_text(encoding="utf-8"))
                expected_frame_ids = [row["frame_id"] for row in sorted(
                    (row for row in rows if row["segment_id"] == segment.name),
                    key=lambda row: float(row["grid_order"]),
                )]
                if data.get("frame_ids") != expected_frame_ids:
                    errors.append(f"{segment.name}/assembly-manifest.json frame_ids do not match time map")
                panel = data.get("panel", {})
                expected_dimensions = (int(spec["panel"]["width"]), int(spec["panel"]["height"]))
                if (panel.get("width"), panel.get("height")) != expected_dimensions:
                    errors.append(f"{segment.name}/assembly-manifest.json panel does not match storyboard spec")
            except json.JSONDecodeError as error:
                errors.append(f"Invalid {segment.name}/assembly-manifest.json: {error}")
    if rows and segments:
        mapped = {row["segment_id"] for row in rows}
        for segment in segments:
            if segment.name not in mapped:
                errors.append(f"frame-time-map.csv has no rows for {segment.name}")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Dynamic master package validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
