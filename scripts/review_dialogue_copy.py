#!/usr/bin/env python3
"""Review spoken dialogue without rewriting the canonical structured script."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SPOKEN_MODES = {"spoken", "sparse_spoken"}
HAN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
THAI = re.compile(r"[\u0E00-\u0E7F]")
WRITTEN_CONNECTORS = ("直到", "而是", "之后", "从而")
MECHANICAL_CTA = ("点击查看", "点开看看", "赶紧下单", "快来购买")
OPERATION_WORDS = ("打开", "装入", "放下", "清洗", "拿出", "按下", "倒入")
VALUE_WORDS = ("放心", "省心", "方便", "轻松", "有趣", "满足", "陪伴", "不无聊", "值得")


def check(code: str, status: str, message: str, **extra: Any) -> dict[str, Any]:
    result = {"code": code, "status": status, "message": message}
    result.update(extra)
    return result


def speech_char_count(text: str) -> int:
    """Count speech-bearing characters, ignoring whitespace and punctuation."""

    punctuation = set("，。！？、,.!?；;：:（）()“”\"'‘’「」『』—-…")
    return sum(1 for char in text if not char.isspace() and char not in punctuation)


def _line_roles(gate: dict[str, Any]) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = {}
    for field, label in (
        ("pain_line_ids", "pain"),
        ("benefit_line_ids", "benefit"),
        ("proof_line_ids", "proof"),
        ("natural_cta_line_ids", "natural_cta"),
    ):
        for line_id in gate.get(field) or []:
            roles.setdefault(str(line_id), set()).add(label)
    return roles


def review(script: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic dialogue review report.

    This reviewer deliberately reports copy problems but never mutates dialogue
    text. The parent script workflow remains the only writer of structured_script.
    """

    runtime = script.get("runtime") or {}
    audio_mode = runtime.get("audio_mode")
    base = {
        "schema": "commerce-dialogue-copy-review-v1",
        "script_id": script.get("script_id", ""),
        "runtime": {
            "audio_mode": audio_mode,
            "target_spoken_language": runtime.get("target_spoken_language"),
        },
    }
    if audio_mode == "natural_sound_only":
        return {
            **base,
            "status": "not_applicable",
            "blocking": False,
            "checks": [],
            "lines": [],
            "summary": "natural_sound_only does not use the dialogue-copy module",
        }

    advisory_checks: list[dict[str, Any]] = []
    soft_checks: list[dict[str, Any]] = []
    dialogue = script.get("dialogue")
    beats = script.get("beats") or []
    beat_by_id = {str(beat.get("beat_id")): beat for beat in beats if beat.get("beat_id")}
    if audio_mode not in SPOKEN_MODES:
        advisory_checks.append(check("INVALID_AUDIO_MODE", "failed", "spoken dialogue review is intended for spoken or sparse_spoken audio_mode"))
    if not isinstance(dialogue, list):
        advisory_checks.append(check("DIALOGUE_NOT_LIST", "failed", "dialogue should be a list"))
        dialogue = []

    line_ids: list[str] = []
    for index, line in enumerate(dialogue):
        if not isinstance(line, dict):
            advisory_checks.append(check("INVALID_DIALOGUE_LINE", "failed", f"dialogue[{index}] should be an object"))
            continue
        line_id = str(line.get("line_id", "")).strip()
        if not line_id:
            advisory_checks.append(check("MISSING_LINE_ID", "failed", f"dialogue[{index}] is missing line_id"))
        line_ids.append(line_id)
        text = str(line.get("text", "")).strip()
        if not text:
            advisory_checks.append(check("EMPTY_DIALOGUE", "failed", f"dialogue[{index}] has empty text", line_id=line_id))
    duplicate_ids = sorted({line_id for line_id in line_ids if line_id and line_ids.count(line_id) > 1})
    if duplicate_ids:
        advisory_checks.append(check("DUPLICATE_LINE_ID", "failed", f"duplicate dialogue line_id: {', '.join(duplicate_ids)}"))

    gate = script.get("dialogue_quality_gate")
    roles: dict[str, set[str]] = {}
    if not isinstance(gate, dict):
        advisory_checks.append(check("MISSING_DIALOGUE_QUALITY_GATE", "failed", "spoken dialogue can include dialogue_quality_gate review metadata"))
        gate = {}
    if gate.get("instruction_manual_restatement_only") is not False:
        advisory_checks.append(check(
            "INSTRUCTION_MANUAL_DIALOGUE",
            "failed",
            "dialogue cannot be only a restatement of visible operations",
        ))
    role_fields = {
        "pain_line_ids": "pain point",
        "benefit_line_ids": "user benefit",
        "proof_line_ids": "visible proof",
        "natural_cta_line_ids": "natural CTA",
    }
    known_ids = set(line_ids)
    for field, label in role_fields.items():
        references = gate.get(field)
        if not isinstance(references, list) or not references:
            advisory_checks.append(check("MISSING_DIALOGUE_QUALITY_ROLE", "failed", f"missing {label} line evidence", field=field))
            continue
        unknown = sorted(str(value) for value in references if str(value) not in known_ids)
        if unknown:
            advisory_checks.append(check(
                "UNKNOWN_DIALOGUE_QUALITY_REFERENCE",
                "failed",
                f"{field} points to unknown line_id: {', '.join(unknown)}",
                field=field,
            ))
    roles = _line_roles(gate)
    ending = script.get("ending") or {}
    ending_cta_line = str(ending.get("cta_line_id", "")).strip()
    natural_cta_ids = {str(value) for value in gate.get("natural_cta_line_ids") or []}
    if ending_cta_line and ending_cta_line not in natural_cta_ids:
        advisory_checks.append(check(
            "CTA_NOT_NATURAL_GATE_EVIDENCE",
            "failed",
            "ending.cta_line_id must be included in natural_cta_line_ids",
        ))

    reviewed_lines: list[dict[str, Any]] = []
    target_language = runtime.get("target_spoken_language")
    for index, line in enumerate(dialogue):
        if not isinstance(line, dict):
            continue
        line_id = str(line.get("line_id", "")).strip()
        text = str(line.get("text", "")).strip()
        beat_id = str(line.get("beat_id", "")).strip()
        char_count = speech_char_count(text)
        visual_action = str((beat_by_id.get(beat_id) or {}).get("visual_action", "")).strip()
        line_report = {
            "line_id": line_id,
            "text": text,
            "char_count": char_count,
            "beat_id": beat_id,
            "segment_id": str(line.get("segment_id", "")).strip(),
            "start": line.get("start"),
            "end": line.get("end"),
            "roles": sorted(roles.get(line_id, set())),
            "has_visual_evidence": bool(visual_action),
        }
        reviewed_lines.append(line_report)

        if target_language == "zh-CN" and text and not HAN.search(text):
            advisory_checks.append(check("DIALOGUE_LANGUAGE_MISMATCH", "failed", f"{line_id} has no Chinese characters", line_id=line_id))
        if target_language == "th" and text and not THAI.search(text):
            advisory_checks.append(check("DIALOGUE_LANGUAGE_MISMATCH", "failed", f"{line_id} has no Thai characters", line_id=line_id))
        if not visual_action:
            soft_checks.append(check(
                "NO_VISUAL_EVIDENCE",
                "warning",
                f"{line_id} cannot be tied to a beat with visual_action",
                line_id=line_id,
                suggestion="先补齐画面证据，再确认这句台词是否需要保留。",
            ))
        if char_count < 6 or char_count > 18:
            soft_checks.append(check(
                "SPOKEN_LENGTH_OUTSIDE_GUIDE",
                "warning",
                f"{line_id} has {char_count} speech characters; the guide is 6–14, suggested maximum 18",
                line_id=line_id,
                suggestion="按一个反应或一个结果重写，避免凑字或说明书式长句。",
            ))
        connector_hits = [word for word in WRITTEN_CONNECTORS if word in text]
        if connector_hits:
            soft_checks.append(check(
                "WRITTEN_CONNECTOR",
                "warning",
                f"{line_id} uses written connector(s): {'、'.join(connector_hits)}",
                line_id=line_id,
                suggestion="尝试改成更像现场反应的短句。",
            ))
        if any(phrase in text for phrase in MECHANICAL_CTA) and ("natural_cta" in roles.get(line_id, set()) or line_id == ending_cta_line):
            soft_checks.append(check(
                "MECHANICAL_CTA",
                "warning",
                f"{line_id} sounds like a mechanical CTA",
                line_id=line_id,
                suggestion="用符合表达者口吻的收尾替代单纯的点击指令。",
            ))
        operation_hits = [word for word in OPERATION_WORDS if word in text]
        value_hits = [word for word in VALUE_WORDS if word in text]
        if operation_hits and not value_hits and not (roles.get(line_id, set()) & {"pain", "proof"}):
            soft_checks.append(check(
                "OPERATION_RESTATEMENT_RISK",
                "warning",
                f"{line_id} may only repeat visible operations: {'、'.join(operation_hits)}",
                line_id=line_id,
                suggestion="把动作转成观众关心的结果、感受或使用价值。",
            ))

    checks = [
        {**item, "status": "advisory"}
        for item in [*advisory_checks, *soft_checks]
    ]
    status = "advisory" if checks else "reviewed"
    return {
        **base,
        "status": status,
        "blocking": False,
        "checks": checks,
        "lines": reviewed_lines,
        "summary": f"{len(checks)} advisory item(s); dialogue review never blocks production",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path, help="structured_script JSON")
    parser.add_argument("--out", type=Path, required=True, help="dialogue-copy-review JSON output")
    args = parser.parse_args()
    try:
        script = json.loads(args.script.read_text(encoding="utf-8"))
        if not isinstance(script, dict):
            raise ValueError("structured script must be a JSON object")
        report = review(script)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        report = {
            "schema": "commerce-dialogue-copy-review-v1",
            "status": "input_error",
            "blocking": False,
            "checks": [check("INVALID_JSON", "error", str(exc))],
            "lines": [],
        }
        try:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] != "input_error" else 2


if __name__ == "__main__":
    raise SystemExit(main())
