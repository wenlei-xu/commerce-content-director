#!/usr/bin/env python3
"""Build an ASS subtitle track with script-approved keyword emphasis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

STYLE_TAGS = {
    # Keep the production subtitle palette intentionally restrained:
    # ordinary text is white and every approved emphasis span is yellow.
    "keyword_yellow": r"{\c&H0000FFFF&\b1}",
    "number_pop": r"{\c&H0000FFFF&\b1}",
    "result_pop": r"{\c&H0000FFFF&\b1}",
    "product_accent": r"{\c&H0000FFFF&\b1}",
    "pain_point_red": r"{\c&H0000FFFF&\b1}",
}
RESET = r"{\rDefault}"


def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(float(seconds) * 100))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{centiseconds:02}"


def escape_ass(text: str) -> str:
    return text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")


def render_caption(text: str, spans: list[dict[str, Any]]) -> str:
    cursor = 0
    parts: list[str] = []
    for span in spans:
        fragment = str(span["text"])
        position = text.find(fragment, cursor)
        if position < 0:
            raise ValueError(f"emphasis text is missing or out of order: {fragment}")
        style = str(span["style"])
        if style not in STYLE_TAGS:
            raise ValueError(f"unsupported emphasis style: {style}")
        parts.append(escape_ass(text[cursor:position]))
        parts.append(STYLE_TAGS[style] + escape_ass(fragment) + RESET)
        cursor = position + len(fragment)
    parts.append(escape_ass(text[cursor:]))
    return "".join(parts)


def wrap_rendered_caption(rendered: str, max_chars: int) -> str:
    """Insert explicit ASS line breaks without splitting inline style tags."""
    if max_chars <= 0:
        return rendered
    output: list[str] = []
    visible_chars = 0
    index = 0
    while index < len(rendered):
        if rendered[index] == "{":
            end = rendered.find("}", index + 1)
            if end < 0:
                raise ValueError("unterminated ASS style tag")
            output.append(rendered[index : end + 1])
            index = end + 1
            continue
        if rendered[index] == "\\" and rendered[index : index + 2] == r"\N":
            output.append(r"\N")
            visible_chars = 0
            index += 2
            continue
        punctuation = "，。！？；：、）》」』”’"
        if visible_chars >= max_chars and rendered[index] not in punctuation:
            output.append(r"\N")
            visible_chars = 0
        output.append(rendered[index])
        visible_chars += 1
        index += 1
    return "".join(output)


def timing_cues(value: Any) -> list[dict[str, Any]]:
    cues = (value.get("cues") or value.get("lines")) if isinstance(value, dict) else value
    if not isinstance(cues, list):
        raise ValueError("subtitle timing must be a list or an object with cues")
    return cues


def build_ass(
    script: dict[str, Any],
    timing: Any,
    *,
    font_name: str = "Leelawadee UI",
    font_size: int = 68,
    margin_v: int = 150,
    wrap_chars: int = 0,
) -> str:
    if (script.get("runtime") or {}).get("subtitle_mode") != "emphasis_from_final_audio":
        raise ValueError("structured script is not in emphasis_from_final_audio mode")
    lines = {str(line["line_id"]): line for line in script.get("dialogue", [])}
    events: list[str] = []
    for cue in timing_cues(timing):
        text = str(cue.get("text", "")).strip()
        line_id = str(cue.get("line_id", ""))
        if not line_id:
            matches = [candidate_id for candidate_id, candidate in lines.items() if str(candidate.get("text", "")).strip() == text]
            if len(matches) != 1:
                raise ValueError(f"subtitle timing without line_id must match exactly one approved line: {text}")
            line_id = matches[0]
        if line_id not in lines:
            raise ValueError(f"unknown line_id in subtitle timing: {line_id}")
        line = lines[line_id]
        if text != str(line.get("text", "")).strip():
            raise ValueError(f"subtitle text differs from approved dialogue: {line_id}")
        start, end = float(cue["start"]), float(cue["end"])
        if start < 0 or end <= start:
            raise ValueError(f"invalid subtitle timing: {line_id}")
        spans = (line.get("caption") or {}).get("emphasis_spans") or []
        rendered = wrap_rendered_caption(render_caption(text, spans), wrap_chars)
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Default,,0,0,0,,{rendered}")
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,70,70,{margin_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    return header + "\n".join(events) + ("\n" if events else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timing", type=Path, help="Final-audio subtitle timing JSON with line_id/start/end/text")
    parser.add_argument("--script", required=True, type=Path, help="Validated structured_script JSON")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--font-name", default="Leelawadee UI")
    parser.add_argument("--font-size", type=int, default=68)
    parser.add_argument("--margin-v", type=int, default=150)
    parser.add_argument("--wrap-chars", type=int, default=0, help="Maximum visible characters per subtitle line; 0 disables explicit wrapping")
    args = parser.parse_args()
    try:
        script = json.loads(args.script.read_text(encoding="utf-8"))
        timing = json.loads(args.timing.read_text(encoding="utf-8"))
        output = build_ass(
            script,
            timing,
            font_name=args.font_name,
            font_size=args.font_size,
            margin_v=args.margin_v,
            wrap_chars=args.wrap_chars,
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to build emphasis subtitles: {exc}") from exc
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(output, encoding="utf-8-sig")
    print(f"Wrote emphasized ASS subtitles: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
