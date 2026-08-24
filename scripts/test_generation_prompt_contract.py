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
    "generation_unit": "target_production_segment",
    "prompt_language": "en",
    "target_spoken_language": "zh-CN",
    "target_duration_seconds": 10,
    "raw_segment_seconds": 10,
    "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
    "common_constraints": ["Natural handheld phone-video texture."],
    "segments": [{
        "segment_id": "Segment-01",
        "target_time_range": {"start": 0, "end": 10},
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
FULL_REPLICATION_PLAN["segments"][0]["source_narrative_segment_ids"] = ["SourceNarrative-01", "SourceNarrative-02"]
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
    assert "target production storyboard board" in prompt
    assert "RHYTHM AUTHORITY" in prompt

    thirty_second_plan = copy.deepcopy(IMAGE_PLAN)
    thirty_second_plan["target_duration_seconds"] = 30
    thirty_second_plan["segments"] = []
    for index in range(3):
        segment = copy.deepcopy(IMAGE_PLAN["segments"][0])
        segment["segment_id"] = f"Segment-{index + 1:02d}"
        segment["target_time_range"] = {"start": index * 10, "end": (index + 1) * 10}
        thirty_second_plan["segments"].append(segment)
    thirty_second_bundle = compile_plan(thirty_second_plan)
    assert len(thirty_second_bundle["prompts"]) == 3
    assert not validate_bundle(thirty_second_bundle, {"en", "zh-CN"})

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
    structure_plan["segments"][0]["source_narrative_segment_ids"] = ["SourceNarrative-01"]
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

    source_timed_plan = copy.deepcopy(FULL_REPLICATION_PLAN)
    source_timed_plan["raw_segment_seconds"] = 7
    source_timed_plan["target_duration_seconds"] = 7
    source_timed_plan["segments"][0]["target_time_range"] = {"start": 0, "end": 7}
    try:
        compile_plan(source_timed_plan)
    except ValueError as error:
        assert "raw_segment_seconds must be 10" in str(error)
    else:
        raise AssertionError("replication must use the same 10-second production unit as original")

    wrong_layout = copy.deepcopy(IMAGE_PLAN)
    wrong_layout["storyboard"] = {"columns": 1, "rows": 2, "panel_ratio": "9:16"}
    try:
        compile_plan(wrong_layout)
    except ValueError as error:
        assert "2x2 board" in str(error)
    else:
        raise AssertionError("storyboard generation must produce one 2x2 board per target Segment")

    wrong_job_count = copy.deepcopy(IMAGE_PLAN)
    wrong_job_count["target_duration_seconds"] = 20
    try:
        compile_plan(wrong_job_count)
    except ValueError as error:
        assert "requires 2 target production Segment" in str(error)
    else:
        raise AssertionError("Job count must equal target duration divided by 10 seconds")

    missing_source_mapping = copy.deepcopy(FULL_REPLICATION_PLAN)
    missing_source_mapping["segments"][0].pop("source_narrative_segment_ids")
    try:
        compile_plan(missing_source_mapping)
    except ValueError as error:
        assert "source_narrative_segment_ids" in str(error)
    else:
        raise AssertionError("replication target Segments must map source narrative evidence")

    thai_plan = copy.deepcopy(IMAGE_PLAN)
    thai_plan["segments"][0]["beats"][0]["description"] = "ภาษาไทย"
    try:
        compile_plan(thai_plan)
    except ValueError as error:
        assert "control prompt must be English" in str(error)
    else:
        raise AssertionError("Thai storyboard control text must fail during compilation")

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

    chinese_video_plan = copy.deepcopy(video_plan)
    chinese_video_plan["target_spoken_language"] = "zh-CN"
    chinese_video_plan["segments"][0]["dialogue"][0]["text"] = "看看这个菠萝玩具"
    chinese_video_bundle = compile_plan(chinese_video_plan)
    assert not validate_bundle(chinese_video_bundle, {"en"}, {"th", "zh-CN"})

    chinese_control_text = copy.deepcopy(chinese_video_plan)
    chinese_control_text["segments"][0]["subject_identity"] = "只使用同一只狗"
    try:
        compile_plan(chinese_control_text)
    except ValueError as error:
        assert "control prompt must be English" in str(error)
    else:
        raise AssertionError("Chinese dialogue is allowed, but generation control text must remain English")

    missing_language_lock = copy.deepcopy(video_plan)
    missing_language_lock.pop("target_spoken_language")
    try:
        compile_plan(missing_language_lock)
    except ValueError as error:
        assert "target_spoken_language" in str(error)
    else:
        raise AssertionError("generation plans must carry the task-start language lock")

    chinese_control_prompt = copy.deepcopy(IMAGE_PLAN)
    chinese_control_prompt["prompt_language"] = "zh-CN"
    try:
        compile_plan(chinese_control_prompt)
    except ValueError as error:
        assert "prompt_language must be en" in str(error)
    else:
        raise AssertionError("generation control prompts must be English")

    print("generation prompt contract tests passed")


if __name__ == "__main__":
    main()
