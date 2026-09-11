#!/usr/bin/env python3
"""Detect repeated creative solutions across Markdown creation workbooks."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any

from workbook import load_and_validate


def _compact(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def creative_signature(workbook: dict[str, Any]) -> tuple[Any, ...]:
    metadata = workbook.get("metadata") or {}
    segments = workbook.get("segments") or []
    visuals = tuple(_compact(segment.get("visual_event")) for segment in segments)
    return (
        _compact(metadata.get("内容角度") or metadata.get("创意角度")),
        _compact(metadata.get("核心创意")),
        visuals,
        _compact(segments[-1].get("continuity") if segments else ""),
    )


def validate(
    paths: list[Path],
    *,
    allow_shared_structure: bool = False,
    reason: str = "",
) -> dict[str, Any]:
    loaded: list[tuple[Path, dict[str, Any]]] = []
    errors: list[dict[str, str]] = []
    for path in paths:
        try:
            loaded.append((path, load_and_validate(path)))
        except (OSError, ValueError) as exc:
            errors.append({"code": "INVALID_WORKBOOK", "path": str(path), "detail": str(exc)})
    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for path, workbook in loaded:
        groups[creative_signature(workbook)].append(str(path))
    collisions = [members for members in groups.values() if len(members) > 1]
    if collisions and not allow_shared_structure:
        for members in collisions:
            errors.append({
                "code": "REPEATED_CREATIVE_STRUCTURE",
                "path": ", ".join(members),
                "detail": "开场、视觉事件和收束方式重复；请重新设计，或明确记录复用理由",
            })
    if collisions and allow_shared_structure and not reason.strip():
        errors.append({
            "code": "MISSING_SHARED_STRUCTURE_REASON",
            "path": "batch",
            "detail": "允许复用创意结构时必须提供 --reason",
        })
    return {
        "schema": "commerce-batch-creativity-report-v2",
        "workbook_count": len(loaded),
        "collision_count": len(collisions),
        "collisions": collisions,
        "allow_shared_structure": allow_shared_structure,
        "reason": reason.strip(),
        "ok": not errors,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbooks", type=Path, nargs="+")
    parser.add_argument("--allow-shared-structure", action="store_true")
    parser.add_argument("--reason", default="")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    report = validate(
        args.workbooks,
        allow_shared_structure=args.allow_shared_structure,
        reason=args.reason,
    )
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output if args.as_json else ("PASS" if report["ok"] else "FAIL"))
    if not report["ok"] and not args.as_json:
        print(output)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
