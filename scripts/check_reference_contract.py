#!/usr/bin/env python3
"""Check active references for schema, model, and legacy-reference drift."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEPRECATED_MARKERS = (
    "Seeddance",
    "seeddance",
    "六视图",
    "six-view",
    "six_view",
    "Banana Pro",
    "gemini-3.0-pro-image-landscape",
    "omni_portrait",
)


def walk_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)


def schema_labels(schema: dict) -> set[str]:
    labels = set()
    for value in walk_strings(schema):
        if any("\u4e00" <= char <= "\u9fff" for char in value):
            labels.add(value)
    return labels


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()

    root = args.skill_dir.resolve()
    schema_path = root / "config" / "base-schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    labels = schema_labels(schema)
    technical_ids = {
        value
        for value in walk_strings(schema)
        if re.search(r"(?:tbl|app)[A-Za-z0-9]+", value)
    }
    active_files = [
        path
        for path in (root / "references").rglob("*.md")
        if "legacy" not in path.parts
    ]
    errors: list[str] = []
    for path in active_files:
        text = path.read_text(encoding="utf-8")
        for marker in DEPRECATED_MARKERS:
            if marker in text:
                errors.append(f"{path}: deprecated marker {marker!r}")
        for value in technical_ids:
            if value in text:
                errors.append(f"{path}: copied schema technical ID {value!r}")
        for match in re.finditer(r"`([^`]+)`", text):
            if match.group(1) in labels:
                errors.append(
                    f"{path}: copied localized schema label {match.group(1)!r}; use its logical key"
                )

    if errors:
        print("\n".join(errors))
        return 1
    print(f"reference contract check passed ({len(active_files)} active references)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
