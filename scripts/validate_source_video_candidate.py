#!/usr/bin/env python3
"""Validate the source-video gate before expensive breakdown work begins."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DECISIONS = {"有效", "无效", "待人工核对"}
CHECKS = (
    "playable",
    "nonblank_visual",
    "duration_consistent",
    "content_matches_metadata",
    "not_duplicate_wrong_attachment",
    "has_analyzable_evidence",
)
REASON_CODES = {
    "unreadable_media",
    "blank_or_black",
    "duration_mismatch",
    "content_mismatch",
    "duplicate_wrong_attachment",
    "insufficient_evidence",
    "other",
}


def validate(report: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not str(report.get("source_record_id") or "").strip():
        errors.append({"code": "MISSING_SOURCE_RECORD", "field": "source_record_id", "message": "必须关联来源记录"})
    decision = report.get("decision")
    if decision not in DECISIONS:
        errors.append({"code": "INVALID_DECISION", "field": "decision", "message": "必须为有效、无效或待人工核对"})
    checks = report.get("checks")
    if not isinstance(checks, dict):
        errors.append({"code": "MISSING_CHECKS", "field": "checks", "message": "必须提供全部有效性检查"})
        checks = {}
    for key in CHECKS:
        if not isinstance(checks.get(key), bool):
            errors.append({"code": "INVALID_CHECK", "field": f"checks.{key}", "message": "必须明确为 true 或 false"})
    evidence = report.get("evidence")
    if not isinstance(evidence, dict):
        errors.append({"code": "MISSING_EVIDENCE", "field": "evidence", "message": "必须提供预检证据"})
    else:
        if not isinstance(evidence.get("sample_frame_paths"), list) or not evidence["sample_frame_paths"]:
            errors.append({"code": "MISSING_SAMPLE_FRAMES", "field": "evidence.sample_frame_paths", "message": "至少需要一张预检帧"})
        if not str(evidence.get("model_visual_summary") or "").strip():
            errors.append({"code": "MISSING_VISUAL_SUMMARY", "field": "evidence.model_visual_summary", "message": "必须记录模型视觉结论"})
    reason_codes = report.get("reason_codes") or []
    if not isinstance(reason_codes, list) or any(code not in REASON_CODES for code in reason_codes):
        errors.append({"code": "INVALID_REASON_CODES", "field": "reason_codes", "message": "包含未知原因码"})
    if decision == "有效":
        failed = [key for key in CHECKS if checks.get(key) is not True]
        if failed:
            errors.append({"code": "VALID_WITH_FAILED_CHECKS", "field": "checks", "message": "有效视频的阻断检查必须全部通过"})
        if reason_codes:
            errors.append({"code": "VALID_WITH_REASONS", "field": "reason_codes", "message": "有效视频不得携带失败原因"})
    elif decision in {"无效", "待人工核对"} and not reason_codes:
        errors.append({"code": "MISSING_REASON", "field": "reason_codes", "message": "无效或待核对必须记录原因"})
    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"ok": False, "errors": [{"code": "INVALID_JSON", "field": "report", "message": str(exc)}]}
    else:
        result = validate(report)
    print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
