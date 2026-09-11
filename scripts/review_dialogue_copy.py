#!/usr/bin/env python3
"""Review workbook voiceover without rewriting the creation workbook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from workbook import load_and_validate


WRITTEN_CONNECTORS = ("直到", "而是", "之后", "从而")
MECHANICAL_CTA = ("点击查看", "点开看看", "赶紧下单", "快来购买")
OPERATION_WORDS = ("打开", "装入", "放下", "清洗", "拿出", "按下", "倒入")
VALUE_WORDS = ("放心", "省心", "方便", "轻松", "有趣", "满足", "陪伴", "不无聊", "值得")
PUNCTUATION = set("，。！？、,.!?；;：:（）()“”\"'‘’「」『』—-…")


def speech_char_count(text: str) -> int:
    return sum(1 for char in text if not char.isspace() and char not in PUNCTUATION)


def _check(code: str, status: str, message: str, **extra: Any) -> dict[str, Any]:
    result = {"code": code, "status": status, "message": message}
    result.update(extra)
    return result


def review(workbook: dict[str, Any]) -> dict[str, Any]:
    metadata = workbook.get("metadata") or {}
    checks: list[dict[str, Any]] = []
    segment_reports: list[dict[str, Any]] = []
    for segment in workbook["segments"]:
        text = str(segment.get("voiceover") or "").strip()
        if not text:
            continue
        count = speech_char_count(text)
        local: list[dict[str, Any]] = []
        if count > 18:
            local.append(_check("LONG_LINE", "advisory", "口播段落超过建议长度，考虑拆成自然短句", count=count))
        if any(word in text for word in WRITTEN_CONNECTORS):
            local.append(_check("WRITTEN_CONNECTOR", "advisory", "包含偏书面的连接词，可检查是否需要更口语化"))
        if any(word in text for word in MECHANICAL_CTA):
            local.append(_check("MECHANICAL_CTA", "advisory", "CTA 可能像机械指令"))
        if any(word in text for word in OPERATION_WORDS) and not str(segment.get("visual_event") or "").strip():
            local.append(_check("ACTION_WITHOUT_VISUAL", "failed", "口播描述操作但段落没有画面事件"))
        if any(word in text for word in VALUE_WORDS):
            local.append(_check("VALUE_LANGUAGE", "pass", "包含观众价值或反应表达"))
        segment_reports.append({
            "segment_id": segment["segment_id"],
            "text": text,
            "character_count": count,
            "checks": local,
        })
        checks.extend(local)
    if metadata.get("音频模式") == "纯自然声":
        checks.append(_check("NATURAL_SOUND_ONLY", "pass", "纯自然声模式不需要口播"))
    failures = [item for item in checks if item["status"] == "failed"]
    return {
        "schema": "commerce-dialogue-review-v2",
        "workbook_path": workbook.get("workbook_path", ""),
        "workbook_revision": workbook.get("workbook_revision"),
        "blocking": bool(failures),
        "status": "failed" if failures else "passed",
        "checks": checks,
        "segments": segment_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        report = review(load_and_validate(args.workbook))
    except (OSError, ValueError) as exc:
        print(f"FAIL {exc}")
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 1 if report["blocking"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
