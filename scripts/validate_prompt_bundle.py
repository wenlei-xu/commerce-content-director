#!/usr/bin/env python3
"""Validate a compiled commerce generation-prompt bundle before Job submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from compile_generation_prompts import validate_beats, validate_inputs


THAI = re.compile(r"[\u0E00-\u0E7F]")
IMAGE_HEADINGS = ("OUTPUT", "INPUT IMAGE ROLES", "HARD FACTS", "TIMELINE", "NEGATIVE CONSTRAINTS")
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
    if bundle.get("prompt_language") not in allowed_languages:
        errors.append("prompt_language is not allowed by the schema")
    raw_seconds = bundle.get("raw_segment_seconds")
    if not isinstance(raw_seconds, (int, float)) or isinstance(raw_seconds, bool) or raw_seconds <= 0:
        errors.append("raw_segment_seconds must be positive")
        return errors
    prompts = bundle.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        return errors + ["prompts must be a non-empty list"]
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
                "inputs": entry.get("inputs"),
                "beats": entry.get("beats"),
                "product_visible": entry.get("product_visible"),
            }
            validate_inputs(segment, kind)
            validate_beats(segment, float(raw_seconds))
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
