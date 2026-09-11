#!/usr/bin/env python3
"""Build an ASS subtitle track from a Markdown workbook and final ASR timing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

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


def _cues(timing: Any) -> list[dict[str, Any]]:
    cues = timing.get("cues") if isinstance(timing, dict) else timing
    if not isinstance(cues, list):
        raise ValueError("timing must be a list or an object with cues")
    return cues


def _approved_text(workbook: dict[str, Any]) -> str:
    return "".join(str(segment.get("voiceover") or "").strip() for segment in workbook["segments"])

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
    font_name: str = "SimHei",
    font_size: int = 50,
    margin_v: int = 130,
) -> str:
    approved = _approved_text(workbook)
    cursor = 0
    events: list[str] = []
    for index, cue in enumerate(_cues(timing), start=1):
        text = str(cue.get("text", "")).strip()
        if not text or "\n" in text or "\r" in text:
            raise ValueError(f"cue {index} must contain one non-empty line")
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
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,1,0,2,28,28,{margin_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    return header + "\n".join(events) + ("\n" if events else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timing", type=Path, help="final-audio timing JSON with cues/start/end/text")
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        workbook = load_and_validate(args.workbook)
        timing = json.loads(args.timing.read_text(encoding="utf-8"))
        output = build_ass(workbook, timing)
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to build subtitles: {exc}") from exc
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8-sig")
    print(f"Wrote subtitles: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
