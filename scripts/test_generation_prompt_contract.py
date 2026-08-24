#!/usr/bin/env python3
"""Regression checks for prompt compilation, variable beats, and bundle validation."""

from __future__ import annotations

import copy

from compile_generation_prompts import compile_plan
from validate_prompt_bundle import validate_bundle


IMAGE_PLAN = {
    "schema": "commerce-generation-prompt-plan-v1",
    "job_kind": "storyboard_image",
    "executor": "flow2api_mcp",
    "model": "gemini-3.1-flash-image-portrait",
    "prompt_language": "en",
    "raw_segment_seconds": 10,
    "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
    "common_constraints": ["Natural handheld phone-video texture."],
    "segments": [{
        "segment_id": "Segment-01",
        "product_visible": True,
        "inputs": [
            {"position": 1, "role": "product_anchor", "asset_id": "product", "sha256": "a" * 64, "clean_for_generation": True, "reason": "Product appears in the proof beat."},
            {"position": 2, "role": "subject_anchor", "asset_id": "subject", "sha256": "b" * 64, "clean_for_generation": True, "reason": "The dog recurs across the Segment."},
        ],
        "beats": [
            {"start": 0, "end": 1.5, "description": "Hook."},
            {"start": 1.5, "end": 4, "description": "Introduce the product."},
            {"start": 4, "end": 7, "description": "Show the proof action."},
            {"start": 7, "end": 10, "description": "Reaction and CTA state."},
        ],
        "hard_constraints": ["No readable text."],
        "subject_identity": "Use the selected dog only.",
    }],
}


FULL_REPLICATION_PLAN = copy.deepcopy(IMAGE_PLAN)
FULL_REPLICATION_PLAN["replication_mode"] = "full_replication"
FULL_REPLICATION_PLAN["segments"][0]["subject_strategy"] = "replace_subject"
FULL_REPLICATION_PLAN["segments"][0]["inputs"].extend([
    {"position": 3, "role": "source_segment_start", "asset_id": "source-start", "sha256": "c" * 64, "clean_for_generation": True, "reason": "Entering composition and state."},
    {"position": 4, "role": "source_segment_result", "asset_id": "source-result", "sha256": "d" * 64, "clean_for_generation": True, "reason": "Visible payoff and handoff state."},
])


def main() -> None:
    bundle = compile_plan(IMAGE_PLAN)
    assert not validate_bundle(bundle, {"en", "zh-CN"})
    prompt = bundle["prompts"][0]["prompt"]
    assert "0.0–1.5s" in prompt
    assert "1.5–4.0s" in prompt

    gpt_image_plan = copy.deepcopy(IMAGE_PLAN)
    gpt_image_plan["executor"] = "gpt_image"
    try:
        compile_plan(gpt_image_plan)
    except ValueError as error:
        assert "flow2api_mcp" in str(error)
    else:
        raise AssertionError("GPT Image must be rejected for storyboard generation")

    gpt_image_bundle = copy.deepcopy(bundle)
    gpt_image_bundle["executor"] = "gpt_image"
    assert any("flow2api_mcp" in error for error in validate_bundle(gpt_image_bundle, {"en", "zh-CN"}))

    missing_image_model = copy.deepcopy(IMAGE_PLAN)
    missing_image_model.pop("model")
    try:
        compile_plan(missing_image_model)
    except ValueError as error:
        assert "Flow2API catalog model ID" in str(error)
    else:
        raise AssertionError("storyboard generation without a Flow2API model must fail")

    full_bundle = compile_plan(FULL_REPLICATION_PLAN)
    assert not validate_bundle(full_bundle, {"en", "zh-CN"})

    preserve_plan = copy.deepcopy(FULL_REPLICATION_PLAN)
    preserve_plan["segments"][0]["subject_strategy"] = "preserve_source_subject"
    preserve_plan["segments"][0]["inputs"].pop(1)
    for position, item in enumerate(preserve_plan["segments"][0]["inputs"], start=1):
        item["position"] = position
    preserve_bundle = compile_plan(preserve_plan)
    assert not validate_bundle(preserve_bundle, {"en", "zh-CN"})

    preserve_with_subject = copy.deepcopy(FULL_REPLICATION_PLAN)
    preserve_with_subject["segments"][0]["subject_strategy"] = "preserve_source_subject"
    try:
        compile_plan(preserve_with_subject)
    except ValueError as error:
        assert "forbids subject_anchor" in str(error)
    else:
        raise AssertionError("preserve_source_subject with a subject anchor should fail")

    structure_plan = copy.deepcopy(IMAGE_PLAN)
    structure_plan["replication_mode"] = "structure_replication"
    structure_plan["segments"][0]["subject_strategy"] = "structure_only"
    structure_bundle = compile_plan(structure_plan)
    assert not validate_bundle(structure_bundle, {"en", "zh-CN"})

    structure_with_source = copy.deepcopy(structure_plan)
    structure_with_source["segments"][0]["inputs"].append({
        "position": 3, "role": "source_segment_start", "asset_id": "source-start",
        "sha256": "c" * 64, "clean_for_generation": True, "reason": "Should not be routed.",
    })
    try:
        compile_plan(structure_with_source)
    except ValueError as error:
        assert "forbids source frames" in str(error)
    else:
        raise AssertionError("structure_only with source frames should fail")

    missing_result = copy.deepcopy(FULL_REPLICATION_PLAN)
    missing_result["segments"][0]["inputs"] = missing_result["segments"][0]["inputs"][:-1]
    try:
        compile_plan(missing_result)
    except ValueError as error:
        assert "source_segment_result" in str(error)
    else:
        raise AssertionError("full replication without result frame should fail")

    contact_sheet = copy.deepcopy(FULL_REPLICATION_PLAN)
    contact_sheet["segments"][0]["inputs"].append({
        "position": 5, "role": "source_contact_sheet", "asset_id": "source-grid",
        "sha256": "e" * 64, "clean_for_generation": True, "reason": "Legacy grid.",
    })
    try:
        compile_plan(contact_sheet)
    except ValueError as error:
        assert "source_contact_sheet" in str(error)
    else:
        raise AssertionError("full replication with a contact sheet should fail")

    thai_plan = copy.deepcopy(IMAGE_PLAN)
    thai_plan["segments"][0]["beats"][0]["description"] = "ภาษาไทย"
    thai_bundle = compile_plan(thai_plan)
    assert any("Thai control text" in error for error in validate_bundle(thai_bundle, {"en", "zh-CN"}))

    missing_anchor = copy.deepcopy(IMAGE_PLAN)
    missing_anchor["segments"][0]["inputs"] = [missing_anchor["segments"][0]["inputs"][1]]
    missing_anchor["segments"][0]["inputs"][0]["position"] = 1
    try:
        compile_plan(missing_anchor)
    except ValueError as error:
        assert "product_anchor" in str(error)
    else:
        raise AssertionError("visible product without product_anchor should fail")

    video_plan = copy.deepcopy(IMAGE_PLAN)
    video_plan.pop("storyboard")
    video_plan["job_kind"] = "final_video"
    video_plan["target_spoken_language"] = "th"
    video_segment = video_plan["segments"][0]
    video_segment["inputs"] = [
        {"position": 1, "role": "storyboard_board", "asset_id": "board", "sha256": "c" * 64, "clean_for_generation": True, "reason": "Chronology and camera intent."},
        *video_segment["inputs"],
    ]
    for position, item in enumerate(video_segment["inputs"], start=1):
        item["position"] = position
    video_segment["audio_mode"] = "spoken"
    video_segment["dialogue"] = [{"line_id": "line-01", "start": 7, "end": 10, "text": "ลองดูของเล่นชิ้นนี้", "intentional_repeat": False}]
    video_bundle = compile_plan(video_plan)
    assert not validate_bundle(video_bundle, {"en", "zh-CN"})

    print("generation prompt contract tests passed")


if __name__ == "__main__":
    main()
