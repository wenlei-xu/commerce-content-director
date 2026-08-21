#!/usr/bin/env python3
"""Compile validated storyboard-image or final-video prompts from a timing plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


IMAGE_ROLES = {"product_anchor", "product_detail", "product_scene", "subject_anchor", "source_contact_sheet"}
VIDEO_ROLES = IMAGE_ROLES | {"storyboard_board", "continuity_frame"}


def fail(message: str) -> ValueError:
    return ValueError(message)


def number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise fail(f"{field} must be a number")
    return float(value)


def validate_beats(segment: dict[str, Any], raw_seconds: float) -> list[dict[str, Any]]:
    beats = segment.get("beats")
    if not isinstance(beats, list) or not beats:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: beats must be a non-empty list")
    cursor = 0.0
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise fail(f"beat {index} must be an object")
        start = number(beat.get("start"), f"beat {index}.start")
        end = number(beat.get("end"), f"beat {index}.end")
        if abs(start - cursor) > 1e-6 or end <= start:
            raise fail(f"beat {index} must start at {cursor:g} and have positive duration")
        if not isinstance(beat.get("description"), str) or not beat["description"].strip():
            raise fail(f"beat {index}.description must be a non-empty string")
        cursor = end
    if abs(cursor - raw_seconds) > 1e-6:
        raise fail(f"beats end at {cursor:g}s, expected {raw_seconds:g}s")
    return beats


def validate_inputs(segment: dict[str, Any], job_kind: str) -> list[dict[str, Any]]:
    inputs = segment.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: inputs must be a non-empty list")
    allowed_roles = IMAGE_ROLES if job_kind == "storyboard_image" else VIDEO_ROLES
    positions: set[int] = set()
    for index, item in enumerate(inputs):
        if not isinstance(item, dict):
            raise fail(f"input {index} must be an object")
        position = item.get("position")
        if not isinstance(position, int) or position < 1 or position in positions:
            raise fail(f"input {index}.position must be a unique positive integer")
        positions.add(position)
        if item.get("role") not in allowed_roles:
            raise fail(f"input {index}.role is not valid for {job_kind}")
        for field in ("asset_id", "sha256", "reason"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise fail(f"input {index}.{field} must be a non-empty string")
        if item.get("clean_for_generation") is not True:
            raise fail(f"input {index}.clean_for_generation must be true")
    if positions != set(range(1, len(inputs) + 1)):
        raise fail("input positions must be contiguous from 1")
    if segment.get("product_visible") and "product_anchor" not in {item["role"] for item in inputs}:
        raise fail("a visible product requires product_anchor")
    return sorted(inputs, key=lambda item: item["position"])


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema") != "commerce-generation-prompt-plan-v1":
        raise fail("unsupported prompt-plan schema")
    job_kind = plan.get("job_kind")
    if job_kind not in {"storyboard_image", "final_video"}:
        raise fail("job_kind must be storyboard_image or final_video")
    if plan.get("prompt_language") not in {"en", "zh-CN"}:
        raise fail("prompt_language must be en or zh-CN")
    raw_seconds = number(plan.get("raw_segment_seconds"), "raw_segment_seconds")
    if raw_seconds <= 0:
        raise fail("raw_segment_seconds must be positive")
    if job_kind == "storyboard_image":
        storyboard = plan.get("storyboard")
        if not isinstance(storyboard, dict) or not all(isinstance(storyboard.get(key), int) and storyboard[key] > 0 for key in ("columns", "rows")):
            raise fail("storyboard image plans require positive storyboard columns and rows")
        if not isinstance(storyboard.get("panel_ratio"), str):
            raise fail("storyboard.panel_ratio must be a string")
    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        raise fail("segments must be a non-empty list")
    seen: set[str] = set()
    for segment in segments:
        if not isinstance(segment, dict):
            raise fail("segment must be an object")
        segment_id = segment.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id or segment_id in seen:
            raise fail("each segment_id must be unique and non-empty")
        seen.add(segment_id)
        validate_beats(segment, raw_seconds)
        validate_inputs(segment, job_kind)
        if job_kind == "storyboard_image" and segment.get("dialogue"):
            raise fail("storyboard-image plans must not contain dialogue")


def timing_lines(beats: list[dict[str, Any]]) -> list[str]:
    return [f"{beat['start']:.1f}–{beat['end']:.1f}s: {beat['description']}" for beat in beats]


def role_lines(inputs: list[dict[str, Any]]) -> list[str]:
    return [f"Input {item['position']} → {item['role']}: {item['reason']}" for item in inputs]


def compile_storyboard(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    storyboard = plan["storyboard"]
    inputs = validate_inputs(segment, "storyboard_image")
    constraints = [*plan.get("common_constraints", []), *segment.get("hard_constraints", [])]
    facts = [item for item in constraints if isinstance(item, str) and item.strip()]
    subject = segment.get("subject_identity")
    if isinstance(subject, str) and subject.strip():
        facts.append(subject)
    return "\n\n".join([
        "OUTPUT\n"
        f"Generate one complete {plan['raw_segment_seconds']:g}-second storyboard board: "
        f"{storyboard['columns']} columns × {storyboard['rows']} rows, {storyboard['panel_ratio']} panels, "
        "zero gutter, left-to-right then top-to-bottom reading order. Do not locally compose or split the returned board.",
        "INPUT IMAGE ROLES\n" + "\n".join(role_lines(inputs)),
        "HARD FACTS\n" + ("\n".join(facts) if facts else "Use only the approved facts for this Segment."),
        "TIMELINE\n" + "\n".join(timing_lines(validate_beats(segment, float(plan['raw_segment_seconds'])))),
        "NEGATIVE CONSTRAINTS\nNo readable text, captions, subtitles, labels, logos, watermarks, UI, panel numbers, or fact-incompatible product structure/action.",
    ])


def compile_video(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    inputs = validate_inputs(segment, "final_video")
    constraints = [item for item in [*plan.get("common_constraints", []), *segment.get("hard_constraints", [])] if isinstance(item, str) and item.strip()]
    dialogue = segment.get("dialogue") or []
    if not isinstance(dialogue, list):
        raise fail("dialogue must be a list when present")
    dialogue_lines = []
    for index, line in enumerate(dialogue):
        if not isinstance(line, dict) or not isinstance(line.get("text"), str):
            raise fail(f"dialogue {index} must include text")
        dialogue_lines.append(f"{number(line.get('start'), f'dialogue {index}.start'):.1f}–{number(line.get('end'), f'dialogue {index}.end'):.1f}s: {line['text']}")
    subject = segment.get("subject_identity") or "No recurring subject identity is locked for this Segment."
    continuity = segment.get("continuity") or "Begin from this Segment's approved opening state with no unexplained change."
    return "\n\n".join([
        "INPUT IMAGE ROLES AND AUTHORITY\n" + "\n".join(role_lines(inputs)),
        "PRODUCT STRUCTURE AND INTERACTION HARD CONSTRAINTS\n" + ("\n".join(constraints) if constraints else "Use only approved product facts."),
        "SUBJECT IDENTITY LOCK\n" + subject,
        "LANGUAGE, AUDIO AND TIMED DIALOGUE\n"
        f"target_spoken_language={plan.get('target_spoken_language', 'th')}. audio_mode={segment.get('audio_mode', 'spoken')}.\n"
        + ("\n".join(dialogue_lines) if dialogue_lines else "Natural sound only; do not speak any line."),
        "NO TEXT AND CROSS-SEGMENT CONTINUITY\n"
        "No captions, subtitles, burned-in text, dialogue transcription, labels, lower thirds, logos, watermarks, UI, or readable text in any language.\n"
        + continuity + "\nTimeline:\n" + "\n".join(timing_lines(validate_beats(segment, float(plan['raw_segment_seconds'])))),
    ])


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    compiler = compile_storyboard if plan["job_kind"] == "storyboard_image" else compile_video
    prompts = []
    for segment in plan["segments"]:
        prompts.append({
            "segment_id": segment["segment_id"],
            "prompt": compiler(plan, segment),
            "inputs": validate_inputs(segment, plan["job_kind"]),
            "beats": validate_beats(segment, float(plan["raw_segment_seconds"])),
            "dialogue": segment.get("dialogue", []),
            "audio_mode": segment.get("audio_mode"),
            "product_visible": bool(segment.get("product_visible")),
        })
    return {
        "schema": "commerce-generation-prompt-bundle-v1",
        "job_kind": plan["job_kind"],
        "prompt_language": plan["prompt_language"],
        "target_spoken_language": plan.get("target_spoken_language"),
        "raw_segment_seconds": plan["raw_segment_seconds"],
        "prompts": prompts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        bundle = compile_plan(plan)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(bundle['prompts'])} prompt(s): {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
