#!/usr/bin/env python3
"""Validate a director-storyboard package and its source-media isolation rules."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from PIL import Image


PANEL_FIELDS = {
    "id", "start", "end", "time", "shot_type", "camera", "action",
    "emotion", "dialogue", "video_control", "transition_to_next",
}
FORBIDDEN_SEGMENT_FIELDS = {
    "source_video", "source_videos", "source_frames", "reference_frames",
    "replacement_anchors", "control_storyboards", "grids", "keyframes",
}
PLACEHOLDERS = ("[Segment-ID]", "[segment-duration]", "[first-SB]", "[last-SB]", "[placeholder]")
REVIEW_HEADINGS = ("## 产品一致性", "## 主体与互动连续性", "## 参考表达一致性")
STYLE_PROFILE_FIELDS = {
    "capture_style", "sharpness", "motion_blur", "white_balance", "exposure",
    "contrast", "saturation", "lighting", "compression", "camera_stability",
    "depth_of_field", "overall_impression", "source_resolution", "source_aspect_ratio",
    "platform_aesthetic", "subject_camera_distance", "composition_discipline",
    "image_degradation", "style_fingerprint", "anti_style_constraints",
}
STORYBOARD_STYLE_BOUNDARY_MARKERS = ("故事板外框", "彩色关键帧")
NARRATION_CUE_FIELDS = {"id", "start", "end", "text", "type", "covered_sb_ids", "anchor", "reserved_reason"}
NARRATION_TYPES = {"anchor-hook", "anchor-proof", "continuous", "anchor-cta", "visual-closure"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes package directory: {value}") from exc
    return path


def require_file(root: Path, value: str, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Missing {label}")
    path = resolve_inside(root, value)
    if not path.is_file():
        raise ValueError(f"Missing {label}: {value}")
    return path


def require_image_size(path: Path, size: tuple[int, int], label: str) -> None:
    with Image.open(path) as image:
        if image.size != size:
            raise ValueError(f"{label} must be {size[0]}x{size[1]}, got {image.size[0]}x{image.size[1]}")


def manifest_paths(segment: dict) -> list[str]:
    values = segment.get("manifests")
    if values is None and segment.get("manifest"):
        values = [segment["manifest"]]
    if not isinstance(values, list) or not values:
        raise ValueError(f"{segment.get('id', '?')} has no storyboard manifests")
    return values


def storyboard_card_count(segment: dict) -> int:
    value = segment.get("storyboard_card_count")
    if value != 6:
        raise ValueError(f"{segment.get('id', '?')} storyboard_card_count must be 6 for the fixed 2x3 storyboard")
    return value


def validate_reference_style_profile(path: Path) -> dict:
    profile = load_json(path)
    if not isinstance(profile, dict):
        raise ValueError("reference style profile must be an object")
    missing = sorted(STYLE_PROFILE_FIELDS - set(profile))
    if missing:
        raise ValueError(f"reference style profile missing fields: {', '.join(missing)}")
    blank = sorted(field for field in STYLE_PROFILE_FIELDS if not isinstance(profile[field], str) or not profile[field].strip())
    if blank:
        raise ValueError(f"reference style profile has blank fields: {', '.join(blank)}")
    if not re.fullmatch(r"\d{2,5}[x×]\d{2,5}", profile["source_resolution"].strip()):
        raise ValueError("reference style profile source_resolution must look like 720x1280")
    if not re.fullmatch(r"\d+(?:\.\d+)?:\d+(?:\.\d+)?", profile["source_aspect_ratio"].strip()):
        raise ValueError("reference style profile source_aspect_ratio must look like 9:16")
    return profile


def validate_style_passthrough(path: Path, profile: dict, label: str, require_storyboard_boundary: bool = False) -> None:
    text = path.read_text(encoding="utf-8")
    for field in ("style_fingerprint", "anti_style_constraints"):
        value = profile[field].strip()
        if value not in text:
            raise ValueError(f"{label} must include reference style profile {field} verbatim")
    if require_storyboard_boundary:
        missing = [marker for marker in STORYBOARD_STYLE_BOUNDARY_MARKERS if marker not in text]
        if missing:
            raise ValueError(
                f"{label} must separate professional storyboard layout from keyframe capture style; "
                f"missing markers: {', '.join(missing)}"
            )


def validate_panel_descriptions(panel: dict) -> None:
    if not isinstance(panel["action"], str) or not panel["action"].strip():
        raise ValueError(f"{panel['id']} needs one complete action description")
    if not isinstance(panel["transition_to_next"], str) or not panel["transition_to_next"].strip():
        raise ValueError(f"{panel['id']} needs one transition_to_next description")


def validate_storyboard_review(path: Path, segment_id: str, panels: list[dict]) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [heading for heading in REVIEW_HEADINGS if heading not in text]
    if missing:
        raise ValueError(f"{segment_id} storyboard review missing sections: {', '.join(missing)}")
    if "总体结论：PASS" not in text or "总体结论：FAIL" in text:
        raise ValueError(f"{segment_id} storyboard review is not a passing gate")
    for panel in panels:
        if text.count(panel["id"]) < 3:
            raise ValueError(f"{segment_id} storyboard review must cover {panel['id']} in all three review sections")


def validate_narration_cues(manifest: dict, segment_id: str, start: float, end: float, panels: list[dict]) -> None:
    """Validate new dual-track narration metadata; omit it only for legacy packages."""
    cues = manifest.get("narration_cues")
    if cues is None:
        return
    if not isinstance(cues, list):
        raise ValueError(f"{segment_id} narration_cues must be a list")
    panel_ids = {str(panel.get("id")) for panel in panels}
    cue_ids: set[str] = set()
    cue_durations: dict[str, list[float]] = {}
    previous_end = start
    for cue in cues:
        if not isinstance(cue, dict):
            raise ValueError(f"{segment_id} narration cue must be an object")
        missing = sorted(NARRATION_CUE_FIELDS - set(cue))
        if missing:
            raise ValueError(f"{segment_id} narration cue missing fields: {', '.join(missing)}")
        cue_id = str(cue["id"])
        if not cue_id or cue_id in cue_ids:
            raise ValueError(f"{segment_id} has blank or duplicate narration cue ID: {cue_id!r}")
        cue_ids.add(cue_id)
        cue_start, cue_end = float(cue["start"]), float(cue["end"])
        if cue_end <= cue_start or cue_start < start - 0.001 or cue_end > end + 0.001:
            raise ValueError(f"{segment_id} narration cue {cue_id} has an invalid time window")
        if cue_start < previous_end - 0.001:
            raise ValueError(f"{segment_id} narration cue {cue_id} overlaps a previous cue")
        previous_end = cue_end
        cue_type = cue["type"]
        if cue_type not in NARRATION_TYPES:
            raise ValueError(f"{segment_id} narration cue {cue_id} has invalid type: {cue_type!r}")
        cue_durations.setdefault(cue_type, []).append(cue_end - cue_start)
        if not isinstance(cue["anchor"], bool):
            raise ValueError(f"{segment_id} narration cue {cue_id} anchor must be boolean")
        expected_anchor = cue_type.startswith("anchor-")
        if cue["anchor"] != expected_anchor:
            raise ValueError(f"{segment_id} narration cue {cue_id} anchor does not match type")
        if not isinstance(cue["reserved_reason"], str) or not cue["reserved_reason"].strip():
            raise ValueError(f"{segment_id} narration cue {cue_id} needs reserved_reason")
        if cue_type == "visual-closure":
            if str(cue["text"]).strip():
                raise ValueError(f"{segment_id} visual-closure cue {cue_id} must be silent")
        elif not isinstance(cue["text"], str) or not cue["text"].strip():
            raise ValueError(f"{segment_id} narration cue {cue_id} needs text")
        covered = cue["covered_sb_ids"]
        if not isinstance(covered, list) or not 1 <= len(covered) <= 3 or any(str(panel_id) not in panel_ids for panel_id in covered):
            raise ValueError(f"{segment_id} narration cue {cue_id} needs 1–3 valid covered_sb_ids")
    if math.isclose(end - start, 15.0, abs_tol=0.001):
        for cue_type, lower, upper in (("anchor-hook", 2.0, 3.0), ("anchor-proof", 1.5, 2.0), ("visual-closure", 1.5, 2.0)):
            durations = cue_durations.get(cue_type, [])
            if len(durations) != 1 or not lower <= durations[0] <= upper:
                raise ValueError(f"{segment_id} needs one {lower:g}–{upper:g}s {cue_type} cue")
    for panel in panels:
        if panel.get("audio_state") not in {"anchor", "continuous", "silent"}:
            raise ValueError(f"{panel.get('id', '?')} needs audio_state: anchor, continuous or silent")
        linked_cues = panel.get("narration_cue_ids")
        if not isinstance(linked_cues, list) or any(str(cue_id) not in cue_ids for cue_id in linked_cues):
            raise ValueError(f"{panel.get('id', '?')} has invalid narration_cue_ids")
        if panel["audio_state"] == "silent" and linked_cues:
            raise ValueError(f"{panel['id']} is silent but links narration cues")


def validate(root: Path) -> list[str]:
    package = load_json(require_file(root, "package.json", "package.json"))
    if package.get("generation_strategy") != "director-storyboard":
        raise ValueError("generation_strategy must be director-storyboard")
    content_origin = package.get("content_origin")
    if content_origin not in {"reference", "original"}:
        raise ValueError("content_origin must be reference or original")
    reference_duration = None
    reference_style = None
    if content_origin == "reference":
        reference_duration = float(package["reference_duration_seconds"])
        if reference_duration <= 0:
            raise ValueError("reference_duration_seconds must be positive")
        style_profile = require_file(root, package.get("reference_style_profile"), "reference style profile")
        try:
            style_profile.relative_to(root / "evidence")
        except ValueError as exc:
            raise ValueError("reference_style_profile must be inside evidence/") from exc
        reference_style = validate_reference_style_profile(style_profile)
    else:
        require_file(root, package.get("creative_brief"), "creative brief")
    total_duration = float(package["total_duration_seconds"])
    if total_duration <= 0:
        raise ValueError("total_duration_seconds must be positive")
    product_anchor = package.get("product_anchor")
    if product_anchor:
        require_file(root, product_anchor, "product anchor")

    subject_required = bool(package.get("subject_required"))
    subject_anchor = package.get("subject_anchor")
    if subject_required and not subject_anchor:
        raise ValueError("subject_required is true but subject_anchor is missing")
    if subject_anchor:
        require_file(root, subject_anchor, "subject anchor")

    segments = package.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("package.json must contain at least one segment")
    if content_origin == "reference" and reference_duration <= 17:
        if len(segments) != 1:
            raise ValueError("reference video at or below 17s must have exactly one storyboard segment")
        if not math.isclose(total_duration, 15.0, abs_tol=0.001):
            raise ValueError("reference video at or below 17s must generate one 15s video")
    elif content_origin == "reference" and reference_duration < 30:
        if len(segments) != 2:
            raise ValueError("reference video between 17s and 30s must have exactly two storyboard segments")
    elif content_origin == "original" and len(segments) != 1:
        raise ValueError("original content must have exactly one segment unless the contract is extended")

    segment_cursor = 0.0
    checked_panels = 0
    for segment in segments:
        segment_id = segment["id"]
        forbidden = sorted(FORBIDDEN_SEGMENT_FIELDS & set(segment))
        if forbidden:
            raise ValueError(f"{segment_id} contains forbidden source-media fields: {', '.join(forbidden)}")
        start, end = float(segment["start"]), float(segment["end"])
        if not math.isclose(start, segment_cursor, abs_tol=0.001):
            raise ValueError(f"{segment_id} starts at {start}, expected {segment_cursor}")
        if end <= start or not math.isclose(float(segment["duration_seconds"]), end - start, abs_tol=0.001):
            raise ValueError(f"{segment_id} has invalid duration")
        if content_origin == "reference" and reference_duration < 30 and float(segment["duration_seconds"]) > 15.001:
            raise ValueError(f"{segment_id} exceeds the 15s generation limit")

        card_count = storyboard_card_count(segment)
        proposal = require_file(root, segment["director_storyboard_proposal"], f"{segment_id} director storyboard")
        require_image_size(proposal, (3840, 2160), f"{segment_id} director storyboard")
        storyboard_prompt = require_file(root, segment["storyboard_image_prompt"], f"{segment_id} storyboard image prompt")
        video_prompt = require_file(root, segment["video_prompt"], f"{segment_id} video prompt")
        if content_origin == "reference":
            validate_style_passthrough(
                storyboard_prompt,
                reference_style,
                f"{segment_id} storyboard image prompt",
                require_storyboard_boundary=True,
            )
            validate_style_passthrough(video_prompt, reference_style, f"{segment_id} video prompt")
        prompt_text = video_prompt.read_text(encoding="utf-8")
        leftovers = [token for token in PLACEHOLDERS if token in prompt_text]
        if leftovers:
            raise ValueError(f"{segment_id} video prompt contains unresolved placeholders: {', '.join(leftovers)}")
        if "prompt续" in prompt_text or "逐 SB 备用" in prompt_text:
            raise ValueError(f"{segment_id} must contain one final video prompt, not prompt continuations")

        panels = []
        for value in manifest_paths(segment):
            manifest = load_json(require_file(root, value, f"{segment_id} manifest"))
            page_panels = manifest.get("panels") or []
            if len(page_panels) != card_count:
                raise ValueError(f"{Path(value).name} must contain exactly {card_count} panels")
            validate_narration_cues(manifest, segment_id, start, end, page_panels)
            panels.extend(page_panels)
        if len(panels) != card_count:
            raise ValueError(f"{segment_id} must contain exactly {card_count} panels in total")
        review = require_file(root, segment.get("storyboard_review"), f"{segment_id} storyboard review")
        validate_storyboard_review(review, segment_id, panels)

        panel_cursor = start
        for panel in panels:
            missing = sorted(PANEL_FIELDS - set(panel))
            if missing:
                raise ValueError(f"{panel.get('id', '?')} missing fields: {', '.join(missing)}")
            validate_panel_descriptions(panel)
            panel_start, panel_end = float(panel["start"]), float(panel["end"])
            if not math.isclose(panel_start, panel_cursor, abs_tol=0.001) or panel_end <= panel_start:
                raise ValueError(f"{panel['id']} has invalid timeline continuity")
            panel_cursor = panel_end
            if content_origin == "reference":
                source_path = require_file(root, panel.get("source_reference_frame"), f"{panel['id']} source reference frame")
                try:
                    source_path.relative_to(root / "evidence")
                except ValueError as exc:
                    raise ValueError(f"{panel['id']} source_reference_frame must be inside evidence/: {panel['source_reference_frame']}") from exc
                checked_panels += 1
            else:
                if panel.get("source_reference_frame"):
                    raise ValueError(f"{panel['id']} original content must not include source_reference_frame")
                if not isinstance(panel.get("creative_basis"), str) or not panel["creative_basis"].strip():
                    raise ValueError(f"{panel['id']} original content needs a non-empty creative_basis")
        if not math.isclose(panel_cursor, end, abs_tol=0.001):
            raise ValueError(f"{segment_id} panels end at {panel_cursor}, expected {end}")
        segment_cursor = end

    if not math.isclose(segment_cursor, total_duration, abs_tol=0.001):
        raise ValueError(f"Segments total {segment_cursor}, expected {total_duration}")
    require_file(root, package.get("quality_report", "quality-report.md"), "quality report")
    return [
        f"validated {len(segments)} director-storyboard segment(s)",
        f"validated {checked_panels} storyboard reference frame(s)" if content_origin == "reference" else "validated original creative bases",
        f"duration closes at {total_duration:g}s",
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    args = parser.parse_args()
    try:
        messages = validate(args.package_dir.resolve())
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"INVALID: {exc}") from exc
    print("VALID")
    for message in messages:
        print(f"- {message}")


if __name__ == "__main__":
    main()
