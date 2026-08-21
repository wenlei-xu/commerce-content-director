#!/usr/bin/env python3
"""Regression checks for prompt compilation, variable beats, and bundle validation."""

from __future__ import annotations

import copy

from compile_generation_prompts import compile_plan
from validate_prompt_bundle import validate_bundle


IMAGE_PLAN = {
    "schema": "commerce-generation-prompt-plan-v1",
    "job_kind": "storyboard_image",
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


def main() -> None:
    bundle = compile_plan(IMAGE_PLAN)
    assert not validate_bundle(bundle, {"en", "zh-CN"})
    prompt = bundle["prompts"][0]["prompt"]
    assert "0.0–1.5s" in prompt
    assert "1.5–4.0s" in prompt

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
