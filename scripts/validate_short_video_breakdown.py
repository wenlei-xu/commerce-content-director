#!/usr/bin/env python3
"""Validate the two reusable outputs of a short-video breakdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SUMMARY_LABELS = ("适合：", "结构：", "主要证明：", "不适合：")
SEGMENT_HEADERS = ("段落", "时间", "叙事任务", "开始参考帧", "结果参考帧", "原内容", "保留机制", "新内容模板")
RHYTHM_VOICEOVER_HEADERS = ("段落", "时间", "叙事任务", "参考帧", "原内容", "原口播")
CAPTION_LABELS = ("类型：", "基础样式：", "强调对象：", "强调方式：", "出现节奏：")
ASSET_STATUSES = {"待审核", "可用", "仅留档", "已合并"}
REUSABLE_ASSET_STATUSES = {"待审核", "可用"}
COMMERCIAL_NARRATIVE_FIELDS = (
    "目标受众与使用场景",
    "叙事视角与表达形式",
    "开头钩子类型",
    "核心冲突或问题",
    "钩子兑现时间与方式",
    "产品首次出现时间",
    "核心卖点及出现顺序",
    "证明链条及出现顺序",
    "主要说服机制",
    "CTA类型",
)
RETIRED_FIELDS = (
    "高光帧",
    "最强高光帧",
    "高光帧时间点",
    "最强高光帧说明",
    "关键转折点及时间",
    "关键信息释放节奏",
    "一句话故事线",
    "叙事结构路径",
    "情绪曲线",
    "视频分辨率",
    "视频帧率",
    "是否有音轨",
    "抽帧总数",
)


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
    asset_status = str(record.get("资产状态", "")).strip()
    if asset_status not in ASSET_STATUSES:
        errors.append({"code": "INVALID_ASSET_STATUS", "field": "资产状态", "message": "必须为待审核、可用、仅留档或已合并"})
    for field in RETIRED_FIELDS:
        if field in record:
            errors.append({"code": "RETIRED_FIELD_PRESENT", "field": field, "message": "该字段已退役，不得继续写入"})
    if asset_status not in REUSABLE_ASSET_STATUSES:
        return {"ok": not errors, "errors": errors}
    for field in COMMERCIAL_NARRATIVE_FIELDS:
        if not str(record.get(field, "")).strip():
            errors.append({"code": "MISSING_COMMERCIAL_FIELD", "field": field, "message": "可复用拆解必须填写十个商业叙事字段"})
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
        errors.append({"code": "MISSING_REFERENCE_FRAMES", "field": "叙事节点参考帧", "message": "可复刻拆解必须为每个叙事段提供开始与结果参考帧"})
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
            if len(cells) != 8 or any(not cell for cell in cells):
                errors.append({"code": "INVALID_SEGMENT_ROW", "field": f"逐段复刻模板[{index}]", "message": "每行必须有八个非空单元格"})
            elif not re.fullmatch(r"S\d{2,}", cells[0]):
                errors.append({"code": "INVALID_SEGMENT_ID", "field": f"逐段复刻模板[{index}]", "message": "段落 ID 必须形如 S01"})
            else:
                segment_id = cells[0]
                start_frame, result_frame = cells[3], cells[4]
                if start_frame == result_frame:
                    errors.append({"code": "DUPLICATE_SEGMENT_REFERENCE_FRAME", "field": f"逐段复刻模板[{index}]", "message": "开始参考帧和结果参考帧必须是不同文件"})
                for role, frame_name in (("start", start_frame), ("result", result_frame)):
                    expected_name = rf"{segment_id}-.+-{role}-\d+(?:\.\d+)?s\.(?:jpg|jpeg|png)"
                    if not re.fullmatch(expected_name, frame_name, flags=re.IGNORECASE):
                        errors.append({"code": "INVALID_REFERENCE_FRAME_NAME", "field": f"逐段复刻模板[{index}]", "message": f"{role} 参考帧文件名必须包含段落 ID、角色和时间：{frame_name}"})
                    if frame_name in referenced_frames:
                        errors.append({"code": "DUPLICATE_REFERENCE_FRAME", "field": f"逐段复刻模板[{index}]", "message": "每张参考帧只能属于一个叙事段和一个角色"})
                    referenced_frames.add(frame_name)
                    if frames and frame_name not in frames:
                        errors.append({"code": "REFERENCE_FRAME_NOT_ATTACHED", "field": f"逐段复刻模板[{index}]", "message": f"附件中找不到 {frame_name}"})
        if frames:
            for frame_name in sorted(frames - referenced_frames):
                errors.append({"code": "UNREFERENCED_NARRATIVE_FRAME", "field": "叙事节点参考帧", "message": f"附件未被逐段模板引用：{frame_name}"})
    rhythm_voiceover = str(record.get("逐段节奏与口播", "")).strip()
    if not rhythm_voiceover:
        errors.append({"code": "MISSING_RHYTHM_VOICEOVER", "field": "逐段节奏与口播", "message": "可复用拆解必须记录逐段节奏与原口播"})
    else:
        lines = [line.strip() for line in rhythm_voiceover.splitlines() if line.strip()]
        header_cells = [cell.strip() for cell in lines[0].strip("|").split("|")] if lines else []
        if tuple(header_cells) != RHYTHM_VOICEOVER_HEADERS:
            errors.append({"code": "INVALID_RHYTHM_VOICEOVER_HEADER", "field": "逐段节奏与口播", "message": "首行必须为：段落、时间、叙事任务、参考帧、原内容、原口播"})
        rows = [line for line in lines[2:] if line.startswith("|")]
        if not rows:
            errors.append({"code": "MISSING_RHYTHM_VOICEOVER_ROWS", "field": "逐段节奏与口播", "message": "至少需要一条逐段节奏与口播记录"})
        for index, row in enumerate(rows, 1):
            cells = [cell.strip() for cell in row.strip("|").split("|")]
            if len(cells) != 6 or any(not cell for cell in cells):
                errors.append({"code": "INVALID_RHYTHM_VOICEOVER_ROW", "field": f"逐段节奏与口播[{index}]", "message": "每行必须有六个非空单元格"})
            elif not re.fullmatch(r"S\d{2,}", cells[0]):
                errors.append({"code": "INVALID_RHYTHM_VOICEOVER_SEGMENT_ID", "field": f"逐段节奏与口播[{index}]", "message": "段落 ID 必须形如 S01"})
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
