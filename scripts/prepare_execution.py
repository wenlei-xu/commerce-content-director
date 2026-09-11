#!/usr/bin/env python3
"""Adapt a Markdown creation workbook into a generation execution plan.

The adapter copies authored segment content. It never creates a missing visual
event, action, camera choice, interaction template or prompt.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from workbook import load_and_validate


FINAL_VIDEO_MODELS = {
    4: "gemini_omni_r2v_portrait_4s",
    6: "gemini_omni_r2v_portrait_6s",
    8: "gemini_omni_r2v_portrait_8s",
    10: "omni_portrait",
}
SPOKEN_LANGUAGES = {"zh-CN", "th"}


def _metadata_value(metadata: dict[str, str], *names: str, default: str = "") -> str:
    for name in names:
        value = metadata.get(name)
        if value:
            return value.strip()
    return default


def _prompt_path(prompt_dir: Path, segment_id: str, stage: str) -> Path | None:
    for suffix in (".md", ".txt"):
        candidate = prompt_dir / f"{segment_id}.{stage}.prompt{suffix}"
        if candidate.is_file():
            return candidate
    return None


def _load_assets(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("assets file must be a JSON object")
    return value


def _asset_roles(assets: dict[str, Any], segment_id: str) -> list[dict[str, Any]]:
    value = assets.get(segment_id, assets.get("default", []))
    if isinstance(value, dict):
        value = value.get("inputs", [])
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ValueError(f"assets for {segment_id} must be a list of input-role objects")
    return value


def build_plan(
    workbook_path: Path,
    *,
    stage: str,
    prompt_dir: Path | None = None,
    segment_ids: set[str] | None = None,
    require_prompts: bool = False,
    assets_path: Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    workbook = load_and_validate(workbook_path)
    selected = [
        segment for segment in workbook["segments"]
        if not segment_ids or segment["segment_id"] in segment_ids
    ]
    if not selected:
        raise ValueError("no requested segment exists in the workbook")
    if segment_ids:
        missing = segment_ids - {segment["segment_id"] for segment in selected}
        if missing:
            raise ValueError(f"unknown segment(s): {', '.join(sorted(missing))}")

    assets = _load_assets(assets_path)
    metadata = workbook["metadata"]
    spoken_language = _metadata_value(metadata, "目标口播语言", "目标语言", default="zh-CN")
    if spoken_language not in SPOKEN_LANGUAGES:
        raise ValueError("目标口播语言 must be zh-CN or th")
    audio_mode = _metadata_value(metadata, "音频模式", default="spoken")
    if audio_mode not in {"spoken", "sparse_spoken", "natural_sound_only"}:
        raise ValueError("音频模式 must be spoken, sparse_spoken or natural_sound_only")

    digest = workbook["workbook_digest"]
    resolved_run_id = run_id or f"RUN-{digest[:12]}-{stage}"
    execution_segments: list[dict[str, Any]] = []
    for segment in selected:
        duration = float(segment["segment_seconds"])
        if duration not in FINAL_VIDEO_MODELS:
            raise ValueError(
                f"{segment['segment_id']}: duration must be exactly 4, 6, 8 or 10 seconds"
            )
        prompt_path = _prompt_path(prompt_dir, segment["segment_id"], stage) if prompt_dir else None
        prompt = prompt_path.read_text(encoding="utf-8").strip() if prompt_path else ""
        if require_prompts and not prompt:
            raise ValueError(
                f"{segment['segment_id']}: missing Agent prompt; expected "
                f"<segment_id>.{stage}.prompt.md"
            )
        execution_segments.append({
            "segment_id": segment["segment_id"],
            "target_time_range": {"start": segment["start"], "end": segment["end"]},
            "segment_seconds": int(duration),
            "voiceover": segment["voiceover"],
            "visual_event": segment["visual_event"],
            "continuity": segment["continuity"],
            "must_show": segment["must_show"],
            "beat_id": segment["beat_id"],
            "asset_roles": _asset_roles(assets, segment["segment_id"]),
            "prompt": prompt,
            "prompt_source": str(prompt_path.resolve()) if prompt_path else "",
            "prompt_status": "ready" if prompt else "required",
            "status": "ready" if prompt else "prompt_required",
        })

    max_end = max(float(segment["end"]) for segment in selected)
    return {
        "schema": "commerce-execution-plan-v1",
        "run_id": resolved_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "workbook_path": workbook["workbook_path"],
        "workbook_revision": workbook["workbook_revision"],
        "workbook_digest": digest,
        "stage": stage,
        "prompt_language": "en",
        "target_spoken_language": spoken_language,
        "audio_mode": audio_mode,
        "target_duration_seconds": max_end,
        "segments": execution_segments,
        "source_metadata": metadata,
        "execution_policy": {
            "prompt_author": "agent",
            "request_builder": "prepare_execution",
            "missing_prompt": "stop",
            "no_default_action": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--stage", choices=("first_frame_image", "final_video"), required=True)
    parser.add_argument("--prompt-dir", type=Path)
    parser.add_argument("--segment-id", action="append", dest="segment_ids")
    parser.add_argument("--require-prompts", action="store_true")
    parser.add_argument("--assets", type=Path, help="JSON map of segment IDs to ordered asset roles")
    parser.add_argument("--run-id")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = build_plan(
            args.workbook,
            stage=args.stage,
            prompt_dir=args.prompt_dir,
            segment_ids=set(args.segment_ids or []),
            require_prompts=args.require_prompts,
            assets_path=args.assets,
            run_id=args.run_id,
        )
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "run_id": plan["run_id"], "segments": len(plan["segments"]), "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
