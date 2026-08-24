#!/usr/bin/env python3
"""Compile validated storyboard-image or final-video prompts from a timing plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


NON_ENGLISH_CONTROL = re.compile(r"[\u0E00-\u0E7F\u3400-\u4DBF\u4E00-\u9FFF]")


SOURCE_FRAME_ROLES = {"source_segment_start", "source_segment_result"}
SUBJECT_STRATEGIES = {"preserve_source_subject", "replace_subject", "structure_only"}
TARGET_PRODUCTION_UNIT = "target_production_segment"
FIXED_RAW_SEGMENT_SECONDS = 10
FIXED_STORYBOARD_COLUMNS = 2
FIXED_STORYBOARD_ROWS = 2
FIXED_PANEL_RATIO = "9:16"
IMAGE_ROLES = {
    "product_anchor", "product_detail", "product_scene", "subject_anchor",
    "source_contact_sheet", *SOURCE_FRAME_ROLES,
}
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


def validate_subject_strategy(
    segment: dict[str, Any], replication_mode: str | None, inputs: list[dict[str, Any]]
) -> str | None:
    if replication_mode not in {"full_replication", "structure_replication"}:
        return None
    strategy = segment.get("subject_strategy")
    if strategy not in SUBJECT_STRATEGIES:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: replication requires subject_strategy")
    roles = [item["role"] for item in inputs]
    source_counts_ok = all(roles.count(role) == 1 for role in SOURCE_FRAME_ROLES)
    if strategy == "preserve_source_subject":
        if replication_mode != "full_replication" or not source_counts_ok:
            raise fail("preserve_source_subject requires full_replication and exactly two source frames")
        if "subject_anchor" in roles:
            raise fail("preserve_source_subject forbids subject_anchor")
    elif strategy == "replace_subject":
        if replication_mode != "full_replication" or not source_counts_ok:
            raise fail("replace_subject requires full_replication and exactly two source frames")
        if roles.count("subject_anchor") != 1:
            raise fail("replace_subject requires exactly one subject_anchor")
    else:
        if replication_mode != "structure_replication":
            raise fail("structure_only requires structure_replication")
        if any(role in roles for role in SOURCE_FRAME_ROLES | {"source_contact_sheet"}):
            raise fail("structure_only forbids source frames as generation inputs")
        if roles.count("subject_anchor") != 1:
            raise fail("structure_only requires exactly one subject_anchor")
    return str(strategy)


def validate_target_time_range(segment: dict[str, Any], index: int, raw_seconds: float) -> None:
    value = segment.get("target_time_range")
    if not isinstance(value, dict):
        raise fail(f"{segment.get('segment_id', '<unknown>')}: target_time_range must be an object")
    start = number(value.get("start"), "target_time_range.start")
    end = number(value.get("end"), "target_time_range.end")
    expected_start = index * raw_seconds
    expected_end = expected_start + raw_seconds
    if abs(start - expected_start) > 1e-6 or abs(end - expected_end) > 1e-6:
        raise fail(
            f"{segment.get('segment_id', '<unknown>')}: target_time_range must be "
            f"{expected_start:g}–{expected_end:g}s"
        )


def validate_source_narrative_mapping(segment: dict[str, Any], replication_mode: str | None) -> list[str]:
    if replication_mode not in {"full_replication", "structure_replication"}:
        return []
    values = segment.get("source_narrative_segment_ids")
    if not isinstance(values, list) or not values:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: replication requires source_narrative_segment_ids")
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise fail("source_narrative_segment_ids must contain non-empty strings")
    normalized = [value.strip() for value in values]
    if len(normalized) != len(set(normalized)):
        raise fail("source_narrative_segment_ids must be unique within a target production Segment")
    return normalized


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.get("schema") != "commerce-generation-prompt-plan-v1":
        raise fail("unsupported prompt-plan schema")
    job_kind = plan.get("job_kind")
    if job_kind not in {"storyboard_image", "final_video"}:
        raise fail("job_kind must be storyboard_image or final_video")
    if plan.get("prompt_language") != "en":
        raise fail("prompt_language must be en")
    if plan.get("target_spoken_language") not in {"th", "zh-CN"}:
        raise fail("target_spoken_language must be locked to th or zh-CN")
    raw_seconds = number(plan.get("raw_segment_seconds"), "raw_segment_seconds")
    if raw_seconds <= 0:
        raise fail("raw_segment_seconds must be positive")
    if job_kind == "storyboard_image":
        if plan.get("executor") != "flow2api_mcp":
            raise fail("storyboard_image executor must be flow2api_mcp; GPT Image and provider fallback are forbidden")
        if not isinstance(plan.get("model"), str) or not plan["model"].strip():
            raise fail("storyboard_image model must be a non-empty Flow2API catalog model ID")
        if plan.get("generation_unit") != TARGET_PRODUCTION_UNIT:
            raise fail(f"storyboard_image generation_unit must be {TARGET_PRODUCTION_UNIT}")
        if abs(raw_seconds - FIXED_RAW_SEGMENT_SECONDS) > 1e-6:
            raise fail(f"storyboard_image raw_segment_seconds must be {FIXED_RAW_SEGMENT_SECONDS}")
        target_seconds = number(plan.get("target_duration_seconds"), "target_duration_seconds")
        if target_seconds <= 0 or abs(target_seconds % raw_seconds) > 1e-6:
            raise fail("storyboard_image target_duration_seconds must be positive and divisible by raw_segment_seconds")
        storyboard = plan.get("storyboard")
        if not isinstance(storyboard, dict) or not all(isinstance(storyboard.get(key), int) and storyboard[key] > 0 for key in ("columns", "rows")):
            raise fail("storyboard image plans require positive storyboard columns and rows")
        if not isinstance(storyboard.get("panel_ratio"), str):
            raise fail("storyboard.panel_ratio must be a string")
        if (
            storyboard["columns"] != FIXED_STORYBOARD_COLUMNS
            or storyboard["rows"] != FIXED_STORYBOARD_ROWS
            or storyboard["panel_ratio"] != FIXED_PANEL_RATIO
        ):
            raise fail("storyboard_image output must be one 2x2 board with four 9:16 panels")
    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        raise fail("segments must be a non-empty list")
    if job_kind == "storyboard_image":
        expected_count = int(float(plan["target_duration_seconds"]) / raw_seconds)
        if len(segments) != expected_count:
            raise fail(
                f"storyboard_image requires {expected_count} target production Segment(s) for "
                f"{plan['target_duration_seconds']:g}s"
            )
    seen: set[str] = set()
    for segment_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise fail("segment must be an object")
        segment_id = segment.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id or segment_id in seen:
            raise fail("each segment_id must be unique and non-empty")
        seen.add(segment_id)
        validate_beats(segment, raw_seconds)
        inputs = validate_inputs(segment, job_kind)
        if job_kind == "storyboard_image":
            validate_target_time_range(segment, segment_index, raw_seconds)
            validate_source_narrative_mapping(segment, plan.get("replication_mode"))
        if job_kind == "storyboard_image" and plan.get("replication_mode") == "full_replication":
            roles = [item["role"] for item in inputs]
            for role in SOURCE_FRAME_ROLES:
                if roles.count(role) != 1:
                    raise fail(f"{segment_id}: full_replication requires exactly one {role}")
            if "source_contact_sheet" in roles:
                raise fail(f"{segment_id}: full_replication cannot use source_contact_sheet")
        if job_kind == "storyboard_image":
            validate_subject_strategy(segment, plan.get("replication_mode"), inputs)
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
    strategy = validate_subject_strategy(segment, plan.get("replication_mode"), inputs)
    if strategy == "preserve_source_subject":
        facts.append("SUBJECT STRATEGY: Preserve the source person or animal exactly; replace only the source product using the target product anchor. Do not add or redesign a subject.")
    elif strategy == "replace_subject":
        facts.append("SUBJECT STRATEGY: The target subject anchor overrides source-subject identity. Replace subject and product in one generation step; do not create an empty-scene intermediate.")
    elif strategy == "structure_only":
        facts.append("SUBJECT STRATEGY: Source frames are planning evidence only and are not generation inputs. Target product and subject anchors own identity.")
    source_ids = validate_source_narrative_mapping(segment, plan.get("replication_mode"))
    if source_ids:
        rhythm = (
            "Source narrative order and relative pacing are evidence only. "
            "The locked target script and this target production Segment timeline own exact timing. "
            "Do not copy source timestamps or divide the four panels evenly unless the target Beats require it. "
            f"Mapped source narratives: {', '.join(source_ids)}."
        )
    else:
        rhythm = (
            "The locked target script and this target production Segment timeline own exact timing. "
            "Do not divide the four panels evenly unless the target Beats require it."
        )
    return "\n\n".join([
        "OUTPUT\n"
        f"Generate one complete {plan['raw_segment_seconds']:g}-second target production storyboard board: "
        f"exactly {storyboard['columns']} columns × {storyboard['rows']} rows, exactly four {storyboard['panel_ratio']} target panels, "
        "zero gutter, left-to-right then top-to-bottom reading order. Do not locally compose or split the returned board.",
        "INPUT IMAGE ROLES\n" + "\n".join(role_lines(inputs)),
        "HARD FACTS\n" + ("\n".join(facts) if facts else "Use only the approved facts for this Segment."),
        "RHYTHM AUTHORITY\n" + rhythm,
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
        f"target_spoken_language={plan['target_spoken_language']}. audio_mode={segment.get('audio_mode', 'spoken')}.\n"
        + ("\n".join(dialogue_lines) if dialogue_lines else "Natural sound only; do not speak any line."),
        "NO TEXT AND CROSS-SEGMENT CONTINUITY\n"
        "No captions, subtitles, burned-in text, dialogue transcription, labels, lower thirds, logos, watermarks, UI, or readable text in any language.\n"
        + continuity + "\nTimeline:\n" + "\n".join(timing_lines(validate_beats(segment, float(plan['raw_segment_seconds'])))),
    ])


def validate_english_control_prompt(prompt: str, dialogue: list[dict[str, Any]]) -> None:
    control_text = prompt
    for line in dialogue:
        text = line.get("text") if isinstance(line, dict) else None
        if isinstance(text, str) and text:
            control_text = control_text.replace(text, "")
    if NON_ENGLISH_CONTROL.search(control_text):
        raise fail("generation control prompt must be English; only approved dialogue may be Thai or Chinese")


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    compiler = compile_storyboard if plan["job_kind"] == "storyboard_image" else compile_video
    prompts = []
    for segment in plan["segments"]:
        compiled_prompt = compiler(plan, segment)
        dialogue = segment.get("dialogue", [])
        validate_english_control_prompt(compiled_prompt, dialogue)
        prompts.append({
            "segment_id": segment["segment_id"],
            "target_time_range": segment.get("target_time_range"),
            "source_narrative_segment_ids": segment.get("source_narrative_segment_ids", []),
            "subject_strategy": segment.get("subject_strategy"),
            "prompt": compiled_prompt,
            "inputs": validate_inputs(segment, plan["job_kind"]),
            "beats": validate_beats(segment, float(plan["raw_segment_seconds"])),
            "dialogue": segment.get("dialogue", []),
            "audio_mode": segment.get("audio_mode"),
            "product_visible": bool(segment.get("product_visible")),
        })
    return {
        "schema": "commerce-generation-prompt-bundle-v1",
        "job_kind": plan["job_kind"],
        "executor": plan.get("executor"),
        "model": plan.get("model"),
        "replication_mode": plan.get("replication_mode"),
        "generation_unit": plan.get("generation_unit"),
        "prompt_language": plan["prompt_language"],
        "target_spoken_language": plan.get("target_spoken_language"),
        "target_duration_seconds": plan.get("target_duration_seconds"),
        "raw_segment_seconds": plan["raw_segment_seconds"],
        "storyboard": plan.get("storyboard"),
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
