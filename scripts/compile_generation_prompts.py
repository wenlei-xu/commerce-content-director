#!/usr/bin/env python3
"""Compile validated first-frame image or final-video prompts from a timing plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from director import direct_segment


NON_ENGLISH_CONTROL = re.compile(r"[\u0E00-\u0E7F\u3400-\u4DBF\u4E00-\u9FFF]")


SOURCE_FRAME_ROLES = {"source_segment_start", "source_segment_result"}
SOURCE_SCENE_REFERENCE_ROLE = "source_scene_reference"
SUBJECT_STRATEGIES = {"preserve_source_subject", "replace_subject", "structure_only"}
HIGH_FIDELITY_REPLICATION_MODES = {"high_fidelity_replication"}
REPLICATION_MODES = HIGH_FIDELITY_REPLICATION_MODES | {"structure_replication"}
SOURCE_VISUAL_STYLE_FIELDS = ("style_fingerprint_en", "anti_style_constraints_en")
TARGET_PRODUCTION_UNIT = "target_production_segment"
FIXED_RAW_SEGMENT_SECONDS = 10
SUPPORTED_FINAL_SEGMENT_SECONDS = {4, 6, 8, 10}
FINAL_VIDEO_MODELS = {
    4: "gemini_omni_r2v_portrait_4s",
    10: "omni_portrait",
    8: "gemini_omni_r2v_portrait_8s",
    6: "gemini_omni_r2v_portrait_6s",
}
FIXED_FIRST_FRAME_RATIO = "9:16"
FIXED_FIRST_FRAME_EXECUTOR = "gpt_image_2_5"
FIXED_FIRST_FRAME_MODEL = "gpt-image-2.5"
FIXED_FIRST_FRAME_SIZE = "1152x2048"
FIXED_FIRST_FRAME_QUALITY = "high"
FIXED_FIRST_FRAME_FORMAT = "png"
DEFAULT_FIRST_FRAME_CONCURRENCY = 5
# ``candidates_per_segment`` controls local retry slots only. It never creates
# a Feishu record; remote authority is the complete A/B script-version package.
FIRST_FRAME_HUMAN_PRESENCE = {
    "none": "No person or human body part visible.",
    "one_hand": "Exactly one natural human hand is visible; no extra hand, arm, person, or fingers.",
    "partial_person": "Only the explicitly described part of one person is visible.",
    "full_person": "Exactly one complete person is visible only as explicitly described.",
}
IMAGE_ROLES = {
    "product_anchor", "product_detail", "product_scene", "subject_anchor",
    SOURCE_SCENE_REFERENCE_ROLE, *SOURCE_FRAME_ROLES,
}
VIDEO_ROLES = IMAGE_ROLES | {"first_frame_asset", "continuity_frame"}
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


def segment_seconds_for(
    plan: dict[str, Any], segment: dict[str, Any]
) -> float:
    """Return the exact local runtime for one final-video Segment."""
    raw_seconds = number(
        segment.get("segment_seconds", plan.get("raw_segment_seconds")),
        f"{segment.get('segment_id', '<unknown>')}.segment_seconds",
    )
    if plan.get("job_kind") == "final_video":
        if raw_seconds not in SUPPORTED_FINAL_SEGMENT_SECONDS:
            raise fail(
                f"{segment.get('segment_id', '<unknown>')}: final-video segment_seconds "
                "must be one of 10, 8, 6, or 4"
            )
    return raw_seconds


def segment_model_for(plan: dict[str, Any], segment: dict[str, Any]) -> str | None:
    """Resolve the direct model required by a final-video Segment."""
    if plan.get("job_kind") != "final_video":
        return None
    seconds = int(segment_seconds_for(plan, segment))
    expected_model = FINAL_VIDEO_MODELS[seconds]
    requested_model = segment.get("model")
    if requested_model is not None and requested_model != expected_model:
        raise fail(
            f"{segment.get('segment_id', '<unknown>')}: video model is fixed to "
            f"{expected_model} for {seconds:g}s; arbitrary model overrides are forbidden"
        )
    return expected_model


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


def validate_product_visual_lock(segment: dict[str, Any]) -> str | None:
    value = segment.get("product_visual_lock")
    if value is None:
        return None
    if segment.get("product_visible") is not True:
        raise fail("product_visual_lock requires product_visible=true")
    if not isinstance(value, str) or not value.strip():
        raise fail("product_visual_lock must be non-empty English control text")
    normalized = value.strip()
    if NON_ENGLISH_CONTROL.search(normalized):
        raise fail("product_visual_lock must be English control text")
    return normalized


def validate_source_visual_style(plan: dict[str, Any]) -> dict[str, str] | None:
    if (
        plan.get("job_kind") != "first_frame_image"
        or plan.get("replication_mode") not in REPLICATION_MODES
    ):
        return None
    profile = plan.get("source_visual_style")
    if not isinstance(profile, dict):
        raise fail("replication requires source_visual_style")
    normalized: dict[str, str] = {}
    for field in SOURCE_VISUAL_STYLE_FIELDS:
        value = profile.get(field)
        if not isinstance(value, str) or not value.strip():
            raise fail(f"source_visual_style.{field} must be non-empty English control text")
        normalized[field] = value.strip()
    return normalized


def validate_first_frame(
    segment: dict[str, Any], raw_seconds: float
) -> dict[str, Any]:
    """Validate the single entering-state image decision for one 10s Segment."""
    validate_beats(segment, raw_seconds)
    first_frame = segment.get("first_frame")
    if not isinstance(first_frame, dict):
        raise fail(f"{segment.get('segment_id', '<unknown>')}: first_frame must be an object")
    for field in ("camera", "composition", "static_moment", "performance", "continuity"):
        if not isinstance(first_frame.get(field), str) or not first_frame[field].strip():
            raise fail(f"first_frame.{field} must be a non-empty string")
    if first_frame.get("human_presence") not in FIRST_FRAME_HUMAN_PRESENCE:
        raise fail(
            "first_frame.human_presence must be one of "
            f"{', '.join(sorted(FIRST_FRAME_HUMAN_PRESENCE))}"
        )
    if "time" in first_frame and number(first_frame["time"], "first_frame.time") != 0:
        raise fail("first_frame.time must be 0")
    return first_frame


def validate_inputs(segment: dict[str, Any], job_kind: str) -> list[dict[str, Any]]:
    inputs = segment.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: inputs must be a non-empty list")
    allowed_roles = IMAGE_ROLES if job_kind == "first_frame_image" else VIDEO_ROLES
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
    if job_kind == "first_frame_image" and segment.get("product_visible"):
        product_anchors = [item for item in inputs if item["role"] == "product_anchor"]
        if len(product_anchors) != 1 or product_anchors[0]["position"] != 1:
            raise fail("a visible first-frame product requires exactly one product_anchor at input position 1")
        subject_anchor = next((item for item in inputs if item["role"] == "subject_anchor"), None)
        scene_reference = next(
            (item for item in inputs if item["role"] == SOURCE_SCENE_REFERENCE_ROLE),
            None,
        )
        if (
            subject_anchor is not None
            and scene_reference is not None
            and subject_anchor["position"] > scene_reference["position"]
        ):
            raise fail(
                "when both subject_anchor and source_scene_reference are routed, "
                "subject_anchor must precede source_scene_reference"
            )
    if sum(item["role"] == SOURCE_SCENE_REFERENCE_ROLE for item in inputs) > 1:
        raise fail("a Segment may use at most one source_scene_reference")
    return sorted(inputs, key=lambda item: item["position"])


def validate_subject_strategy(
    segment: dict[str, Any], replication_mode: str | None, inputs: list[dict[str, Any]]
) -> str | None:
    if replication_mode not in REPLICATION_MODES:
        return None
    strategy = segment.get("subject_strategy")
    if strategy not in SUBJECT_STRATEGIES:
        raise fail(f"{segment.get('segment_id', '<unknown>')}: replication requires subject_strategy")
    roles = [item["role"] for item in inputs]
    source_counts_ok = all(roles.count(role) == 1 for role in SOURCE_FRAME_ROLES)
    if strategy == "preserve_source_subject":
        if SOURCE_SCENE_REFERENCE_ROLE in roles:
            raise fail("source_scene_reference is available only for structure_only")
        if replication_mode not in HIGH_FIDELITY_REPLICATION_MODES or not source_counts_ok:
            raise fail("preserve_source_subject requires high-fidelity replication and exactly two source frames")
        if "subject_anchor" in roles:
            raise fail("preserve_source_subject forbids subject_anchor")
    elif strategy == "replace_subject":
        if SOURCE_SCENE_REFERENCE_ROLE in roles:
            raise fail("source_scene_reference is available only for structure_only")
        if replication_mode not in HIGH_FIDELITY_REPLICATION_MODES or not source_counts_ok:
            raise fail("replace_subject requires high-fidelity replication and exactly two source frames")
        if roles.count("subject_anchor") != 1:
            raise fail("replace_subject requires exactly one subject_anchor")
    else:
        if replication_mode != "structure_replication":
            raise fail("structure_only requires structure_replication")
        if any(role in roles for role in SOURCE_FRAME_ROLES):
            raise fail("structure_only forbids source frames as generation inputs")
        if roles.count(SOURCE_SCENE_REFERENCE_ROLE) > 1:
            raise fail("structure_only permits at most one source_scene_reference")
        if roles.count("subject_anchor") != 1:
            raise fail("structure_only requires exactly one subject_anchor")
    return str(strategy)


def validate_target_time_range(
    segment: dict[str, Any],
    index: int,
    raw_seconds: float,
    *,
    expected_start: float | None = None,
    expected_duration: float | None = None,
) -> None:
    value = segment.get("target_time_range")
    if not isinstance(value, dict):
        raise fail(f"{segment.get('segment_id', '<unknown>')}: target_time_range must be an object")
    start = number(value.get("start"), "target_time_range.start")
    end = number(value.get("end"), "target_time_range.end")
    start_expected = index * raw_seconds if expected_start is None else expected_start
    duration_expected = raw_seconds if expected_duration is None else expected_duration
    expected_end = start_expected + duration_expected
    if abs(start - start_expected) > 1e-6 or abs(end - expected_end) > 1e-6:
        raise fail(
            f"{segment.get('segment_id', '<unknown>')}: target_time_range must be "
            f"{start_expected:g}–{expected_end:g}s"
        )


def validate_source_narrative_mapping(segment: dict[str, Any], replication_mode: str | None) -> list[str]:
    if replication_mode not in REPLICATION_MODES:
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
    if job_kind not in {"first_frame_image", "final_video"}:
        raise fail("job_kind must be first_frame_image or final_video")
    if plan.get("prompt_language") != "en":
        raise fail("prompt_language must be en")
    if plan.get("target_spoken_language") not in {"th", "zh-CN"}:
        raise fail("target_spoken_language must be locked to th or zh-CN")
    raw_seconds = number(plan.get("raw_segment_seconds"), "raw_segment_seconds")
    if raw_seconds <= 0:
        raise fail("raw_segment_seconds must be positive")
    if job_kind == "first_frame_image":
        versions = plan.get("versions")
        if versions is not None and versions != ["A", "B"]:
            raise fail("first_frame_image versions must be exactly ['A', 'B']")
        if versions == ["A", "B"]:
            specs = plan.get("version_specs")
            if isinstance(specs, dict):
                deltas = [specs.get(version, {}).get("variant_delta") if isinstance(specs.get(version), dict) else None for version in versions]
                if all(isinstance(delta, str) and delta.strip() for delta in deltas) and deltas[0].strip() == deltas[1].strip():
                    raise fail("A/B version_specs must declare different variant_delta values")
        if plan.get("executor") != FIXED_FIRST_FRAME_EXECUTOR:
            raise fail(f"first_frame_image executor must be {FIXED_FIRST_FRAME_EXECUTOR}; Flow2API image generation is forbidden")
        if plan.get("model") != FIXED_FIRST_FRAME_MODEL:
            raise fail(f"first_frame_image model must be exactly {FIXED_FIRST_FRAME_MODEL}")
        if plan.get("generation_unit") != TARGET_PRODUCTION_UNIT:
            raise fail(f"first_frame_image generation_unit must be {TARGET_PRODUCTION_UNIT}")
        if abs(raw_seconds - FIXED_RAW_SEGMENT_SECONDS) > 1e-6:
            raise fail(f"first_frame_image raw_segment_seconds must be {FIXED_RAW_SEGMENT_SECONDS}")
        target_seconds = number(plan.get("target_duration_seconds"), "target_duration_seconds")
        if target_seconds <= 0 or abs(target_seconds % raw_seconds) > 1e-6:
            raise fail("first_frame_image target_duration_seconds must be positive and divisible by raw_segment_seconds")
        first_frame_layout = plan.get("first_frame_layout")
        if not isinstance(first_frame_layout, dict) or first_frame_layout.get("aspect_ratio") != FIXED_FIRST_FRAME_RATIO:
            raise fail("first_frame_image output must declare aspect_ratio=9:16")
        expected_output = {
            "size": FIXED_FIRST_FRAME_SIZE,
            "quality": FIXED_FIRST_FRAME_QUALITY,
            "format": FIXED_FIRST_FRAME_FORMAT,
        }
        if plan.get("image_output") != expected_output:
            raise fail(
                "first_frame_image image_output must be "
                f"{FIXED_FIRST_FRAME_SIZE}/high/png"
            )
        positive_integer(
            plan.get("candidates_per_segment"), "candidates_per_segment"
        )
        if plan.get("common_constraints"):
            raise fail(
                "first_frame_image plans must use visual_continuity instead of common_constraints"
            )
        validate_source_visual_style(plan)
    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        raise fail("segments must be a non-empty list")
    if job_kind == "first_frame_image":
        expected_count = int(float(plan["target_duration_seconds"]) / raw_seconds)
        if len(segments) != expected_count:
            raise fail(
                f"first_frame_image requires {expected_count} target production Segment(s) for "
                f"{plan['target_duration_seconds']:g}s"
            )
    if job_kind == "final_video":
        target_seconds = number(plan.get("target_duration_seconds"), "target_duration_seconds")
        if target_seconds <= 0:
            raise fail("final_video target_duration_seconds must be positive")
        planned_seconds = 0.0
        for index, planned_segment in enumerate(segments):
            if not isinstance(planned_segment, dict):
                raise fail("segment must be an object")
            local_seconds = segment_seconds_for(plan, planned_segment)
            if index < len(segments) - 1 and local_seconds != FIXED_RAW_SEGMENT_SECONDS:
                raise fail("only the final-video Segment may use a 4-second, 6-second, or 8-second tail")
            segment_model_for(plan, planned_segment)
            planned_seconds += local_seconds
        if abs(planned_seconds - target_seconds) > 1e-6:
            raise fail(
                f"final_video duration plan totals {planned_seconds:g}s, "
                f"expected target_duration_seconds {target_seconds:g}s"
            )
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
    timeline_cursor = 0.0
    for segment_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise fail("segment must be an object")
        segment_id = segment.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id or segment_id in seen:
            raise fail("each segment_id must be unique and non-empty")
        seen.add(segment_id)
        local_seconds = segment_seconds_for(plan, segment)
        segment_model_for(plan, segment)
        validate_beats(segment, local_seconds)
        inputs = validate_inputs(segment, job_kind)
        if job_kind == "first_frame_image":
            validate_product_visual_lock(segment)
            validate_first_frame(segment, raw_seconds)
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
        if job_kind == "final_video":
            validate_target_time_range(
                segment,
                segment_index,
                raw_seconds,
                expected_start=timeline_cursor,
                expected_duration=local_seconds,
            )
            timeline_cursor += local_seconds
        if job_kind == "first_frame_image" and plan.get("replication_mode") in HIGH_FIDELITY_REPLICATION_MODES:
            roles = [item["role"] for item in inputs]
            for role in SOURCE_FRAME_ROLES:
                if roles.count(role) != 1:
                    raise fail(f"{segment_id}: high-fidelity replication requires exactly one {role}")
        if job_kind == "first_frame_image":
            validate_subject_strategy(segment, plan.get("replication_mode"), inputs)
        if job_kind == "first_frame_image" and segment.get("dialogue"):
            raise fail("first-frame image plans must not contain dialogue")


def timing_lines(beats: list[dict[str, Any]]) -> list[str]:
    return [f"{beat['start']:.1f}–{beat['end']:.1f}s: {beat['description']}" for beat in beats]


def role_lines(inputs: list[dict[str, Any]]) -> list[str]:
    return [f"Input {item['position']} → {item['role']}: {item['reason']}" for item in inputs]


def compile_first_frame(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    director_output = direct_segment(
        segment,
        variant=str(segment.get("_director_variant", "A")),
        variant_delta=segment.get("_director_variant_delta"),
    )
    first_frame_layout = plan["first_frame_layout"]
    inputs = validate_inputs(segment, "first_frame_image")
    continuity = validate_string_list(
        segment.get("visual_continuity"),
        f"{segment.get('segment_id', '<unknown>')}.visual_continuity",
    )
    constraints = validate_string_list(
        segment.get("hard_constraints", []),
        f"{segment.get('segment_id', '<unknown>')}.hard_constraints",
        allow_empty=True,
    )
    product_visual_lock = validate_product_visual_lock(segment)
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
        if product_visual_lock is not None:
            authority.append(
                "Input 1 has highest product-identity priority. Later subject and scene "
                "references must not alter, hide, omit, replace, reconnect, or reorient "
                "the locked product structure."
            )
    subject_anchor = next((item for item in inputs if item["role"] == "subject_anchor"), None)
    if subject_anchor is not None:
        authority.append(
            f"Input {subject_anchor['position']} is the subject identity authority. "
            "Keep the same identity, markings, proportions, age, accessories, and body features "
            "at the Segment boundary and across Segment transitions."
        )
    subject = segment.get("subject_identity")
    if isinstance(subject, str) and subject.strip():
        authority.append(subject.strip())
    scene_reference = next((item for item in inputs if item["role"] == SOURCE_SCENE_REFERENCE_ROLE), None)
    if scene_reference is not None:
        authority.append(
            f"Input {scene_reference['position']} is a source scene-space reference only. Preserve its spatial layout, camera direction, lighting, background geometry, subject scale and action staging; replace its people, animals, products, text, logos and source-specific hardware with the target authorities."
        )
    strategy = validate_subject_strategy(segment, plan.get("replication_mode"), inputs)
    if strategy == "preserve_source_subject":
        authority.append("Preserve the source person or animal exactly; replace only the source product using the target product anchor. Do not add or redesign a subject.")
    elif strategy == "replace_subject":
        authority.append("The target subject anchor overrides source-subject identity. Replace subject and product in one generation step; do not create an empty-scene intermediate.")
    elif strategy == "structure_only":
        if scene_reference is None:
            authority.append("Source action frames are planning evidence only and are not generation inputs. Target product and subject anchors own identity.")
        else:
            authority.append("The source scene-space reference controls environment and spatial composition only. Target product and subject anchors own identity; do not copy the source subject, product, text or hardware mechanism.")
    validate_source_narrative_mapping(segment, plan.get("replication_mode"))
    first_frame = director_output["first_frame"]
    source_visual_style = validate_source_visual_style(plan)
    style_lines = (
        [source_visual_style[field] for field in SOURCE_VISUAL_STYLE_FIELDS]
        if source_visual_style is not None
        else []
    )
    negatives = list(dict.fromkeys([
        "No readable text, captions, logos, watermarks, UI, grids, contact sheets, dividers, or borders.",
        "No duplicate product or subject, extra people or body parts, malformed hands, or fact-incompatible product structure or action.",
        *negative_constraints,
    ]))
    return "\n\n".join([
        "REFERENCE IMAGE ROLE\n" + "\n".join(authority),
        "OUTPUT SPECIFICATION\n"
        f"Generate exactly one {first_frame_layout['aspect_ratio']} portrait first-frame image for the {plan['raw_segment_seconds']:g}-second target production Segment. "
        "Show one static entering state at local t=0; do not generate a grid, contact sheet, multiple panels, divider or border.",
        "CREATIVE INTENT\n" + f"Viewer read: {director_output['variant_delta']}",
        "CAMERA OPERATOR VIEWPOINT\n" + "\n".join([
            f"Camera: {first_frame['camera'].strip()}",
            f"Composition: {first_frame['composition'].strip()}",
            f"Human presence: {FIRST_FRAME_HUMAN_PRESENCE[first_frame['human_presence']]}",
        ]),
        "SCENE EVENT\n" + "\n".join([
            f"Local time: {number(first_frame.get('time', 0), 'first_frame.time'):.1f}s",
            f"Static moment: {first_frame['static_moment'].strip()}",
            f"Continuity: {first_frame['continuity'].strip()}",
        ]),
        "SUBJECT PERFORMANCE\n" + f"Performance: {first_frame['performance'].strip()}",
        "PRODUCT LOCK\n" + (
            "\n".join([item for item in [product_visual_lock, *constraints] if item])
            if product_visual_lock or constraints
            else "Use only the approved product and action facts for this Segment."
        ),
        "PHONE IMAGE TEXTURE\n" + "\n".join([*style_lines, *continuity]),
        "NEGATIVE CONSTRAINTS\n" + "\n".join(negatives),
    ])


def compile_video(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    local_seconds = segment_seconds_for(plan, segment)
    video_model = segment_model_for(plan, segment)
    inputs = validate_inputs(segment, "final_video")
    common_constraints = [
        item for item in plan.get("common_constraints", [])
        if isinstance(item, str) and item.strip()
    ]
    hard_constraints = [
        item for item in segment.get("hard_constraints", [])
        if isinstance(item, str) and item.strip()
    ]
    negative_constraints = [
        item for item in segment.get("negative_constraints", [])
        if isinstance(item, str) and item.strip()
    ]
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
    camera = segment.get("camera")
    if not isinstance(camera, str) or not camera.strip():
        camera = "Use the approved camera direction and point of view for this Segment."
    visual_style = segment.get("visual_style")
    if not isinstance(visual_style, str) or not visual_style.strip():
        visual_style = "Use the visual style established by the reference and approved constraints."
    if common_constraints:
        visual_style = "\n".join([visual_style.strip(), *common_constraints])
    action_lines = [subject]
    if hard_constraints:
        action_lines.extend(hard_constraints)
    else:
        action_lines.append("Use only the approved action and product facts for this Segment.")
    return "\n\n".join([
        "Reference:\n" + "\n".join(role_lines(inputs)),
        "Subject & Action:\n" + "\n".join(action_lines),
        "Camera:\n" + camera.strip(),
        "Visual Style:\n" + visual_style,
        "Continuity & Timing:\n"
        + f"Segment duration: {local_seconds:g}s. Direct model: {video_model}.\n"
        + continuity
        + "\nTimeline:\n"
        + "\n".join(timing_lines(validate_beats(segment, local_seconds))),
        "Audio:\n" + audio_payload,
        "Unwanted Elements:\n"
        "No captions, subtitles, burned-in text, dialogue transcription, labels, lower thirds, logos, watermarks, UI, or readable text in any language.\n"
        + ("\n".join(negative_constraints) if negative_constraints else "No unapproved visual elements."),
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
        "first_frame" if job_kind == "first_frame_image" else "video"
    )
    for prompt_index, prompt in enumerate(prompts):
        segment_id = prompt["segment_id"]
        version = prompt.get("version")
        version_prefix = f"{version}:" if version else ""
        version_suffix = f":{version}" if version else ""
        if job_kind == "first_frame_image":
            candidate_count = positive_integer(
                candidates_per_segment, "candidates_per_segment"
            )
            attempts = range(1, candidate_count + 1)
        else:
            attempts = range(1, 2)
        for attempt in attempts:
            jobs.append({
                "job_key": f"{version_prefix}{segment_id}:{job_kind}:attempt-{attempt:02d}",
                "prompt_index": prompt_index,
                "segment_id": segment_id,
                **({"version": version} if version else {}),
                "attempt": attempt,
                "content_id_template": (
                    f"{{script_record_id}}{version_suffix}:{segment_id}:attempt-{attempt:02d}"
                ),
                "idempotency_key_template": (
                    f"{{run_id}}{version_suffix}:{segment_id}:{idempotency_kind}:{attempt}"
                ),
            })
    return jobs


def build_submission_policy(job_kind: str, job_count: int) -> dict[str, Any]:
    is_batch = job_count >= BATCH_SUBMISSION_THRESHOLD
    stage_name = "first_frame" if job_kind == "first_frame_image" else "video"
    if job_kind == "first_frame_image":
        return {
            "scope": BATCH_SCOPE,
            "ready_job_count": job_count,
            "batch_threshold": BATCH_SUBMISSION_THRESHOLD,
            "method": "gpt_image_2_5_concurrent" if is_batch else "gpt_image_2_5_single",
            "max_concurrency": DEFAULT_FIRST_FRAME_CONCURRENCY if is_batch else 1,
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
        "batch_kind": "image" if job_kind == "first_frame_image" else "video",
        "batch_id_template": f"{{run_id}}:{stage_name}:initial",
        "single_submit_allowed_only_when": [
            "one_ready_job",
            "one_repair_job",
            "recorded_batch_unavailable",
        ],
    }


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    validate_plan(plan)
    compiler = compile_first_frame if plan["job_kind"] == "first_frame_image" else compile_video
    candidates_per_segment = (
        positive_integer(
            plan.get("candidates_per_segment"), "candidates_per_segment"
        )
        if plan["job_kind"] == "first_frame_image"
        else None
    )
    explicit_versions = plan.get("versions")
    versions = explicit_versions if isinstance(explicit_versions, list) and explicit_versions else [None]
    if plan["job_kind"] == "first_frame_image" and any(version not in {"A", "B"} for version in versions if version is not None):
        raise fail("first-frame versions must be A or B")
    prompts = []
    for version in versions:
        for source_segment in plan["segments"]:
            segment = dict(source_segment)
            if version is not None:
                segment["_director_variant"] = version
                specs = plan.get("version_specs")
                if isinstance(specs, dict) and isinstance(specs.get(version), dict):
                    segment["_director_variant_delta"] = specs[version].get("variant_delta")
            compiled_prompt = compiler(plan, segment)
            dialogue = segment.get("dialogue", [])
            validate_english_control_prompt(compiled_prompt, dialogue)
            director_output = (
                direct_segment(
                    segment,
                    variant=version or "A",
                    variant_delta=segment.get("_director_variant_delta"),
                )
                if plan["job_kind"] == "first_frame_image"
                else None
            )
            prompts.append({
                "segment_id": segment["segment_id"],
                **({"version": version} if version else {}),
                "target_time_range": segment.get("target_time_range"),
                "segment_seconds": segment_seconds_for(plan, segment),
                "video_model": segment_model_for(plan, segment),
                "source_narrative_segment_ids": segment.get("source_narrative_segment_ids", []),
                "subject_strategy": segment.get("subject_strategy"),
                "product_visual_lock": validate_product_visual_lock(segment),
                "visual_continuity": segment.get("visual_continuity"),
                "first_frame": segment.get("first_frame"),
                "director": director_output,
                "prompt": compiled_prompt,
                "inputs": validate_inputs(segment, plan["job_kind"]),
                "beats": validate_beats(segment, segment_seconds_for(plan, segment)),
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
        "source_visual_style": plan.get("source_visual_style"),
        "generation_unit": plan.get("generation_unit"),
        "prompt_language": plan["prompt_language"],
        "target_spoken_language": plan.get("target_spoken_language"),
        "voiceover_provider": plan.get("voiceover_provider"),
        "omni_audio_policy": plan.get("omni_audio_policy"),
        "target_duration_seconds": plan.get("target_duration_seconds"),
        "raw_segment_seconds": plan["raw_segment_seconds"],
        "duration_plan": [
            {
                "segment_id": segment["segment_id"],
                "segment_seconds": segment_seconds_for(plan, segment),
                "video_model": segment_model_for(plan, segment),
            }
            for segment in plan["segments"]
        ] if plan["job_kind"] == "final_video" else None,
        "first_frame_layout": plan.get("first_frame_layout"),
        "image_output": plan.get("image_output"),
        "versions": [version for version in versions if version is not None],
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
    if bundle["job_kind"] == "first_frame_image":
        print(
            f"Wrote {len(bundle['prompts'])} logical Segment prompt(s) and "
            f"{bundle['expected_candidate_job_count']} candidate Job(s): {args.out}"
        )
    else:
        print(f"Wrote {len(bundle['prompts'])} prompt(s): {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
