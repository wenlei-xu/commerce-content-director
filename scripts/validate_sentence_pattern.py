#!/usr/bin/env python3
"""Validate a sentence-pattern candidate before it is written to Feishu."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PURPOSES = {"钩子", "问题提出", "产品引入", "原理解释", "操作说明", "结果证明", "转折", "CTA"}
LANGUAGES = {"语义模板", "泰语", "中文"}
STATUSES = {"待审核", "可用", "已驳回", "已合并"}
REQUIRED = ("句式名称", "句式用途", "语言", "原句示例", "模板句式", "使用说明", "审核状态")
PROVENANCE_LABELS = ("来源拆解：", "证据类型：", "证据时间码：", "置信度：")


def validate(candidate: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    for key in REQUIRED:
        if not str(candidate.get(key, "")).strip():
            errors.append({"code": "MISSING_REQUIRED", "field": key, "message": f"{key}不能为空"})
    if candidate.get("句式用途") not in PURPOSES:
        errors.append({"code": "INVALID_PURPOSE", "field": "句式用途", "message": "句式用途必须是预设值"})
    if candidate.get("语言") not in LANGUAGES:
        errors.append({"code": "INVALID_LANGUAGE", "field": "语言", "message": "语言必须是预设值"})
    if candidate.get("审核状态") not in STATUSES:
        errors.append({"code": "INVALID_STATUS", "field": "审核状态", "message": "审核状态必须是预设值"})
    pattern = str(candidate.get("模板句式", ""))
    if not re.search(r"\[[^\[\]]+\]", pattern):
        errors.append({"code": "MISSING_SLOT", "field": "模板句式", "message": "模板句式至少包含一个 [槽位]"})
    usage_notes = str(candidate.get("使用说明", ""))
    for label in PROVENANCE_LABELS:
        if label not in usage_notes:
            errors.append({"code": "MISSING_PROVENANCE", "field": "使用说明", "message": f"缺少 {label}"})
    return {"ok": not errors, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {"ok": False, "errors": [{"code": "INVALID_JSON", "field": "candidate", "message": str(exc)}]}
    else:
        report = validate(data)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
