#!/usr/bin/env python3
"""Build a global SRT subtitle file from validated storyboard manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EMPTY_CAPTIONS = {"", "none", "null", "n/a", "无", "无字幕", "无口播", "无对白"}


def format_time(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, milliseconds = divmod(remainder, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def caption_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in EMPTY_CAPTIONS:
        return None
    return text


def resolve_inside(root: Path, value: str) -> Path:
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Manifest path escapes package directory: {value}") from exc
    return path


def manifest_paths(segment: dict) -> list[str]:
    values = segment.get("manifests")
    if values is None and segment.get("manifest"):
        values = [segment["manifest"]]
    if not isinstance(values, list) or not values:
        raise ValueError(f"{segment.get('id', '?')} has no manifests")
    return values


def build(package_dir: Path) -> list[tuple[float, float, str]]:
    package = json.loads((package_dir / "package.json").read_text(encoding="utf-8"))
    captions: list[tuple[float, float, str]] = []
    for segment in package["segments"]:
        for manifest_value in manifest_paths(segment):
            manifest = json.loads(
                resolve_inside(package_dir, manifest_value).read_text(encoding="utf-8")
            )
            narration_cues = manifest.get("narration_cues")
            if narration_cues is not None:
                for cue in narration_cues:
                    text = caption_text(cue.get("text"))
                    if text:
                        captions.append((float(cue["start"]), float(cue["end"]), text))
            else:
                # Legacy package fallback: narration used to live on every SB.
                for panel in manifest.get("panels", []):
                    text = caption_text(panel.get("dialogue")) or caption_text(panel.get("subtitle"))
                    if text:
                        captions.append((float(panel["start"]), float(panel["end"]), text))
    return sorted(captions, key=lambda item: (item[0], item[1]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    package_dir = args.package_dir.resolve()
    captions = build(package_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    blocks = [
        f"{index}\n{format_time(start)} --> {format_time(end)}\n{text}"
        for index, (start, end, text) in enumerate(captions, start=1)
    ]
    args.out.write_text("\n\n".join(blocks) + ("\n" if blocks else ""), encoding="utf-8")
    print(f"Wrote {len(captions)} subtitle cue(s): {args.out}")


if __name__ == "__main__":
    main()
