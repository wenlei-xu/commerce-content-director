#!/usr/bin/env python3
"""Parse and validate the Markdown creation workbook.

The workbook is intentionally small and human-readable. This module is the
single parser used by the execution adapter and copy reviewer; it does not
invent missing creative content.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from pathlib import Path
from typing import Any


SEGMENT_RE = re.compile(
    r"^##\s+(?P<segment_id>[^｜|]+?)\s*[｜|]\s*"
    r"(?P<start>\d+(?:\.\d+)?)\s*(?:秒|s)?\s*"
    r"[–—-]\s*(?P<end>\d+(?:\.\d+)?)\s*(?:秒|s)?\s*$",
    re.IGNORECASE,
)
LABEL_RE = re.compile(r"^\s*(?P<label>[^：:]+?)\s*[：:]\s*(?P<inline>.*)$")
FIELD_NAMES = {"对应口播", "口播", "画面", "衔接", "必须看清", "生成结果", "Beat"}


def _clean(value: str) -> str:
    return value.strip()


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metadata(lines: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LABEL_RE.match(line)
        if match and match.group("label").strip() not in FIELD_NAMES:
            result[_clean(match.group("label"))] = _clean(match.group("inline"))
    return result


def _section_value(lines: list[str], start: int, end: int) -> dict[str, str]:
    result: dict[str, list[str]] = {}
    current: str | None = None
    for raw in lines[start:end]:
        line = raw.rstrip()
        match = LABEL_RE.match(line)
        label = _clean(match.group("label")) if match else ""
        if match and label in FIELD_NAMES:
            current = label
            result.setdefault(current, [])
            inline = _clean(match.group("inline"))
            if inline:
                result[current].append(inline)
            continue
        if current is not None and line.strip():
            result[current].append(line.strip())
    return {key: "\n".join(value).strip() for key, value in result.items()}


def _float(value: str, field: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a number") from exc
    if number < 0:
        raise ValueError(f"{field} must be non-negative")
    return number


def parse(path: Path) -> dict[str, Any]:
    """Parse a Markdown workbook into an execution-neutral Python object."""

    source = path.read_text(encoding="utf-8")
    lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    headings = [index for index, line in enumerate(lines) if SEGMENT_RE.match(line.strip())]
    if not headings:
        raise ValueError("workbook must contain at least one segment heading such as '## S01｜0–6 秒'")

    segments: list[dict[str, Any]] = []
    for position, heading_index in enumerate(headings):
        match = SEGMENT_RE.match(lines[heading_index].strip())
        assert match is not None
        end_index = headings[position + 1] if position + 1 < len(headings) else len(lines)
        values = _section_value(lines, heading_index + 1, end_index)
        segment_id = _clean(match.group("segment_id"))
        start = _float(match.group("start"), f"{segment_id}.start")
        end = _float(match.group("end"), f"{segment_id}.end")
        segment: dict[str, Any] = {
            "segment_id": segment_id,
            "start": start,
            "end": end,
            "segment_seconds": end - start,
            "voiceover": values.get("对应口播") or values.get("口播", ""),
            "visual_event": values.get("画面", ""),
            "continuity": values.get("衔接", ""),
            "must_show": values.get("必须看清", ""),
            "results": values.get("生成结果", ""),
            "beat_id": values.get("Beat", ""),
        }
        segments.append(segment)

    metadata = _metadata(lines[: headings[0]])
    revision_value = metadata.get("修订号") or metadata.get("版本") or "1"
    try:
        revision = int(revision_value)
    except ValueError as exc:
        raise ValueError("修订号/版本 must be a positive integer") from exc
    if revision < 1:
        raise ValueError("修订号/版本 must be a positive integer")

    return {
        "schema": "commerce-creation-workbook-v1",
        "workbook_path": str(path.resolve()),
        "workbook_revision": revision,
        "workbook_digest": _digest(source),
        "metadata": metadata,
        "segments": segments,
    }


def validate(workbook: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    segments = workbook.get("segments")
    if not isinstance(segments, list) or not segments:
        return ["workbook.segments must contain at least one segment"]
    previous_end: float | None = None
    seen: set[str] = set()
    for index, segment in enumerate(segments, start=1):
        prefix = f"segments[{index}]"
        if not isinstance(segment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        segment_id = segment.get("segment_id")
        if not isinstance(segment_id, str) or not segment_id.strip():
            errors.append(f"{prefix}.segment_id is required")
        elif segment_id in seen:
            errors.append(f"{prefix}.segment_id is duplicated: {segment_id}")
        else:
            seen.add(segment_id)
        start, end = segment.get("start"), segment.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            errors.append(f"{prefix} must have numeric start and end")
            continue
        if end <= start:
            errors.append(f"{prefix}.end must be greater than start")
        if previous_end is not None and start < previous_end:
            errors.append(f"{prefix} overlaps the previous segment")
        previous_end = float(end)
        if not isinstance(segment.get("visual_event"), str) or not segment["visual_event"].strip():
            errors.append(f"{prefix}.画面 is required; the adapter will not invent an action")
    return errors


def load_and_validate(path: Path) -> dict[str, Any]:
    workbook = parse(path)
    errors = validate(workbook)
    if errors:
        raise ValueError("; ".join(errors))
    return workbook
