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
FIXED_STORYBOARD_EXECUTOR = "gpt_image_2"
FIXED_STORYBOARD_MODEL = "gpt-image-2"
FIXED_STORYBOARD_SIZE = "1152x2048"
FIXED_STORYBOARD_QUALITY = "high"
FIXED_STORYBOARD_FORMAT = "png"
DEFAULT_STORYBOARD_CONCURRENCY = 5
STORYBOARD_PANEL_ORDER = ("top_left", "top_right", "bottom_left", "bottom_right")
STORYBOARD_PANEL_LABELS = {
    "top_left": "Top-left",
    "top_right": "Top-right",
    "bottom_left": "Bottom-left",
    "bottom_right": "Bottom-right",
}
STORYBOARD_HUMAN_PRESENCE = {
    "none": "No person or human body part visible.",
    "one_hand": "Exactly one natural human hand is visible; no extra hand, arm, person, or fingers.",
    "partial_person": "Only the explicitly described part of one person is visible.",
    "full_person": "Exactly one complete person is visible only as explicitly described.",
}
IMAGE_ROLES = {
    "product_anchor", "product_detail", "product_scene", "subject_anchor",
    "source_contact_sheet", *SOURCE_FRAME_ROLES,
}
VIDEO_ROLES = IMAGE_ROLES | {"storyboard_board", "continuity_frame"}
AUDIO_MODES = {"spoken", "sparse_spoken", "natural_sound_only"}
CHINESE_VOICEOVER_PROVIDER = "doubao_tts_2_0"
THAI_VOICEOVER_PROVIDER = "omni_native"
NO_VOICEOVER_PROVIDER = "none"
ENVIRONMENT_ONLY = "environment_only"
NATIVE_DIALOGUE = "native_dialogue"
BATCH_SUBMISSION_THRESHOLD = 2
BATCH_SCOPE = "single_script_single_stage"


def fail(message: str) -> ValueError:
    return ValueError(message)


def number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise fail(f"{field} must be a number")
    return float(value)


def positive_integer(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise fail(f"{field} must be a positive integer")
    return value


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


def validate_string_list(value: object, field: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        requirement = "a list" if allow_empty else "a non-empty list"
        raise fail(f"{field} must be {requirement} of non-empty strings")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise fail(f"{field} must contain only non-empty strings")
    return [item.strip() for item in value]


def validate_storyboard_keyframes(
    segment: dict[str, Any], raw_seconds: float
) -> list[dict[str, Any]]:
    keyframes = validate_beats(segment, raw_seconds)
    if len(keyframes) != len(STORYBOARD_PANEL_ORDER):
        raise fail(
            f"{segment.get('segment_id', '<unknown>')}: storyboard beats must contain "
            "exactly four static panel keyframes"
        )
    observed_panels = tuple(keyframe.get("panel") for keyframe in keyframes)
    if observed_panels != STORYBOARD_PANEL_ORDER:
        raise fail(
            f"{segment.get('segment_id', '<unknown>')}: storyboard panels must be "
            "top_left, top_right, bottom_left, bottom_right in reading order"
        )
    for index, keyframe in enumerate(keyframes):
        for field in ("camera", "continuity"):
            if not isinstance(keyframe.get(field), str) or not keyframe[field].strip():
                raise fail(f"storyboard keyframe {index}.{field} must be a non-empty string")
        if keyframe.get("human_presence") not in STORYBOARD_HUMAN_PRESENCE:
            raise fail(
                f"storyboard keyframe {index}.human_presence must be one of "
                f"{', '.join(sorted(STORYBOARD_HUMAN_PRESENCE))}"
            )
    return keyframes


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
        if plan.get("executor") != FIXED_STORYBOARD_EXECUTOR:
            raise fail(f"storyboard_image executor must be {FIXED_STORYBOARD_EXECUTOR}; Flow2API image generation is forbidden")
        if plan.get("model") != FIXED_STORYBOARD_MODEL:
            raise fail(f"storyboard_image model must be exactly {FIXED_STORYBOARD_MODEL}")
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
        expected_output = {
            "size": FIXED_STORYBOARD_SIZE,
            "quality": FIXED_STORYBOARD_QUALITY,
            "format": FIXED_STORYBOARD_FORMAT,
        }
        if plan.get("image_output") != expected_output:
            raise fail(
                "storyboard_image image_output must be "
                f"{FIXED_STORYBOARD_SIZE}/high/png"
            )
        positive_integer(
            plan.get("candidates_per_segment"), "candidates_per_segment"
        )
        if plan.get("common_constraints"):
            raise fail(
                "storyboard_image plans must use visual_continuity instead of common_constraints"
            )
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
    if job_kind == "final_video":
        audio_modes = {segment.get("audio_mode", "spoken") for segment in segments if isinstance(segment, dict)}
        invalid_modes = audio_modes - AUDIO_MODES
        if invalid_modes:
            raise fail(f"unsupported audio_mode(s): {', '.join(sorted(invalid_modes))}")
        has_voiceover = bool(audio_modes & {"spoken", "sparse_spoken"})
        language = plan["target_spoken_language"]
        expected_provider = (
            CHINESE_VOICEOVER_PROVIDER
            if has_voiceover and language == "zh-CN"
            else THAI_VOICEOVER_PROVIDER
            if has_voiceover
            else NO_VOICEOVER_PROVIDER
        )
        expected_policy = ENVIRONMENT_ONLY if language == "zh-CN" or not has_voiceover else NATIVE_DIALOGUE
        if plan.get("voiceover_provider") != expected_provider:
            raise fail(f"final_video voiceover_provider must be {expected_provider} for this language/audio mode")
        if plan.get("omni_audio_policy") != expected_policy:
            raise fail(f"final_video omni_audio_policy must be {expected_policy} for this language/audio mode")
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
            validate_storyboard_keyframes(segment, raw_seconds)
            validate_string_list(
                segment.get("visual_continuity"),
                f"{segment_id}.visual_continuity",
            )
            validate_string_list(
                segment.get("hard_constraints", []),
                f"{segment_id}.hard_constraints",
                allow_empty=True,
            )
            validate_string_list(
                segment.get("negative_constraints", []),
                f"{segment_id}.negative_constraints",
                allow_empty=True,
            )
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


def storyboard_keyframe_lines(keyframes: list[dict[str, Any]]) -> list[str]:
    lines = [
        "Each panel must depict one frozen, directly observable instant. "
        "Do not describe or blend a multi-step process inside one panel."
    ]
    for keyframe in keyframes:
        label = STORYBOARD_PANEL_LABELS[keyframe["panel"]]
        human_presence = STORYBOARD_HUMAN_PRESENCE[keyframe["human_presence"]]
        lines.append(
            f"{label} ({keyframe['start']:.1f}–{keyframe['end']:.1f}s): "
            f"Camera: {keyframe['camera'].strip()} "
            f"Keyframe: {keyframe['description'].strip()} "
            f"Continuity: {keyframe['continuity'].strip()} "
            f"Human presence: {human_presence}"
        )
    return lines


def compile_storyboard(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    storyboard = plan["storyboard"]
    inputs = validate_inputs(segment, "storyboard_image")
    continuity = validate_string_list(
        segment.get("visual_continuity"),
        f"{segment.get('segment_id', '<unknown>')}.visual_continuity",
    )
    constraints = validate_string_list(
        segment.get("hard_constraints", []),
        f"{segment.get('segment_id', '<unknown>')}.hard_constraints",
        allow_empty=True,
    )
    negative_constraints = validate_string_list(
        segment.get("negative_constraints", []),
        f"{segment.get('segment_id', '<unknown>')}.negative_constraints",
        allow_empty=True,
    )
    authority = role_lines(inputs)
    product_anchor = next((item for item in inputs if item["role"] == "product_anchor"), None)
    if product_anchor is not None:
        authority.append(
            f"Input {product_anchor['position']} is the product appearance authority. "
            "Match its exact colorway, silhouette, proportions, surface texture, feature count, "
            "openings, and relative positions. Do not infer or reinterpret appearance from the "
            "product name or category."
        )
    subject_anchor = next((item for item in inputs if item["role"] == "subject_anchor"), None)
    if subject_anchor is not None:
        authority.append(
            f"Input {subject_anchor['position']} is the subject identity authority. "
            "Keep the same identity, markings, proportions, age, accessories, and body features "
            "across all four panels."
        )
    subject = segment.get("subject_identity")
    if isinstance(subject, str) and subject.strip():
        authority.append(subject.strip())
    strategy = validate_subject_strategy(segment, plan.get("replication_mode"), inputs)
    if strategy == "preserve_source_subject":
        authority.append("Preserve the source person or animal exactly; replace only the source product using the target product anchor. Do not add or redesign a subject.")
    elif strategy == "replace_subject":
        authority.append("The target subject anchor overrides source-subject identity. Replace subject and product in one generation step; do not create an empty-scene intermediate.")
    elif strategy == "structure_only":
        authority.append("Source frames are planning evidence only and are not generation inputs. Target product and subject anchors own identity.")
    validate_source_narrative_mapping(segment, plan.get("replication_mode"))
    keyframes = validate_storyboard_keyframes(
        segment, float(plan["raw_segment_seconds"])
    )
    negatives = [
        "No readable text, captions, subtitles, labels, logos, watermarks, UI, timecodes, or panel numbers.",
        "No visible divider lines, blank gutters, decorative borders, grooves, panel fusion, or content crossing between panels.",
        "No duplicate product or subject, extra people or body parts, malformed hands, extra fingers, or fact-incompatible product structure or action.",
        *negative_constraints,
    ]
    return "\n\n".join([
        "OUTPUT SPECIFICATION\n"
        f"Generate one complete {plan['raw_segment_seconds']:g}-second target production storyboard board: "
        f"exactly {storyboard['columns']} columns × {storyboard['rows']} rows, exactly four {storyboard['panel_ratio']} target panels, "
        "left-to-right then top-to-bottom reading order. The four panels touch edge-to-edge and remain visually independent with hard boundaries. "
        "There is no blank gutter, gap, groove, visible divider line, decorative border, panel label, or content crossing between panels.",
        "GLOBAL VISUAL CONTINUITY\n" + "\n".join([
            *continuity,
            "Keep the same scene, surface, lighting, product identity, subject identity, and spatial relationship across all four panels unless a keyframe explicitly changes one of them.",
        ]),
        "REFERENCE AND IDENTITY AUTHORITY\n" + "\n".join(authority),
        "PRODUCT AND ACTION CONSTRAINTS\n" + (
            "\n".join(constraints)
            if constraints
            else "Use only the approved product and action facts for this Segment."
        ),
        "FOUR STATIC KEYFRAMES\n" + "\n".join(storyboard_keyframe_lines(keyframes)),
        "NEGATIVE CONSTRAINTS\n" + "\n".join(negatives),
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
    audio_mode = segment.get("audio_mode", "spoken")
    if plan["target_spoken_language"] == "zh-CN":
        external_voiceover_note = (
            "Approved Chinese dialogue is produced outside Omni with Doubao TTS 2.0 and is intentionally omitted from this generation prompt."
            if audio_mode in {"spoken", "sparse_spoken"}
            else "This Segment has no dialogue or voiceover."
        )
        audio_payload = (
            f"target_spoken_language=zh-CN. audio_mode={audio_mode}. "
            f"voiceover_provider={plan['voiceover_provider']}. omni_audio_policy={ENVIRONMENT_ONLY}.\n"
            "Generate synchronized environmental sounds only. No spoken voice, narration, dialogue, "
            f"singing, humming, or background music. {external_voiceover_note}"
        )
    else:
        audio_payload = (
            f"target_spoken_language=th. audio_mode={audio_mode}. "
            f"voiceover_provider={plan['voiceover_provider']}. omni_audio_policy={plan['omni_audio_policy']}.\n"
            + ("\n".join(dialogue_lines) if dialogue_lines else "Natural sound only; do not speak any line.")
        )
    return "\n\n".join([
        "INPUT IMAGE ROLES AND AUTHORITY\n" + "\n".join(role_lines(inputs)),
        "PRODUCT STRUCTURE AND INTERACTION HARD CONSTRAINTS\n" + ("\n".join(constraints) if constraints else "Use only approved product facts."),
        "SUBJECT IDENTITY LOCK\n" + subject,
        "LANGUAGE, AUDIO AND TIMED DIALOGUE\n" + audio_payload,
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


def build_execution_jobs(
    job_kind: str,
    prompts: list[dict[str, Any]],
    candidates_per_segment: int | None,
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    idempotency_kind = (
        "storyboard" if job_kind == "storyboard_image" else "video"
    )
    for prompt_index, prompt in enumerate(prompts):
        segment_id = prompt["segment_id"]
        if job_kind == "storyboard_image":
            candidate_count = positive_integer(
                candidates_per_segment, "candidates_per_segment"
            )
            attempts = range(1, candidate_count + 1)
        else:
            attempts = range(1, 2)
        for attempt in attempts:
            jobs.append({
                "job_key": f"{segment_id}:{job_kind}:attempt-{attempt:02d}",
                "prompt_index": prompt_index,
                "segment_id": segment_id,
                "attempt": attempt,
                "content_id_template": (
                    f"{{script_record_id}}:{segment_id}:attempt-{attempt:02d}"
                ),
                "idempotency_key_template": (
                    f"{{run_id}}:{segment_id}:{idempotency_kind}:{attempt}"
                ),
            })
    return jobs


def build_submission_policy(job_kind: str, job_count: int) -> dict[str, Any]:
    is_batch = job_count >= BATCH_SUBMISSION_THRESHOLD
    stage_name = "storyboard" if job_kind == "storyboard_image" else "video"
    if job_kind == "storyboard_image":
        return {
            "scope": BATCH_SCOPE,
            "ready_job_count": job_count,
            "batch_threshold": BATCH_SUBMISSION_THRESHOLD,
            "method": "gpt_image_2_concurrent" if is_batch else "gpt_image_2_single",
            "max_concurrency": DEFAULT_STORYBOARD_CONCURRENCY if is_batch else 1,
            "request_group_id_template": f"{{run_id}}:{stage_name}:initial",
            "single_submit_allowed_only_when": [
                "one_ready_job",
                "one_repair_job",
            ],
        }
    return {
        "scope": BATCH_SCOPE,
        "ready_job_count": job_count,
        "batch_threshold": BATCH_SUBMISSION_THRESHOLD,
        "method": "flow_submit_batch" if is_batch else "flow_submit_video",
        "batch_kind": "image" if job_kind == "storyboard_image" else "video",
        "batch_id_template": f"{{run_id}}:{stage_name}:initial",
        "single_submit_allowed_only_when": [
            "one_ready_job",
            "one_repair_job",
            "recorded_batch_unavailable",
        ],
    }


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    compiler = compile_storyboard if plan["job_kind"] == "storyboard_image" else compile_video
    candidates_per_segment = (
        positive_integer(
            plan.get("candidates_per_segment"), "candidates_per_segment"
        )
        if plan["job_kind"] == "storyboard_image"
        else None
    )
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
            "visual_continuity": segment.get("visual_continuity"),
            "prompt": compiled_prompt,
            "inputs": validate_inputs(segment, plan["job_kind"]),
            "beats": validate_beats(segment, float(plan["raw_segment_seconds"])),
            "dialogue": segment.get("dialogue", []),
            "audio_mode": segment.get("audio_mode"),
            "voiceover_provider": plan.get("voiceover_provider"),
            "omni_audio_policy": plan.get("omni_audio_policy"),
            "product_visible": bool(segment.get("product_visible")),
            "candidate_attempts": (
                list(range(1, candidates_per_segment + 1))
                if candidates_per_segment is not None
                else None
            ),
        })
    execution_jobs = build_execution_jobs(
        plan["job_kind"], prompts, candidates_per_segment
    )
    return {
        "schema": "commerce-generation-prompt-bundle-v1",
        "job_kind": plan["job_kind"],
        "executor": plan.get("executor"),
        "model": plan.get("model"),
        "replication_mode": plan.get("replication_mode"),
        "generation_unit": plan.get("generation_unit"),
        "prompt_language": plan["prompt_language"],
        "target_spoken_language": plan.get("target_spoken_language"),
        "voiceover_provider": plan.get("voiceover_provider"),
        "omni_audio_policy": plan.get("omni_audio_policy"),
        "target_duration_seconds": plan.get("target_duration_seconds"),
        "raw_segment_seconds": plan["raw_segment_seconds"],
        "storyboard": plan.get("storyboard"),
        "image_output": plan.get("image_output"),
        "candidates_per_segment": candidates_per_segment,
        "expected_candidate_job_count": (
            len(prompts) * candidates_per_segment
            if candidates_per_segment is not None
            else None
        ),
        "expected_job_count": len(execution_jobs),
        "submission_policy": build_submission_policy(
            plan["job_kind"], len(execution_jobs)
        ),
        "execution_jobs": execution_jobs,
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
    if bundle["job_kind"] == "storyboard_image":
        print(
            f"Wrote {len(bundle['prompts'])} logical Segment prompt(s) and "
            f"{bundle['expected_candidate_job_count']} candidate Job(s): {args.out}"
        )
    else:
        print(f"Wrote {len(bundle['prompts'])} prompt(s): {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
