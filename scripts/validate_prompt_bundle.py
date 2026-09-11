#!/usr/bin/env python3
"""Validate an execution bundle before generation submission."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


HAN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
THAI = re.compile(r"[\u0E00-\u0E7F]")
SUPPORTED_SECONDS = {4, 6, 8, 10}
VIDEO_MODELS = {
    4: "gemini_omni_r2v_portrait_4s",
    6: "gemini_omni_r2v_portrait_6s",
    8: "gemini_omni_r2v_portrait_8s",
    10: "omni_portrait",
}


def validate_bundle(bundle: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if bundle.get("schema") != "commerce-execution-bundle-v1":
        return ["unsupported execution-bundle schema"]
    if bundle.get("stage") not in {"first_frame_image", "final_video"}:
        errors.append("stage must be first_frame_image or final_video")
    if bundle.get("prompt_language") != "en":
        errors.append("prompt_language must be en")
    if not isinstance(bundle.get("workbook_revision"), int) or bundle["workbook_revision"] < 1:
        errors.append("workbook_revision must be a positive integer")
    if not isinstance(bundle.get("workbook_digest"), str) or not bundle["workbook_digest"].strip():
        errors.append("workbook_digest is required")
    prompts = bundle.get("prompts")
    jobs = bundle.get("execution_jobs")
    if not isinstance(prompts, list) or not prompts:
        errors.append("prompts must contain at least one item")
        prompts = []
    if not isinstance(jobs, list) or len(jobs) != len(prompts):
        errors.append("execution_jobs must contain one job per prompt")
        jobs = []
    prompt_ids: list[str] = []
    for index, prompt in enumerate(prompts):
        prefix = f"prompts[{index}]"
        if not isinstance(prompt, dict):
            errors.append(f"{prefix} must be an object")
            continue
        segment_id = prompt.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id.strip():
            errors.append(f"{prefix}.segment_id is required")
            continue
        prompt_ids.append(segment_id)
        seconds = prompt.get("segment_seconds")
        if seconds not in SUPPORTED_SECONDS:
            errors.append(f"{prefix}.segment_seconds must be 4, 6, 8 or 10")
        if not isinstance(prompt.get("visual_event"), str) or not prompt["visual_event"].strip():
            errors.append(f"{prefix}.visual_event is required")
        value = prompt.get("prompt")
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.prompt is required")
        else:
            if HAN.search(value) or THAI.search(value):
                errors.append(f"{prefix}.prompt must use English control text")
            if "Execution constraints:" not in value:
                errors.append(f"{prefix}.prompt is missing compiler execution constraints")
        if not isinstance(prompt.get("asset_roles"), list):
            errors.append(f"{prefix}.asset_roles must be a list")
    if len(set(prompt_ids)) != len(prompt_ids):
        errors.append("prompts contain duplicate segment IDs")
    for index, job in enumerate(jobs):
        prefix = f"execution_jobs[{index}]"
        if not isinstance(job, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if job.get("prompt_index") != index:
            errors.append(f"{prefix}.prompt_index must equal {index}")
        if job.get("segment_id") != prompts[index].get("segment_id"):
            errors.append(f"{prefix}.segment_id must match its prompt")
        if job.get("status") != "ready":
            errors.append(f"{prefix}.status must be ready before submission")
    if bundle.get("expected_job_count") != len(jobs):
        errors.append("expected_job_count does not match execution_jobs")
    stage = bundle.get("stage")
    if stage == "first_frame_image":
        if bundle.get("executor") != "gpt_image_2_5":
            errors.append("first_frame_image executor must be gpt_image_2_5")
        if bundle.get("model") != "gpt-image-2.5":
            errors.append("first_frame_image model must be gpt-image-2.5")
        if bundle.get("image_output") != {"size": "1152x2048", "quality": "high", "format": "png"}:
            errors.append("first_frame_image image_output must be 1152x2048/high/png")
    elif stage == "final_video":
        if bundle.get("executor") != "flow2api_omni":
            errors.append("final_video executor must be flow2api_omni")
        for index, prompt in enumerate(prompts):
            seconds = prompt.get("segment_seconds")
            if seconds in VIDEO_MODELS and prompt.get("video_model") != VIDEO_MODELS[seconds]:
                errors.append(f"prompts[{index}].video_model does not match segment duration")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    args = parser.parse_args()
    try:
        bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
        if not isinstance(bundle, dict):
            raise ValueError("bundle must be an object")
        errors = validate_bundle(bundle)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL {exc}")
        return 2
    if errors:
        print("\n".join(f"FAIL {error}" for error in errors))
        return 1
    print(f"PASS {args.bundle}: {len(bundle['prompts'])} prompt(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
