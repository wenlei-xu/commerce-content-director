#!/usr/bin/env python3
"""Regression tests for the Director deep module seam."""

from __future__ import annotations

import copy
import unittest

from director import direct_segment


class DirectorTests(unittest.TestCase):
    def test_returns_explicit_first_frame_decision_without_mutating_input(self) -> None:
        segment = {
            "segment_id": "Segment-01",
            "visual_continuity": ["Same room and light."],
            "beats": [{"start": 0, "end": 10, "description": "Locked Beat timeline."}],
            "first_frame": {"camera": "Phone camera", "composition": "Centered subject.", "static_moment": "Entering state.", "performance": "No visible human performance.", "continuity": "Carry state.", "human_presence": "none"},
        }
        before = copy.deepcopy(segment)
        result = direct_segment(segment, variant="B", variant_delta="Wider reaction emphasis.")
        self.assertEqual(segment, before)
        self.assertEqual(result["module"], "Director")
        self.assertEqual(result["variant"], "B")
        self.assertEqual(result["variant_delta"], "Wider reaction emphasis.")
        self.assertEqual(result["first_frame"]["time"], 0)
        self.assertEqual(set(result["first_frame"]), {"time", "static_moment", "camera", "composition", "performance", "continuity", "human_presence"})
        self.assertEqual(result["script_mutation"], "forbidden")


if __name__ == "__main__":
    unittest.main()
