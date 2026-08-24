#!/usr/bin/env python3
"""Validate the two reusable outputs of a short-video breakdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SUMMARY_LABELS = ("适合：", "结构：", "主要证明：", "不适合：")
SEGMENT_HEADERS = ("段落", "时间", "叙事任务", "参考帧", "原内容", "保留机制", "新内容模板")
CAPTION_LABELS = ("类型：", "基础样式：", "强调对象：", "强调方式：", "出现节奏：")


def attachment_names(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    names: set[str] = set()
    for item in value:
        if isinstance(item, str) and item.strip():
            names.add(item.strip())
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("file_name") or "").strip()
            if name:
                names.add(name)
    return names


def validate(record: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    summary = str(record.get("可参考的叙事模板", "")).strip()
    for label in SUMMARY_LABELS:
        if label not in summary:
            errors.append({"code": "SUMMARY_LABEL_MISSING", "field": "可参考的叙事模板", "message": f"缺少 {label}"})
    caption_template = str(record.get("字幕表达模板", "")).strip()
    if not caption_template:
        errors.append({"code": "MISSING_CAPTION_TEMPLATE", "field": "字幕表达模板", "message": "必须记录字幕呈现方式或明确写无字幕"})
    elif "类型：无字幕" not in caption_template:
        for label in CAPTION_LABELS:
            if label not in caption_template:
                errors.append({"code": "CAPTION_LABEL_MISSING", "field": "字幕表达模板", "message": f"缺少 {label}"})
    frames = attachment_names(record.get("叙事节点参考帧"))
    if not frames:
        errors.append({"code": "MISSING_REFERENCE_FRAMES", "field": "叙事节点参考帧", "message": "可复刻拆解必须为每个叙事段提供开始参考帧"})
    template = str(record.get("逐段复刻模板", "")).strip()
    if not template:
        errors.append({"code": "MISSING_SEGMENT_TEMPLATE", "field": "逐段复刻模板", "message": "可复刻拆解必须有逐段模板"})
    else:
        lines = [line.strip() for line in template.splitlines() if line.strip()]
        if not lines or any(header not in lines[0] for header in SEGMENT_HEADERS):
            errors.append({"code": "INVALID_SEGMENT_HEADER", "field": "逐段复刻模板", "message": "首行必须包含七列标准表头"})
        rows = [line for line in lines[2:] if line.startswith("|")]
        if not rows:
            errors.append({"code": "MISSING_SEGMENT_ROWS", "field": "逐段复刻模板", "message": "至少需要一条叙事段映射"})
        referenced_frames: set[str] = set()
        for index, row in enumerate(rows, 1):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) != 7 or any(not cell for cell in cells):
                errors.append({"code": "INVALID_SEGMENT_ROW", "field": f"逐段复刻模板[{index}]", "message": "每行必须有七个非空单元格"})
            elif not re.fullmatch(r"S\d{2,}", cells[0]):
                errors.append({"code": "INVALID_SEGMENT_ID", "field": f"逐段复刻模板[{index}]", "message": "段落 ID 必须形如 S01"})
            else:
                frame_name = cells[3]
                if frame_name in referenced_frames:
                    errors.append({"code": "DUPLICATE_REFERENCE_FRAME", "field": f"逐段复刻模板[{index}]", "message": "每个叙事段必须使用唯一参考帧"})
                referenced_frames.add(frame_name)
                if frames and frame_name not in frames:
                    errors.append({"code": "REFERENCE_FRAME_NOT_ATTACHED", "field": f"逐段复刻模板[{index}]", "message": f"附件中找不到 {frame_name}"})
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
