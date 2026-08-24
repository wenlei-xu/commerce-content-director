#!/usr/bin/env python3
"""Validate the two reusable outputs of a short-video breakdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SUMMARY_LABELS = ("适合：", "结构：", "主要证明：", "不适合：")
SHOT_HEADERS = ("镜头", "时间", "叙事任务", "原内容", "保留机制", "新内容模板")


def validate(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    summary = str(record.get("可参考的叙事模板", "")).strip()
    for label in SUMMARY_LABELS:
        if label not in summary:
            errors.append({"code": "SUMMARY_LABEL_MISSING", "field": "可参考的叙事模板", "message": f"缺少 {label}"})
    template = str(record.get("逐镜头复刻模板", "")).strip()
    if not template:
        errors.append({"code": "MISSING_SHOT_TEMPLATE", "field": "逐镜头复刻模板", "message": "可复刻拆解必须有逐镜头模板"})
    else:
        lines = [line.strip() for line in template.splitlines() if line.strip()]
        if not lines or any(header not in lines[0] for header in SHOT_HEADERS):
            errors.append({"code": "INVALID_SHOT_HEADER", "field": "逐镜头复刻模板", "message": "首行必须包含六列标准表头"})
        rows = [line for line in lines[2:] if line.startswith("|")]
        if not rows:
            errors.append({"code": "MISSING_SHOT_ROWS", "field": "逐镜头复刻模板", "message": "至少需要一条镜头映射"})
        for index, row in enumerate(rows, 1):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) != 6 or any(not cell for cell in cells):
                errors.append({"code": "INVALID_SHOT_ROW", "field": f"逐镜头复刻模板[{index}]", "message": "每行必须有六个非空单元格"})
            elif not re.fullmatch(r"S\d{2,}", cells[0]):
                errors.append({"code": "INVALID_SHOT_ID", "field": f"逐镜头复刻模板[{index}]", "message": "镜头 ID 必须形如 S01"})
    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {"ok": False, "errors": [{"code": "INVALID_JSON", "field": "record", "message": str(exc)}]}
    else:
        report = validate(data)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
