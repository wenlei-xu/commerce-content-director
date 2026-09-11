#!/usr/bin/env python3
"""Build the ordinary SRT track for one Skill-local production run."""

from __future__ import annotations

import argparse
import json

from run_context import open_run
from subtitle_track import build_srt, subtitle_layout_spec
from workbook import load_and_validate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        run = open_run(args.run_id)
        workbook = load_and_validate(run.path("inputs/workbook.md"))
        timing_path = run.path("audio/timing-map.json")
        timing = json.loads(timing_path.read_text(encoding="utf-8"))
        output = run.write_text("subtitles/final.srt", build_srt(workbook, timing), artifact_type="subtitle_srt")
        run.write_json("subtitles/subtitle-layout.json", subtitle_layout_spec(), artifact_type="subtitle_layout")
        run.update(current_stage="subtitles")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Unable to build subtitles: {exc}") from exc
    print(f"Wrote subtitles: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
