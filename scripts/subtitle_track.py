"""Shared subtitle source and timing rules for the active run workflow."""

from __future__ import annotations

import re
from typing import Any


EMPTY_CAPTIONS = {"", "none", "null", "n/a", "无", "无字幕", "无口播", "无对白"}
DISPLAY_PUNCTUATION = re.compile(r"[，。！？、,.!?；;：:（）()“”\"'‘’「」『』—…]+")

# One geometry contract is shared by SRT burn-in, ASS generation and final
# assembly.  Coordinates are expressed in the canonical 720x1280 portrait
# canvas; the subtitle renderer scales the same margins with the output.
SUBTITLE_CANVAS_WIDTH = 720
SUBTITLE_CANVAS_HEIGHT = 1280
SUBTITLE_FONT_NAME = "SimHei"
SUBTITLE_FONT_SIZE = 50
SUBTITLE_FONT_WEIGHT = "bold"
SUBTITLE_OUTLINE_PX = 1
SUBTITLE_SHADOW_PX = 0
SUBTITLE_ALIGNMENT = 2  # ASS/Libass: bottom-center
SUBTITLE_MARGIN_LEFT = 28
SUBTITLE_MARGIN_RIGHT = 28
# Keep the subtitle in the lower-third viewing area while staying above the
# caption/description/interaction overlay commonly present in vertical-feed
# apps such as Douyin/TikTok.
SUBTITLE_MARGIN_BOTTOM = 340
SUBTITLE_MAX_LINES = 2
SUBTITLE_LINE_HEIGHT = 60
SUBTITLE_SAFE_TOP = SUBTITLE_CANVAS_HEIGHT - SUBTITLE_MARGIN_BOTTOM - (SUBTITLE_LINE_HEIGHT * SUBTITLE_MAX_LINES)
SUBTITLE_SAFE_RIGHT = SUBTITLE_CANVAS_WIDTH - SUBTITLE_MARGIN_RIGHT


def subtitle_layout_spec() -> dict[str, Any]:
    """Return the auditable, canonical subtitle placement contract."""
    return {
        "schema": "commerce-subtitle-layout-v1",
        "canvas": {"width": SUBTITLE_CANVAS_WIDTH, "height": SUBTITLE_CANVAS_HEIGHT},
        "anchor": "bottom-center",
        "safe_area": {
            "left": SUBTITLE_MARGIN_LEFT,
            "top": SUBTITLE_SAFE_TOP,
            "right": SUBTITLE_SAFE_RIGHT,
            "bottom": SUBTITLE_CANVAS_HEIGHT - SUBTITLE_MARGIN_BOTTOM,
            "max_lines": SUBTITLE_MAX_LINES,
            "line_height": SUBTITLE_LINE_HEIGHT,
        },
        "margins": {
            "left": SUBTITLE_MARGIN_LEFT,
            "right": SUBTITLE_MARGIN_RIGHT,
            "bottom": SUBTITLE_MARGIN_BOTTOM,
        },
        "style": {
            "font_name": SUBTITLE_FONT_NAME,
            "font_size": SUBTITLE_FONT_SIZE,
            "font_weight": SUBTITLE_FONT_WEIGHT,
            "outline_px": SUBTITLE_OUTLINE_PX,
            "shadow_px": SUBTITLE_SHADOW_PX,
        },
        "visual_qa": {
            "required": True,
            "status": "pending",
            "checks": ["inside_safe_area", "no_third_line", "no_subject_or_product_obstruction"],
        },
    }


def validate_subtitle_layout(spec: dict[str, Any]) -> None:
    """Reject drift from the single production subtitle geometry."""
    if not isinstance(spec, dict):
        raise ValueError("subtitle layout must be an object")
    expected = subtitle_layout_spec()
    actual_core = {key: value for key, value in spec.items() if key != "visual_qa"}
    expected_core = {key: value for key, value in expected.items() if key != "visual_qa"}
    visual_qa = spec.get("visual_qa")
    if actual_core != expected_core or not isinstance(visual_qa, dict) or visual_qa.get("status") not in {"pending", "passed", "failed"}:
        raise ValueError("subtitle layout does not match the canonical 720x1280 safe-area contract")


def validate_ass_text(text: str) -> None:
    """Validate the geometry that an ASS renderer will actually use."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    required_info = {
        "PlayResX": str(SUBTITLE_CANVAS_WIDTH),
        "PlayResY": str(SUBTITLE_CANVAS_HEIGHT),
    }
    for key, expected_value in required_info.items():
        if f"{key}: {expected_value}" not in lines:
            raise ValueError(f"ASS subtitle must declare {key}: {expected_value}")
    format_line = next((line for line in lines if line.startswith("Format: Name,Fontname,")), None)
    style_line = next((line for line in lines if line.startswith("Style: Default,")), None)
    if not format_line or not style_line:
        raise ValueError("ASS subtitle is missing the Default style contract")
    fields = [field.strip().lower() for field in format_line.removeprefix("Format: ").split(",")]
    values = style_line.removeprefix("Style: ").split(",")
    if len(fields) != len(values):
        raise ValueError("ASS Default style does not match its format declaration")
    style = dict(zip(fields, (value.strip() for value in values)))
    expected = {
        "fontname": SUBTITLE_FONT_NAME,
        "fontsize": str(SUBTITLE_FONT_SIZE),
        "bold": "1",
        "outline": str(SUBTITLE_OUTLINE_PX),
        "shadow": str(SUBTITLE_SHADOW_PX),
        "alignment": str(SUBTITLE_ALIGNMENT),
        "marginl": str(SUBTITLE_MARGIN_LEFT),
        "marginr": str(SUBTITLE_MARGIN_RIGHT),
        "marginv": str(SUBTITLE_MARGIN_BOTTOM),
    }
    drift = [f"{key}={style.get(key)!r} (expected {value!r})" for key, value in expected.items() if style.get(key) != value]
    if drift:
        raise ValueError("ASS subtitle geometry/style drift: " + ", ".join(drift))


def cues_from_timing(timing: Any) -> list[dict[str, Any]]:
    if isinstance(timing, dict):
        cues = timing.get("cues") or timing.get("segments")
    else:
        cues = timing
    if not isinstance(cues, list):
        raise ValueError("timing must be a list or an object with cues")
    result: list[dict[str, Any]] = []
    for index, cue in enumerate(cues, start=1):
        if not isinstance(cue, dict):
            raise ValueError(f"cue {index} must be an object")
        text = str(cue.get("text", "")).strip()
        if not text or "\n" in text or "\r" in text:
            raise ValueError(f"cue {index} must contain one non-empty line")
        start, end = float(cue["start"]), float(cue["end"])
        if start < 0 or end <= start:
            raise ValueError(f"invalid cue timing: {index}")
        result.append({**cue, "text": text, "start": start, "end": end})
    return result


def approved_voiceover(workbook: dict[str, Any]) -> str:
    return "".join(str(segment.get("voiceover") or "").strip() for segment in workbook["segments"])


def validate_cues(workbook: dict[str, Any], timing: Any) -> list[dict[str, Any]]:
    approved = approved_voiceover(workbook)
    cursor = 0
    result = cues_from_timing(timing)
    for index, cue in enumerate(result, start=1):
        position = approved.find(cue["text"], cursor)
        if position < 0:
            raise ValueError(f"cue {index} is not present in approved workbook voiceover")
        cursor = position + len(cue["text"])
    return result


def display_text(text: str) -> str:
    return DISPLAY_PUNCTUATION.sub("", text).strip()


def srt_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def build_srt(workbook: dict[str, Any], timing: Any) -> str:
    cues = validate_cues(workbook, timing)
    blocks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        text = display_text(cue["text"])
        if not text:
            continue
        blocks.append(
            f"{index}\n{srt_time(cue['start'])} --> {srt_time(cue['end'])}\n{text}"
        )
    return "\n\n".join(blocks) + ("\n" if blocks else "")
