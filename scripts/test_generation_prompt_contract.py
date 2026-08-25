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
    "candidates_per_segment": 2,
    "storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"},
    "segments": [{
        "segment_id": "Segment-01",
        "target_time_range": {"start": 0, "end": 10},
        "product_visible": True,
        "visual_continuity": [
            "Natural handheld phone-video texture.",
            "Use the same room, floor surface and natural light across all four panels.",
        ],
        "inputs": [
            {"position": 1, "role": "product_anchor", "asset_id": "product", "sha256": "a" * 64, "clean_for_generation": True, "reason": "Product appears in the proof beat."},
            {"position": 2, "role": "subject_anchor", "asset_id": "subject", "sha256": "b" * 64, "clean_for_generation": True, "reason": "The dog recurs across the Segment."},
        ],
        "beats": [
            {
                "panel": "top_left", "start": 0, "end": 1.5,
                "camera": "Tight handheld close-up.",
                "description": "A frozen hook moment.",
                "continuity": "Opening state in the same room and light.",
                "human_presence": "none",
            },
            {
                "panel": "top_right", "start": 1.5, "end": 4,
                "camera": "Product-forward medium close-up.",
                "description": "A frozen product introduction moment.",
                "continuity": "Carry forward the same room, dog and product scale.",
                "human_presence": "one_hand",
            },
            {
                "panel": "bottom_left", "start": 4, "end": 7,
                "camera": "Unobstructed proof close-up.",
                "description": "One directly observable proof instant.",
                "continuity": "Carry forward the exact product orientation.",
                "human_presence": "one_hand",
            },
            {
                "panel": "bottom_right", "start": 7, "end": 10,
                "camera": "Natural reaction medium shot.",
                "description": "A frozen reaction and closing state.",
                "continuity": "Same scene, light, product and subject.",
                "human_presence": "none",
            },
        ],
        "hard_constraints": ["Use only the approved product interaction path."],
        "negative_constraints": ["No readable text."],
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
    assert bundle["candidates_per_segment"] == 2
    assert bundle["expected_candidate_job_count"] == 2
    assert bundle["expected_job_count"] == 2
    assert bundle["submission_policy"]["method"] == "flow_submit_batch"
    assert bundle["submission_policy"]["scope"] == "single_script_single_stage"
    assert len(bundle["execution_jobs"]) == 2
    assert bundle["execution_jobs"][0]["idempotency_key_template"] == (
        "{run_id}:Segment-01:storyboard:1"
    )
    assert bundle["prompts"][0]["candidate_attempts"] == [1, 2]
    assert bundle["prompts"][0]["visual_continuity"] == IMAGE_PLAN["segments"][0]["visual_continuity"]
    prompt = bundle["prompts"][0]["prompt"]
    assert "0.0–1.5s" in prompt
    assert "1.5–4.0s" in prompt
    assert "target production storyboard board" in prompt
    assert "OUTPUT SPECIFICATION" in prompt
    assert "GLOBAL VISUAL CONTINUITY" in prompt
    assert "REFERENCE AND IDENTITY AUTHORITY" in prompt
    assert "FOUR STATIC KEYFRAMES" in prompt
    assert "RHYTHM AUTHORITY" not in prompt
    assert "Mapped source narratives:" not in prompt
    assert "Do not locally compose" not in prompt
    assert "Do not infer or reinterpret appearance from the product name or category" in prompt
    assert "Top-left (0.0–1.5s)" in prompt
    assert "Human presence: Exactly one natural human hand" in prompt

    missing_visual_continuity = copy.deepcopy(IMAGE_PLAN)
    missing_visual_continuity["segments"][0].pop("visual_continuity")
    try:
        compile_plan(missing_visual_continuity)
    except ValueError as error:
        assert "visual_continuity" in str(error)
    else:
        raise AssertionError("storyboard plans must declare global visual continuity")

    legacy_common_constraints = copy.deepcopy(IMAGE_PLAN)
    legacy_common_constraints["common_constraints"] = ["Legacy mixed constraint."]
    try:
        compile_plan(legacy_common_constraints)
    except ValueError as error:
        assert "visual_continuity instead of common_constraints" in str(error)
    else:
        raise AssertionError("storyboard plans must separate visual continuity from other facts")

    missing_panel_keyframe = copy.deepcopy(IMAGE_PLAN)
    missing_panel_keyframe["segments"][0]["beats"].pop()
    missing_panel_keyframe["segments"][0]["beats"][-1]["end"] = 10
    try:
        compile_plan(missing_panel_keyframe)
    except ValueError as error:
        assert "exactly four static panel keyframes" in str(error)
    else:
        raise AssertionError("storyboard plans must define exactly four static panel keyframes")

    missing_continuity = copy.deepcopy(IMAGE_PLAN)
    missing_continuity["segments"][0]["beats"][1].pop("continuity")
    try:
        compile_plan(missing_continuity)
    except ValueError as error:
        assert "continuity" in str(error)
    else:
        raise AssertionError("every storyboard keyframe must declare inherited continuity")

    leaked_workflow_metadata = copy.deepcopy(bundle)
    leaked_workflow_metadata["prompts"][0]["prompt"] += "\nMapped source narratives: SourceNarrative-01."
    assert any(
        "workflow metadata" in error
        for error in validate_bundle(leaked_workflow_metadata, {"en", "zh-CN"})
    )

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
    assert thirty_second_bundle["expected_candidate_job_count"] == 6
    assert thirty_second_bundle["expected_job_count"] == 6
    assert thirty_second_bundle["submission_policy"]["method"] == "flow_submit_batch"
    assert len(thirty_second_bundle["execution_jobs"]) == 6
    assert not validate_bundle(thirty_second_bundle, {"en", "zh-CN"})

    single_job_plan = copy.deepcopy(IMAGE_PLAN)
    single_job_plan["candidates_per_segment"] = 1
    single_job_bundle = compile_plan(single_job_plan)
    assert single_job_bundle["submission_policy"]["method"] == "flow_submit_image"
    assert not validate_bundle(single_job_bundle, {"en", "zh-CN"})

    wrong_submission_policy = copy.deepcopy(bundle)
    wrong_submission_policy["submission_policy"]["method"] = "flow_submit_image"
    assert any(
        "flow_submit_batch" in error
        for error in validate_bundle(wrong_submission_policy, {"en", "zh-CN"})
    )

    missing_candidate_count = copy.deepcopy(IMAGE_PLAN)
    missing_candidate_count.pop("candidates_per_segment")
    try:
        compile_plan(missing_candidate_count)
    except ValueError as error:
        assert "candidates_per_segment" in str(error)
    else:
        raise AssertionError("storyboard plans must declare the candidate count")

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
    video_plan["common_constraints"] = ["Natural handheld phone-video texture."]
    video_plan["job_kind"] = "final_video"
    video_plan["target_spoken_language"] = "th"
    video_plan["voiceover_provider"] = "omni_native"
    video_plan["omni_audio_policy"] = "native_dialogue"
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
    assert video_bundle["submission_policy"]["method"] == "flow_submit_video"

    thirty_second_video_plan = copy.deepcopy(video_plan)
    thirty_second_video_plan["target_duration_seconds"] = 30
    thirty_second_video_plan["segments"] = []
    for index in range(3):
        segment = copy.deepcopy(video_plan["segments"][0])
        segment["segment_id"] = f"Segment-{index + 1:02d}"
        segment["target_time_range"] = {
            "start": index * 10,
            "end": (index + 1) * 10,
        }
        segment["dialogue"][0]["line_id"] = f"line-{index + 1:02d}"
        thirty_second_video_plan["segments"].append(segment)
    thirty_second_video_bundle = compile_plan(thirty_second_video_plan)
    assert thirty_second_video_bundle["expected_job_count"] == 3
    assert (
        thirty_second_video_bundle["submission_policy"]["method"]
        == "flow_submit_batch"
    )
    assert not validate_bundle(thirty_second_video_bundle, {"en", "zh-CN"})

    chinese_video_plan = copy.deepcopy(video_plan)
    chinese_video_plan["target_spoken_language"] = "zh-CN"
    chinese_video_plan["voiceover_provider"] = "doubao_tts_2_0"
    chinese_video_plan["omni_audio_policy"] = "environment_only"
    chinese_video_plan["segments"][0]["dialogue"][0]["text"] = "看看这个菠萝玩具"
    chinese_video_bundle = compile_plan(chinese_video_plan)
    assert not validate_bundle(chinese_video_bundle, {"en"}, {"th", "zh-CN"})
    chinese_omni_prompt = chinese_video_bundle["prompts"][0]["prompt"]
    assert "看看这个菠萝玩具" not in chinese_omni_prompt
    assert "voiceover_provider=doubao_tts_2_0" in chinese_omni_prompt
    assert "omni_audio_policy=environment_only" in chinese_omni_prompt
    assert "No spoken voice, narration, dialogue, singing, humming, or background music" in chinese_omni_prompt
    assert chinese_video_bundle["prompts"][0]["dialogue"][0]["text"] == "看看这个菠萝玩具"

    leaked_chinese_dialogue = copy.deepcopy(chinese_video_bundle)
    leaked_chinese_dialogue["prompts"][0]["prompt"] += "\n7.0–10.0s: 看看这个菠萝玩具"
    leaked_errors = validate_bundle(leaked_chinese_dialogue, {"en"}, {"th", "zh-CN"})
    assert any("must not be sent to Omni" in error for error in leaked_errors)

    wrong_chinese_provider = copy.deepcopy(chinese_video_plan)
    wrong_chinese_provider["voiceover_provider"] = "omni_native"
    try:
        compile_plan(wrong_chinese_provider)
    except ValueError as error:
        assert "doubao_tts_2_0" in str(error)
    else:
        raise AssertionError("Chinese spoken video must use Doubao TTS 2.0")

    chinese_natural_sound = copy.deepcopy(chinese_video_plan)
    chinese_natural_sound["voiceover_provider"] = "none"
    chinese_natural_sound["segments"][0]["audio_mode"] = "natural_sound_only"
    chinese_natural_sound["segments"][0]["dialogue"] = []
    natural_bundle = compile_plan(chinese_natural_sound)
    assert not validate_bundle(natural_bundle, {"en"}, {"th", "zh-CN"})
    assert "voiceover_provider=none" in natural_bundle["prompts"][0]["prompt"]
    assert "Doubao TTS 2.0" not in natural_bundle["prompts"][0]["prompt"]

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
