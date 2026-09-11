#!/usr/bin/env python3
"""Build a generation request bundle from an Agent-authored execution plan."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FINAL_VIDEO_MODELS = {
    4: "gemini_omni_r2v_portrait_4s",
    6: "gemini_omni_r2v_portrait_6s",
    8: "gemini_omni_r2v_portrait_8s",
    10: "omni_portrait",
}
IMAGE_EXECUTOR = "gpt_image_2_5"
IMAGE_MODEL = "gpt-image-2.5"
IMAGE_OUTPUT = {"size": "1152x2048", "quality": "high", "format": "png"}
HAN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")
THAI = re.compile(r"[\u0E00-\u0E7F]")


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _number(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    return float(value)


def _validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    if plan.get("schema") != "commerce-execution-plan-v1":
        raise ValueError("input must be a commerce-execution-plan-v1 created from a Markdown workbook")
    stage = plan.get("stage")
    if stage not in {"first_frame_image", "final_video"}:
        raise ValueError("stage must be first_frame_image or final_video")
    if plan.get("prompt_language") != "en":
        raise ValueError("prompt_language must be en")
    if not isinstance(plan.get("workbook_revision"), int) or plan["workbook_revision"] < 1:
        raise ValueError("workbook_revision must be a positive integer")
    if not isinstance(plan.get("workbook_digest"), str) or not plan["workbook_digest"].strip():
        raise ValueError("workbook_digest is required")
    segments = plan.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("segments must contain at least one entry")
    seen: set[str] = set()
    for index, segment in enumerate(segments, start=1):
        if not isinstance(segment, dict):
            raise ValueError(f"segments[{index}] must be an object")
        segment_id = _require_text(segment.get("segment_id"), f"segments[{index}].segment_id")
        if segment_id in seen:
            raise ValueError(f"{segment_id}: duplicate segment")
        seen.add(segment_id)
        duration = _number(segment.get("segment_seconds"), f"{segment_id}.segment_seconds")
        if duration not in FINAL_VIDEO_MODELS:
            raise ValueError(f"{segment_id}.segment_seconds must be 4, 6, 8 or 10")
        _require_text(segment.get("visual_event"), f"{segment_id}.visual_event")
        prompt = _require_text(segment.get("prompt"), f"{segment_id}.prompt")
        if HAN.search(prompt) or THAI.search(prompt):
            raise ValueError(f"{segment_id}.prompt must use English control text")
        target_range = segment.get("target_time_range")
        if not isinstance(target_range, dict):
            raise ValueError(f"{segment_id}.target_time_range is required")
        start = _number(target_range.get("start"), f"{segment_id}.target_time_range.start")
        end = _number(target_range.get("end"), f"{segment_id}.target_time_range.end")
        if end <= start:
            raise ValueError(f"{segment_id}.target_time_range.end must be greater than start")
        roles = segment.get("asset_roles", [])
        if not isinstance(roles, list) or not all(isinstance(role, dict) for role in roles):
            raise ValueError(f"{segment_id}.asset_roles must be a list of objects")
    return segments


def _technical_tail(plan: dict[str, Any], segment: dict[str, Any]) -> str:
    stage = plan["stage"]
    seconds = int(segment["segment_seconds"])
    lines = [
        "Execution constraints:",
        f"Use exactly one continuous {seconds}-second portrait 9:16 generation segment.",
        "Keep the routed reference identities, product geometry and approved continuity intact.",
        "No captions, subtitles, logos, watermarks, UI, grids, contact sheets or readable text.",
    ]
    if stage == "first_frame_image":
        lines.extend([
            "This is one static entering state at local t=0, not a storyboard or a sequence of panels.",
            "Output exactly one portrait PNG image at 1152x2048, high quality.",
        ])
    else:
        lines.append(f"Use the exact duration-matched video model: {FINAL_VIDEO_MODELS[seconds]}.")
        language = plan.get("target_spoken_language")
        audio_mode = plan.get("audio_mode", "spoken")
        if language == "zh-CN" and audio_mode in {"spoken", "sparse_spoken"}:
            lines.append("Generate environmental sound only; no spoken voice, narration, dialogue, singing or background music. Chinese voiceover is added after generation.")
        elif audio_mode == "natural_sound_only":
            lines.append("Generate environmental sound only; do not speak.")
    return "\n".join(lines)


def compile_plan(plan: dict[str, Any]) -> dict[str, Any]:
    segments = _validate_plan(plan)
    prompts: list[dict[str, Any]] = []
    jobs: list[dict[str, Any]] = []
    for index, segment in enumerate(segments):
        segment_id = segment["segment_id"]
        prompt = f"{segment['prompt'].strip()}\n\n{_technical_tail(plan, segment)}"
        seconds = int(segment["segment_seconds"])
        prompts.append({
            "segment_id": segment_id,
            "workbook_revision": plan["workbook_revision"],
            "workbook_digest": plan["workbook_digest"],
            "target_time_range": segment["target_time_range"],
            "segment_seconds": seconds,
            "video_model": FINAL_VIDEO_MODELS[seconds] if plan["stage"] == "final_video" else None,
            "visual_event": segment["visual_event"],
            "continuity": segment.get("continuity", ""),
            "must_show": segment.get("must_show", ""),
            "asset_roles": segment.get("asset_roles", []),
            "prompt": prompt,
            "prompt_source": segment.get("prompt_source", "agent"),
            "status": "ready",
        })
        jobs.append({
            "job_key": f"{segment_id}:{plan['stage']}:attempt-01",
            "prompt_index": index,
            "segment_id": segment_id,
            "attempt": 1,
            "idempotency_key_template": f"{{run_id}}:{segment_id}:{plan['stage']}:attempt-01",
            "status": "ready",
        })

    return {
        "schema": "commerce-execution-bundle-v1",
        "run_id": plan["run_id"],
        "stage": plan["stage"],
        "workbook_path": plan["workbook_path"],
        "workbook_revision": plan["workbook_revision"],
        "workbook_digest": plan["workbook_digest"],
        "prompt_language": "en",
        "target_spoken_language": plan["target_spoken_language"],
        "audio_mode": plan["audio_mode"],
        "target_duration_seconds": plan["target_duration_seconds"],
        "executor": IMAGE_EXECUTOR if plan["stage"] == "first_frame_image" else "flow2api_omni",
        "model": IMAGE_MODEL if plan["stage"] == "first_frame_image" else None,
        "image_output": IMAGE_OUTPUT if plan["stage"] == "first_frame_image" else None,
        "prompts": prompts,
        "execution_jobs": jobs,
        "expected_job_count": len(jobs),
        "request_policy": {
            "prompt_author": "agent",
            "technical_constraints_added_by": "compiler",
            "submit": "only_ready_jobs",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execution_plan", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.execution_plan.read_text(encoding="utf-8"))
        if not isinstance(plan, dict):
            raise ValueError("execution plan must be an object")
        bundle = compile_plan(plan)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "run_id": bundle["run_id"], "jobs": len(bundle["execution_jobs"]), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
