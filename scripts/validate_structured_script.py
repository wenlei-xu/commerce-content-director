#!/usr/bin/env python3
"""Validate a structured short-video script before it reaches Feishu or storyboard."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REQUIRED_STRATEGY = {
    "target_audience", "viewer_before_state", "viewer_after_state", "content_format",
    "content_angle", "core_idea", "primary_cta",
}
SUBTITLE_MODES = {"auto_from_final_audio", "emphasis_from_final_audio", "none"}
EMPHASIS_STYLES = {"keyword_yellow", "number_pop", "result_pop", "product_accent", "pain_point_red"}
TARGET_SPOKEN_LANGUAGES = {"th", "zh-CN"}
THAI = re.compile(r"[\u0E00-\u0E7F]")
HAN = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF]")


def issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def unique(items: list[dict[str, Any]], key: str, label: str, errors: list[dict[str, str]]) -> set[str]:
    values = [str(item.get(key, "")).strip() for item in items]
    if any(not value for value in values):
        errors.append(issue("MISSING_ID", label, f"{label} requires {key}"))
    if len(values) != len(set(values)):
        errors.append(issue("DUPLICATE_ID", label, f"{label} contains duplicate {key}"))
    return set(values)


def validate(script: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    for key in ("schema_version", "script_id", "script_revision", "direction_id", "runtime", "strategy_snapshot", "hook", "beats", "dialogue", "screen_texts", "segments", "loops", "ending"):
        if key not in script:
            errors.append(issue("MISSING_REQUIRED", key, f"missing {key}"))

    runtime = script.get("runtime") or {}
    target_spoken_language = runtime.get("target_spoken_language")
    if target_spoken_language not in TARGET_SPOKEN_LANGUAGES:
        errors.append(issue("INVALID_TARGET_SPOKEN_LANGUAGE", "runtime.target_spoken_language", "expected th or zh-CN"))
    subtitle_mode = runtime.get("subtitle_mode")
    if subtitle_mode not in SUBTITLE_MODES:
        errors.append(issue("INVALID_SUBTITLE_MODE", "runtime.subtitle_mode", f"expected one of {sorted(SUBTITLE_MODES)}"))
    strategy = script.get("strategy_snapshot") or {}
    missing_strategy = sorted(REQUIRED_STRATEGY - set(strategy))
    if missing_strategy:
        errors.append(issue("MISSING_STRATEGY", "strategy_snapshot", ", ".join(missing_strategy)))

    beats = script.get("beats") or []
    dialogue = script.get("dialogue") or []
    texts = script.get("screen_texts") or []
    segments = script.get("segments") or []
    loops = script.get("loops") or []
    beat_ids = unique(beats, "beat_id", "beats", errors)
    line_ids = unique(dialogue, "line_id", "dialogue", errors)
    text_ids = unique(texts, "text_id", "screen_texts", errors)
    segment_ids = unique(segments, "segment_id", "segments", errors)
    unique(loops, "loop_id", "loops", errors)

    duration = float(runtime.get("target_duration_seconds") or 0)
    ordered_beats = sorted(beats, key=lambda item: float(item.get("start", -1)))
    previous_end = 0.0
    for index, beat in enumerate(ordered_beats):
        start, end = float(beat.get("start", -1)), float(beat.get("end", -1))
        if start < 0 or end <= start:
            errors.append(issue("INVALID_BEAT_TIME", f"beats[{index}]", "beat time range is invalid"))
        if index == 0 and start != 0:
            errors.append(issue("TIMELINE_NOT_ZERO", "beats[0]", "first beat must start at 0"))
        if start != previous_end:
            errors.append(issue("TIMELINE_GAP_OR_OVERLAP", f"beats[{index}]", "beats must be continuous"))
        previous_end = end
        if not str(beat.get("visual_action", "")).strip() or not str(beat.get("product_state", "")).strip():
            errors.append(issue("INCOMPLETE_BEAT", f"beats[{index}]", "visual_action and product_state are required"))
    if duration and previous_end != duration:
        errors.append(issue("DURATION_MISMATCH", "beats", f"beats end at {previous_end}, target is {duration}"))

    segment_by_id = {str(item.get("segment_id")): item for item in segments}
    emphasis_span_count = 0
    for index, line in enumerate(dialogue):
        beat_id, segment_id = str(line.get("beat_id", "")), str(line.get("segment_id", ""))
        if beat_id not in beat_ids:
            errors.append(issue("UNKNOWN_BEAT_REFERENCE", f"dialogue[{index}]", beat_id))
        segment = segment_by_id.get(segment_id)
        if not segment:
            errors.append(issue("UNKNOWN_SEGMENT_REFERENCE", f"dialogue[{index}]", segment_id))
            continue
        start, end = float(line.get("start", -1)), float(line.get("end", -1))
        if start < float(segment.get("start", 0)) or end > float(segment.get("end", 0)) or end <= start:
            errors.append(issue("DIALOGUE_CROSSES_SEGMENT", f"dialogue[{index}]", str(line.get("line_id"))))
        if not str(line.get("text", "")).strip():
            errors.append(issue("EMPTY_DIALOGUE", f"dialogue[{index}]", str(line.get("line_id"))))
        line_text = str(line.get("text", ""))
        if target_spoken_language == "th" and line_text and not THAI.search(line_text):
            errors.append(issue("DIALOGUE_LANGUAGE_MISMATCH", f"dialogue[{index}].text", "Thai lock requires Thai dialogue"))
        if target_spoken_language == "zh-CN" and line_text and not HAN.search(line_text):
            errors.append(issue("DIALOGUE_LANGUAGE_MISMATCH", f"dialogue[{index}].text", "Chinese lock requires Chinese dialogue"))
        caption = line.get("caption") or {}
        spans = caption.get("emphasis_spans") or []
        if spans and subtitle_mode != "emphasis_from_final_audio":
            errors.append(issue("EMPHASIS_MODE_MISMATCH", f"dialogue[{index}].caption", "emphasis spans require emphasis_from_final_audio"))
        cursor = 0
        for span_index, span in enumerate(spans):
            span_text = str(span.get("text", "")).strip()
            style = str(span.get("style", "")).strip()
            if not span_text:
                errors.append(issue("EMPTY_EMPHASIS_SPAN", f"dialogue[{index}].caption.emphasis_spans[{span_index}]", "span text is required"))
                continue
            position = line_text.find(span_text, cursor)
            if position < 0:
                errors.append(issue("EMPHASIS_TEXT_NOT_IN_LINE", f"dialogue[{index}].caption.emphasis_spans[{span_index}]", span_text))
            else:
                cursor = position + len(span_text)
            if style not in EMPHASIS_STYLES:
                errors.append(issue("INVALID_EMPHASIS_STYLE", f"dialogue[{index}].caption.emphasis_spans[{span_index}]", style))
            emphasis_span_count += 1
    for index, text in enumerate(texts):
        if str(text.get("beat_id", "")) not in beat_ids:
            errors.append(issue("UNKNOWN_BEAT_REFERENCE", f"screen_texts[{index}]", str(text.get("beat_id"))))
        if text.get("is_subtitle") is not False:
            errors.append(issue("SCREEN_TEXT_IS_SUBTITLE", f"screen_texts[{index}]", "creative screen text must not be a subtitle"))

    if runtime.get("audio_mode") == "natural_sound_only" and dialogue:
        errors.append(issue("NATURAL_SOUND_HAS_DIALOGUE", "dialogue", "natural_sound_only requires no dialogue"))
    if subtitle_mode == "emphasis_from_final_audio" and emphasis_span_count == 0:
        errors.append(issue("EMPHASIS_SUBTITLES_HAVE_NO_SPANS", "dialogue", "at least one dialogue line must mark an emphasis span"))
    hook = script.get("hook") or {}
    if str(hook.get("payoff_beat_id", "")) not in beat_ids:
        errors.append(issue("HOOK_NOT_CLOSED", "hook.payoff_beat_id", "payoff Beat does not exist"))
    for index, loop in enumerate(loops):
        if loop.get("status") != "closed":
            errors.append(issue("OPEN_LOOP", f"loops[{index}]", str(loop.get("loop_id"))))
        if str(loop.get("open_beat_id", "")) not in beat_ids or str(loop.get("close_beat_id", "")) not in beat_ids:
            errors.append(issue("INVALID_LOOP_REFERENCE", f"loops[{index}]", str(loop.get("loop_id"))))
    ending = script.get("ending") or {}
    if ending.get("primary_cta") != strategy.get("primary_cta"):
        errors.append(issue("CTA_MISMATCH", "ending.primary_cta", "ending CTA must equal strategy CTA"))
    cta_text = str(ending.get("cta_screen_text_id", ""))
    if cta_text not in text_ids:
        errors.append(issue("CTA_TEXT_MISSING", "ending.cta_screen_text_id", cta_text))
    if runtime.get("audio_mode") != "natural_sound_only" and ending.get("cta_line_id") and str(ending["cta_line_id"]) not in line_ids:
        errors.append(issue("CTA_LINE_MISSING", "ending.cta_line_id", str(ending["cta_line_id"])))

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "metrics": {
            "duration_seconds": duration,
            "beat_count": len(beats),
            "line_count": len(dialogue),
            "screen_text_count": len(texts),
            "emphasis_span_count": emphasis_span_count,
            "closed_loop_count": len(loops),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        script = json.loads(args.script.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = {"ok": False, "errors": [issue("INVALID_JSON", "script", str(exc))], "warnings": [], "metrics": {}}
    else:
        report = validate(script)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
