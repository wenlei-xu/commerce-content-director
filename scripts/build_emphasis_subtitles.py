#!/usr/bin/env python3
"""Build an ASS subtitle track from a Markdown workbook and final ASR timing."""

from __future__ import annotations

import argparse
import json
from typing import Any

from run_context import open_run
from subtitle_track import (
    SUBTITLE_ALIGNMENT,
    SUBTITLE_CANVAS_HEIGHT,
    SUBTITLE_CANVAS_WIDTH,
    SUBTITLE_FONT_NAME,
    SUBTITLE_FONT_SIZE,
    SUBTITLE_MARGIN_BOTTOM,
    SUBTITLE_MARGIN_LEFT,
    SUBTITLE_MARGIN_RIGHT,
    SUBTITLE_OUTLINE_PX,
    SUBTITLE_SHADOW_PX,
    subtitle_layout_spec,
    validate_cues,
)
from workbook import load_and_validate


STYLE_TAG = r"{\c&H0000FFFF&\b1}"
RESET = r"{\rDefault}"


def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(float(seconds) * 100))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{centiseconds:02}"


def escape_ass(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def _render(text: str, spans: list[dict[str, Any]]) -> str:
    cursor = 0
    parts: list[str] = []
    for span in spans:
        fragment = str(span.get("text", ""))
        position = text.find(fragment, cursor)
        if not fragment or position < 0:
            raise ValueError(f"emphasis text is missing or out of order: {fragment}")
        parts.append(escape_ass(text[cursor:position]))
        parts.append(STYLE_TAG + escape_ass(fragment) + RESET)
        cursor = position + len(fragment)
    parts.append(escape_ass(text[cursor:]))
    return "".join(parts)


def build_ass(
    workbook: dict[str, Any],
    timing: Any,
    *,
    font_name: str = SUBTITLE_FONT_NAME,
    font_size: int = SUBTITLE_FONT_SIZE,
    margin_v: int = SUBTITLE_MARGIN_BOTTOM,
) -> str:
    if font_name != SUBTITLE_FONT_NAME or font_size != SUBTITLE_FONT_SIZE or margin_v != SUBTITLE_MARGIN_BOTTOM:
        raise ValueError(
            "ASS subtitle placement/style is fixed by subtitle_track.py: "
            f"font={SUBTITLE_FONT_NAME}, size={SUBTITLE_FONT_SIZE}, bottom_margin={SUBTITLE_MARGIN_BOTTOM}"
        )
    cues = validate_cues(workbook, timing)
    approved = "".join(str(segment.get("voiceover") or "").strip() for segment in workbook["segments"])
    cursor = 0
    events: list[str] = []
    for index, cue in enumerate(cues, start=1):
        text = cue["text"]
        position = approved.find(text, cursor)
        if position < 0:
            raise ValueError(f"cue {index} is not present in approved workbook voiceover")
        cursor = position + len(text)
        start, end = float(cue["start"]), float(cue["end"])
        if start < 0 or end <= start:
            raise ValueError(f"invalid cue timing: {index}")
        rendered = _render(text, cue.get("emphasis_spans") or [])
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{rendered}")
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {SUBTITLE_CANVAS_WIDTH}
PlayResY: {SUBTITLE_CANVAS_HEIGHT}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{SUBTITLE_OUTLINE_PX},{SUBTITLE_SHADOW_PX},{SUBTITLE_ALIGNMENT},{SUBTITLE_MARGIN_LEFT},{SUBTITLE_MARGIN_RIGHT},{margin_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    return header + "\n".join(events) + ("\n" if events else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        run = open_run(args.run_id)
        workbook = load_and_validate(run.path("inputs/workbook.md"))
        timing = json.loads(run.path("audio/timing-map.json").read_text(encoding="utf-8"))
        output = build_ass(workbook, timing)
        output_path = run.write_text("subtitles/final.ass", output, artifact_type="subtitle_ass")
        run.write_json("subtitles/subtitle-layout.json", subtitle_layout_spec(), artifact_type="subtitle_layout")
        run.update(current_stage="subtitles")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to build subtitles: {exc}") from exc
    print(f"Wrote subtitles: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
