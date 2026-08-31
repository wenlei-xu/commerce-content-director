#!/usr/bin/env python3
"""Validate a compiled commerce generation-prompt bundle before Job submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from compile_generation_prompts import (
    CHINESE_VOICEOVER_PROVIDER,
    ENVIRONMENT_ONLY,
    FIXED_FIRST_FRAME_RATIO,
    FIXED_RAW_SEGMENT_SECONDS,
    FIXED_FIRST_FRAME_EXECUTOR,
    FIXED_FIRST_FRAME_FORMAT,
    FIXED_FIRST_FRAME_MODEL,
    FIXED_FIRST_FRAME_QUALITY,
    FIXED_FIRST_FRAME_SIZE,
    HIGH_FIDELITY_REPLICATION_MODES,
    REPLICATION_MODES,
    SOURCE_FRAME_ROLES,
    SOURCE_VISUAL_STYLE_FIELDS,
    TARGET_PRODUCTION_UNIT,
    THAI_VOICEOVER_PROVIDER,
    build_execution_jobs,
    build_submission_policy,
    validate_beats,
    validate_inputs,
    validate_source_narrative_mapping,
    validate_source_visual_style,
    validate_string_list,
    validate_product_visual_lock,
    validate_first_frame,
    validate_subject_strategy,
    validate_target_time_range,
)


THAI = re.compile(r"[\u0E00-\u0E7F]")
HAN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
IMAGE_HEADINGS = (
    "OUTPUT SPECIFICATION",
    "GLOBAL VISUAL CONTINUITY",
    "REFERENCE AND IDENTITY AUTHORITY",
    "PRODUCT AND ACTION CONSTRAINTS",
    "FIRST FRAME",
    "NEGATIVE CONSTRAINTS",
)
IMAGE_WORKFLOW_METADATA_MARKERS = (
    "RHYTHM AUTHORITY",
    "Mapped source narratives:",
    "Do not locally compose",
)


def load_allowed_languages(schema_path: Path) -> set[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    policy = schema.get("language_policy") or {}
    languages = policy.get("generation_prompt_languages")
    if not isinstance(languages, list) or not all(isinstance(value, str) for value in languages):
        raise ValueError("schema generation_prompt_languages must be a string list")
    return set(languages)


def load_allowed_spoken_languages(schema_path: Path) -> set[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    policy = schema.get("language_policy") or {}
    languages = policy.get("allowed_spoken_languages")
    if not isinstance(languages, list) or not all(isinstance(value, str) for value in languages):
        raise ValueError("schema allowed_spoken_languages must be a string list")
    return set(languages)


def validate_bundle(
    bundle: dict[str, Any],
    allowed_languages: set[str],
    allowed_spoken_languages: set[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    allowed_spoken_languages = allowed_spoken_languages or {"th", "zh-CN"}
    if bundle.get("schema") != "commerce-generation-prompt-bundle-v1":
        return ["unsupported prompt-bundle schema"]
    kind = bundle.get("job_kind")
    if kind not in {"first_frame_image", "final_video"}:
        return ["job_kind must be first_frame_image or final_video"]
    if kind == "first_frame_image":
        if bundle.get("executor") != FIXED_FIRST_FRAME_EXECUTOR:
            errors.append(f"first_frame_image executor must be {FIXED_FIRST_FRAME_EXECUTOR}; Flow2API image generation is forbidden")
        if bundle.get("model") != FIXED_FIRST_FRAME_MODEL:
            errors.append(f"first_frame_image model must be exactly {FIXED_FIRST_FRAME_MODEL}")
        if bundle.get("generation_unit") != TARGET_PRODUCTION_UNIT:
            errors.append(f"first_frame_image generation_unit must be {TARGET_PRODUCTION_UNIT}")
        first_frame_layout = bundle.get("first_frame_layout")
        if not isinstance(first_frame_layout, dict) or first_frame_layout.get("aspect_ratio") != FIXED_FIRST_FRAME_RATIO:
            errors.append("first_frame_image output must declare aspect_ratio=9:16")
        expected_output = {
            "size": FIXED_FIRST_FRAME_SIZE,
            "quality": FIXED_FIRST_FRAME_QUALITY,
            "format": FIXED_FIRST_FRAME_FORMAT,
        }
        if bundle.get("image_output") != expected_output:
            errors.append(
                "first_frame_image image_output must be "
                f"{FIXED_FIRST_FRAME_SIZE}/high/png"
            )
        candidates_per_segment = bundle.get("candidates_per_segment")
        if (
            not isinstance(candidates_per_segment, int)
            or isinstance(candidates_per_segment, bool)
            or candidates_per_segment < 1
        ):
            errors.append("candidates_per_segment must be a positive integer")
    source_visual_style = None
    try:
        source_visual_style = validate_source_visual_style(bundle)
    except ValueError as error:
        errors.append(str(error))
    if bundle.get("prompt_language") not in allowed_languages:
        errors.append("prompt_language is not allowed by the schema")
    target_spoken_language = bundle.get("target_spoken_language")
    if target_spoken_language not in allowed_spoken_languages:
        errors.append("target_spoken_language is not allowed by the schema")
    raw_seconds = bundle.get("raw_segment_seconds")
    if not isinstance(raw_seconds, (int, float)) or isinstance(raw_seconds, bool) or raw_seconds <= 0:
        errors.append("raw_segment_seconds must be positive")
        return errors
    if kind == "first_frame_image" and abs(float(raw_seconds) - FIXED_RAW_SEGMENT_SECONDS) > 1e-6:
        errors.append(f"first_frame_image raw_segment_seconds must be {FIXED_RAW_SEGMENT_SECONDS}")
    target_seconds = bundle.get("target_duration_seconds")
    if kind == "first_frame_image":
        if not isinstance(target_seconds, (int, float)) or isinstance(target_seconds, bool) or target_seconds <= 0:
            errors.append("first_frame_image target_duration_seconds must be positive")
        elif abs(float(target_seconds) % float(raw_seconds)) > 1e-6:
            errors.append("first_frame_image target_duration_seconds must be divisible by raw_segment_seconds")
    prompts = bundle.get("prompts")
    if not isinstance(prompts, list) or not prompts:
        return errors + ["prompts must be a non-empty list"]
    if kind == "final_video":
        audio_modes = {entry.get("audio_mode", "spoken") for entry in prompts if isinstance(entry, dict)}
        has_voiceover = bool(audio_modes & {"spoken", "sparse_spoken"})
        expected_provider = (
            CHINESE_VOICEOVER_PROVIDER
            if has_voiceover and target_spoken_language == "zh-CN"
            else THAI_VOICEOVER_PROVIDER
            if has_voiceover
            else "none"
        )
        expected_policy = ENVIRONMENT_ONLY if target_spoken_language == "zh-CN" or not has_voiceover else "native_dialogue"
        if bundle.get("voiceover_provider") != expected_provider:
            errors.append(f"voiceover_provider must be {expected_provider} for this final-video bundle")
        if bundle.get("omni_audio_policy") != expected_policy:
            errors.append(f"omni_audio_policy must be {expected_policy} for this final-video bundle")
    if kind == "first_frame_image" and isinstance(target_seconds, (int, float)) and not isinstance(target_seconds, bool):
        expected_count = int(float(target_seconds) / float(raw_seconds))
        versions = bundle.get("versions")
        version_count = len(versions) if isinstance(versions, list) and versions else 1
        if len(prompts) != expected_count * version_count:
            errors.append(f"first_frame_image requires {expected_count * version_count} Segment/version prompt(s)")
        if isinstance(versions, list) and versions and set(versions) != {"A", "B"}:
            errors.append("first-frame versions must contain exactly A and B")
        if isinstance(versions, list) and set(versions) == {"A", "B"}:
            expected_per_version = expected_count
            observed = {version: 0 for version in versions}
            for entry in prompts:
                version = entry.get("version") if isinstance(entry, dict) else None
                if version in observed:
                    observed[version] += 1
                else:
                    errors.append("every versioned first-frame prompt must declare version A or B")
            if any(count != expected_per_version for count in observed.values()):
                errors.append(f"each first-frame version requires {expected_per_version} prompt(s)")
        candidates_per_segment = bundle.get("candidates_per_segment")
        if isinstance(candidates_per_segment, int) and not isinstance(candidates_per_segment, bool):
            expected_jobs = expected_count * version_count * candidates_per_segment
            if bundle.get("expected_candidate_job_count") != expected_jobs:
                errors.append(
                    f"expected_candidate_job_count must be {expected_jobs}"
                )
    # Final-video prompts follow the compact creative scaffold. Their section
    # labels are organizational guidance, not a hard validation gate. Keep
    # hard checks on the underlying input, timing, language, audio and execution
    # metadata below instead of accepting/rejecting prompts by heading count.
    headings = IMAGE_HEADINGS if kind == "first_frame_image" else ()
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
        if kind == "first_frame_image":
            for marker in IMAGE_WORKFLOW_METADATA_MARKERS:
                if marker in prompt:
                    errors.append(
                        f"{prefix} contains workflow metadata that must stay outside the image prompt: {marker!r}"
                    )
            if bundle.get("replication_mode") in REPLICATION_MODES and source_visual_style:
                for field in SOURCE_VISUAL_STYLE_FIELDS:
                    if source_visual_style[field] not in prompt:
                        errors.append(
                            f"{prefix} must include source_visual_style.{field} verbatim"
                        )
        control_text = prompt
        dialogue_payload = entry.get("dialogue") or []
        if not (kind == "final_video" and target_spoken_language == "zh-CN"):
            for line in dialogue_payload:
                text = line.get("text") if isinstance(line, dict) else None
                if isinstance(text, str) and text:
                    control_text = control_text.replace(text, "")
        if THAI.search(control_text) or HAN.search(control_text):
            errors.append(f"{prefix} contains non-English control text")
        try:
            segment = {
                "segment_id": segment_id,
                "target_time_range": entry.get("target_time_range"),
                "source_narrative_segment_ids": entry.get("source_narrative_segment_ids"),
                "inputs": entry.get("inputs"),
                "beats": entry.get("beats"),
                "product_visible": entry.get("product_visible"),
                "product_visual_lock": entry.get("product_visual_lock"),
                "subject_strategy": entry.get("subject_strategy"),
                "first_frame": entry.get("first_frame"),
            }
            inputs = validate_inputs(segment, kind)
            validate_beats(segment, float(raw_seconds))
            if kind == "first_frame_image":
                product_visual_lock = validate_product_visual_lock(segment)
                if product_visual_lock and product_visual_lock not in prompt:
                    errors.append(
                        f"{prefix}: product_visual_lock must be copied verbatim into the prompt"
                    )
                validate_first_frame(segment, float(raw_seconds))
                validate_string_list(
                    entry.get("visual_continuity"),
                    f"{prefix}.visual_continuity",
                )
                segment_position = index
                if isinstance(versions, list) and set(versions) == {"A", "B"}:
                    segment_position = index % expected_count
                validate_target_time_range(segment, segment_position, float(raw_seconds))
                validate_source_narrative_mapping(segment, bundle.get("replication_mode"))
            if kind == "first_frame_image" and bundle.get("replication_mode") in HIGH_FIDELITY_REPLICATION_MODES:
                roles = [item.get("role") for item in entry.get("inputs") or []]
                for role in SOURCE_FRAME_ROLES:
                    if roles.count(role) != 1:
                        errors.append(f"{prefix}: high-fidelity replication requires exactly one {role}")
            if kind == "first_frame_image":
                validate_subject_strategy(segment, bundle.get("replication_mode"), inputs)
                director = entry.get("director")
                if not isinstance(director, dict) or director.get("module") != "Director":
                    errors.append(f"{prefix}: first-frame prompt must include Director output")
                elif director.get("script_mutation") != "forbidden":
                    errors.append(f"{prefix}: Director must declare script_mutation=forbidden")
                elif not isinstance(director.get("first_frame"), dict):
                    errors.append(f"{prefix}: Director output must contain one first_frame")
                else:
                    required_first_frame_fields = ("static_moment", "camera", "composition", "performance", "continuity")
                    first_frame = director["first_frame"]
                    if any(not isinstance(first_frame.get(field), str) or not first_frame[field].strip() for field in required_first_frame_fields):
                        errors.append(f"{prefix}: Director first_frame is missing a visual decision")
        except ValueError as error:
            errors.append(f"{prefix}: {error}")
        dialogue = entry.get("dialogue") or []
        if kind == "first_frame_image" and dialogue:
            errors.append(f"{prefix}: first-frame image prompt cannot contain dialogue")
        if kind == "first_frame_image" and isinstance(
            bundle.get("candidates_per_segment"), int
        ):
            expected_attempts = list(
                range(1, bundle["candidates_per_segment"] + 1)
            )
            if entry.get("candidate_attempts") != expected_attempts:
                errors.append(
                    f"{prefix}.candidate_attempts must be {expected_attempts}"
                )
        if kind == "final_video":
            if entry.get("voiceover_provider") != bundle.get("voiceover_provider"):
                errors.append(f"{prefix}: voiceover_provider does not match the bundle")
            if entry.get("omni_audio_policy") != bundle.get("omni_audio_policy"):
                errors.append(f"{prefix}: omni_audio_policy does not match the bundle")
            if target_spoken_language == "zh-CN":
                required_audio_markers = (
                    f"voiceover_provider={bundle.get('voiceover_provider')}",
                    "omni_audio_policy=environment_only",
                    "No spoken voice",
                    "No spoken voice, narration, dialogue, singing, humming, or background music",
                )
                for marker in required_audio_markers:
                    if marker not in prompt:
                        errors.append(f"{prefix}: Chinese external-TTS prompt is missing {marker!r}")
                for line in dialogue_payload:
                    text = line.get("text") if isinstance(line, dict) else None
                    if isinstance(text, str) and text and text in prompt:
                        errors.append(f"{prefix}: Chinese dialogue must not be sent to Omni")
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
                if not isinstance(text, str):
                    errors.append(f"{prefix}.dialogue[{line_index}] must contain text")
                elif target_spoken_language == "th" and not THAI.search(text):
                    errors.append(f"{prefix}.dialogue[{line_index}] must contain Thai text")
                elif target_spoken_language == "zh-CN" and not HAN.search(text):
                    errors.append(f"{prefix}.dialogue[{line_index}] must contain Chinese text")
                try:
                    start = float(line["start"])
                    end = float(line["end"])
                    if start < 0 or end <= start or end > float(raw_seconds):
                        errors.append(f"{prefix}.dialogue[{line_index}] timing is outside the Segment")
                except (KeyError, TypeError, ValueError):
                    errors.append(f"{prefix}.dialogue[{line_index}] must have valid start/end times")
    candidates_per_segment = (
        bundle.get("candidates_per_segment")
        if kind == "first_frame_image"
        else None
    )
    if kind == "first_frame_image" and not (
        isinstance(candidates_per_segment, int)
        and not isinstance(candidates_per_segment, bool)
        and candidates_per_segment > 0
    ):
        return errors
    if not all(
        isinstance(prompt, dict)
        and isinstance(prompt.get("segment_id"), str)
        and bool(prompt["segment_id"])
        for prompt in prompts
    ):
        return errors
    expected_execution_jobs = build_execution_jobs(
        kind, prompts, candidates_per_segment
    )
    if bundle.get("execution_jobs") != expected_execution_jobs:
        errors.append("execution_jobs do not match the compiled Segment/attempt plan")
    if bundle.get("expected_job_count") != len(expected_execution_jobs):
        errors.append(
            f"expected_job_count must be {len(expected_execution_jobs)}"
        )
    expected_policy = build_submission_policy(kind, len(expected_execution_jobs))
    if bundle.get("submission_policy") != expected_policy:
        errors.append(
            "submission_policy must match concurrent GPT Image 2 execution for "
            "first-frame images or Flow2API batch execution for final video"
        )
    return errors


def main() -> int:
    skill_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--schema", type=Path, default=skill_dir / "config" / "base-schema.json")
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        errors = validate_bundle(
            bundle,
            load_allowed_languages(args.schema),
            load_allowed_spoken_languages(args.schema),
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if errors:
        print("\n".join(f"FAIL {error}" for error in errors))
        return 1
    print(f"PASS {args.bundle}: {len(bundle['prompts'])} prompt(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
