#!/usr/bin/env python3
"""Validate a compiled commerce generation-prompt bundle before Job submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from compile_generation_prompts import (
    FIXED_PANEL_RATIO,
    FIXED_RAW_SEGMENT_SECONDS,
    FIXED_STORYBOARD_COLUMNS,
    FIXED_STORYBOARD_ROWS,
    SOURCE_FRAME_ROLES,
    TARGET_PRODUCTION_UNIT,
    validate_beats,
    validate_inputs,
    validate_source_narrative_mapping,
    validate_subject_strategy,
    validate_target_time_range,
)


THAI = re.compile(r"[\u0E00-\u0E7F]")
IMAGE_HEADINGS = ("OUTPUT", "INPUT IMAGE ROLES", "HARD FACTS", "RHYTHM AUTHORITY", "TIMELINE", "NEGATIVE CONSTRAINTS")
VIDEO_HEADINGS = (
    "INPUT IMAGE ROLES AND AUTHORITY",
    "PRODUCT STRUCTURE AND INTERACTION HARD CONSTRAINTS",
    "SUBJECT IDENTITY LOCK",
    "LANGUAGE, AUDIO AND TIMED DIALOGUE",
    "NO TEXT AND CROSS-SEGMENT CONTINUITY",
)


def load_allowed_languages(schema_path: Path) -> set[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    policy = schema.get("language_policy") or {}
    languages = policy.get("generation_prompt_languages")
    if not isinstance(languages, list) or not all(isinstance(value, str) for value in languages):
        raise ValueError("schema generation_prompt_languages must be a string list")
    return set(languages)


def validate_bundle(bundle: dict[str, Any], allowed_languages: set[str]) -> list[str]:
    errors: list[str] = []
    if bundle.get("schema") != "commerce-generation-prompt-bundle-v1":
        return ["unsupported prompt-bundle schema"]
    kind = bundle.get("job_kind")
    if kind not in {"storyboard_image", "final_video"}:
        return ["job_kind must be storyboard_image or final_video"]
    if kind == "storyboard_image":
        if bundle.get("executor") != "flow2api_mcp":
            errors.append("storyboard_image executor must be flow2api_mcp; GPT Image and provider fallback are forbidden")
        if not isinstance(bundle.get("model"), str) or not bundle["model"].strip():
            errors.append("storyboard_image model must be a non-empty Flow2API catalog model ID")
        if bundle.get("generation_unit") != TARGET_PRODUCTION_UNIT:
            errors.append(f"storyboard_image generation_unit must be {TARGET_PRODUCTION_UNIT}")
        storyboard = bundle.get("storyboard")
        if not isinstance(storyboard, dict) or (
            storyboard.get("columns") != FIXED_STORYBOARD_COLUMNS
            or storyboard.get("rows") != FIXED_STORYBOARD_ROWS
            or storyboard.get("panel_ratio") != FIXED_PANEL_RATIO
        ):
            errors.append("storyboard_image output must be one 2x2 board with four 9:16 panels")
    if bundle.get("prompt_language") not in allowed_languages:
        errors.append("prompt_language is not allowed by the schema")
    raw_seconds = bundle.get("raw_segment_seconds")
    if not isinstance(raw_seconds, (int, float)) or isinstance(raw_seconds, bool) or raw_seconds <= 0:
        errors.append("raw_segment_seconds must be positive")
        return errors
    if kind == "storyboard_image" and abs(float(raw_seconds) - FIXED_RAW_SEGMENT_SECONDS) > 1e-6:
        errors.append(f"storyboard_image raw_segment_seconds must be {FIXED_RAW_SEGMENT_SECONDS}")
    target_seconds = bundle.get("target_duration_seconds")
    if kind == "storyboard_image":
        if not isinstance(target_seconds, (int, float)) or isinstance(target_seconds, bool) or target_seconds <= 0:
            errors.append("storyboard_image target_duration_seconds must be positive")
        elif abs(float(target_seconds) % float(raw_seconds)) > 1e-6:
            errors.append("storyboard_image target_duration_seconds must be divisible by raw_segment_seconds")
    prompts = bundle.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        return errors + ["prompts must be a non-empty list"]
    if kind == "storyboard_image" and isinstance(target_seconds, (int, float)) and not isinstance(target_seconds, bool):
        expected_count = int(float(target_seconds) / float(raw_seconds))
        if len(prompts) != expected_count:
            errors.append(f"storyboard_image requires {expected_count} target production Segment(s)")
    headings = IMAGE_HEADINGS if kind == "storyboard_image" else VIDEO_HEADINGS
    dialogue_ids: dict[str, str] = {}
    for index, entry in enumerate(prompts):
        prefix = f"prompt {index}"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        segment_id = entry.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id:
            errors.append(f"{prefix}.segment_id must be a non-empty string")
        prompt = entry.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{prefix}.prompt must be a non-empty string")
            continue
        for heading in headings:
            if heading not in prompt:
                errors.append(f"{prefix} is missing heading {heading!r}")
        if kind == "storyboard_image" and THAI.search(prompt):
            errors.append(f"{prefix} contains Thai control text")
        try:
            segment = {
                "segment_id": segment_id,
                "target_time_range": entry.get("target_time_range"),
                "source_narrative_segment_ids": entry.get("source_narrative_segment_ids"),
                "inputs": entry.get("inputs"),
                "beats": entry.get("beats"),
                "product_visible": entry.get("product_visible"),
                "subject_strategy": entry.get("subject_strategy"),
            }
            inputs = validate_inputs(segment, kind)
            validate_beats(segment, float(raw_seconds))
            if kind == "storyboard_image":
                validate_target_time_range(segment, index, float(raw_seconds))
                validate_source_narrative_mapping(segment, bundle.get("replication_mode"))
            if kind == "storyboard_image" and bundle.get("replication_mode") == "full_replication":
                roles = [item.get("role") for item in entry.get("inputs") or []]
                for role in SOURCE_FRAME_ROLES:
                    if roles.count(role) != 1:
                        errors.append(f"{prefix}: full_replication requires exactly one {role}")
                if "source_contact_sheet" in roles:
                    errors.append(f"{prefix}: full_replication cannot use source_contact_sheet")
            if kind == "storyboard_image":
                validate_subject_strategy(segment, bundle.get("replication_mode"), inputs)
        except ValueError as error:
            errors.append(f"{prefix}: {error}")
        dialogue = entry.get("dialogue") or []
        if kind == "storyboard_image" and dialogue:
            errors.append(f"{prefix}: storyboard-image prompt cannot contain dialogue")
        if kind == "final_video":
            if bundle.get("target_spoken_language") != "th":
                errors.append("final-video bundle must set target_spoken_language to th")
            if entry.get("audio_mode") == "natural_sound_only" and dialogue:
                errors.append(f"{prefix}: natural_sound_only cannot contain dialogue")
            for line_index, line in enumerate(dialogue):
                if not isinstance(line, dict):
                    errors.append(f"{prefix}.dialogue[{line_index}] must be an object")
                    continue
                line_id = line.get("line_id")
                text = line.get("text")
                if not isinstance(line_id, str) or not line_id:
                    errors.append(f"{prefix}.dialogue[{line_index}].line_id must be non-empty")
                elif line_id in dialogue_ids and line.get("intentional_repeat") is not True:
                    errors.append(f"dialogue line {line_id!r} appears in more than one Segment")
                else:
                    dialogue_ids[line_id] = str(segment_id)
                if not isinstance(text, str) or not THAI.search(text):
                    errors.append(f"{prefix}.dialogue[{line_index}] must contain Thai text")
                try:
                    start = float(line["start"])
                    end = float(line["end"])
                    if start < 0 or end <= start or end > float(raw_seconds):
                        errors.append(f"{prefix}.dialogue[{line_index}] timing is outside the Segment")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{prefix}.dialogue[{line_index}] must have valid start/end times")
    return errors


def main() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--schema", type=Path, default=skill_dir / "config" / "base-schema.json")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        errors = validate_bundle(bundle, load_allowed_languages(args.schema))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if errors:
        print("\n".join(f"FAIL {error}" for error in errors))
        return 1
    print(f"PASS {args.bundle}: {len(bundle['prompts'])} prompt(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
