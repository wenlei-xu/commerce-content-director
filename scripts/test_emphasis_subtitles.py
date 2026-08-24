#!/usr/bin/env python3
"""Contract tests for emphasized subtitle validation and ASS rendering."""

from __future__ import annotations

import unittest
from pathlib import Path

from assemble_final_video import subtitle_filter
from build_emphasis_subtitles import build_ass
from validate_structured_script import validate


def valid_script() -> dict:
    return {
        "schema_version": "1.0",
        "script_id": "SCRIPT-ASS-001",
        "script_revision": 1,
        "direction_id": "DIRECTION-001",
        "runtime": {
            "target_duration_seconds": 3,
            "target_spoken_language": "th",
            "audio_mode": "spoken",
            "subtitle_mode": "emphasis_from_final_audio",
        },
        "strategy_snapshot": {
            "target_audience": "pet owners",
            "viewer_before_state": "curious",
            "viewer_after_state": "convinced",
            "content_format": "实测",
            "content_angle": "10-second test",
            "core_idea": "show the result",
            "primary_cta": "ดูรายละเอียด",
        },
        "hook": {
            "hook_id": "H01",
            "first_frame": "dog and toy",
            "viewer_question": "will it work",
            "promise": "visible result",
            "payoff_beat_id": "B01",
        },
        "beats": [{
            "beat_id": "B01", "start": 0, "end": 3, "function": "result",
            "visual_action": "dog gets a treat", "product_state": "dispensing", "audio_refs": ["L01"],
        }],
        "dialogue": [{
            "line_id": "L01", "beat_id": "B01", "segment_id": "SEG01", "start": 0, "end": 2.5,
            "speaker_id": "OWNER", "text": "ได้ขนมใน 10 วินาที", "function": "result", "delivery": "excited",
            "caption": {"emphasis_spans": [{"text": "10 วินาที", "style": "number_pop"}]},
        }],
        "screen_texts": [{
            "text_id": "T01", "beat_id": "B01", "start": 2.5, "end": 3,
            "text": "ดูรายละเอียด", "function": "CTA", "is_subtitle": False,
        }],
        "segments": [{
            "segment_id": "SEG01", "start": 0, "end": 3, "start_state": "dog watches",
            "end_state": "dog gets treat", "dialogue_ids": ["L01"], "product_final_state": "dispensed",
            "next_segment_inherits": [],
        }],
        "loops": [],
        "ending": {
            "primary_cta": "ดูรายละเอียด", "cta_screen_text_id": "T01", "cta_line_id": "L01",
            "ending_visual": "dog beside toy", "hook_closure": "treat appears",
        },
    }


class EmphasisSubtitleTests(unittest.TestCase):
    def test_valid_emphasis_script_and_ass_output(self) -> None:
        script = valid_script()
        report = validate(script)
        self.assertTrue(report["ok"], report)
        ass = build_ass(script, {"cues": [{"line_id": "L01", "start": 0, "end": 2.5, "text": "ได้ขนมใน 10 วินาที"}]})
        self.assertIn(r"{\c&H0000FFFF&\b1\fscx130\fscy130}10 วินาที{\rDefault}", ass)
        self.assertIn("Dialogue: 0,0:00:00.00,0:00:02.50", ass)

    def test_validator_rejects_keyword_not_in_dialogue(self) -> None:
        script = valid_script()
        script["dialogue"][0]["caption"]["emphasis_spans"][0]["text"] = "30 วินาที"
        report = validate(script)
        self.assertFalse(report["ok"])
        self.assertIn("EMPHASIS_TEXT_NOT_IN_LINE", {item["code"] for item in report["errors"]})

    def test_ass_rejects_timing_text_drift(self) -> None:
        with self.assertRaisesRegex(ValueError, "differs from approved dialogue"):
            build_ass(valid_script(), {"cues": [{"line_id": "L01", "start": 0, "end": 2, "text": "different"}]})

    def test_legacy_timing_lines_can_exact_match_unique_dialogue(self) -> None:
        ass = build_ass(valid_script(), {"lines": [{"start": 0, "end": 2.5, "text": "ได้ขนมใน 10 วินาที"}]})
        self.assertIn("10 วินาที", ass)

    def test_final_assembler_preserves_ass_embedded_styles(self) -> None:
        value = subtitle_filter(Path("captions.ass"), "unused", 95)
        self.assertNotIn("force_style", value)
        self.assertIn("captions.ass", value)


if __name__ == "__main__":
    unittest.main()
