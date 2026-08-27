#!/usr/bin/env python3
"""Regression tests for the Director deep module seam."""

from __future__ import annotations

import copy
import unittest

from director import direct_segment


class DirectorTests(unittest.TestCase):
    def test_returns_explicit_panel_decisions_without_mutating_input(self) -> None:
        segment = {
            "segment_id": "Segment-01",
            "visual_continuity": ["Same room and light."],
            "beats": [
                {"panel": panel, "start": start, "end": end, "camera": "Phone camera", "description": f"Moment {index}", "continuity": "Carry state.", "human_presence": "none"}
                for index, (panel, start, end) in enumerate(zip(("top_left", "top_right", "bottom_left", "bottom_right"), (0, 1, 2, 3), (1, 2, 3, 4)), start=1)
            ],
        }
        before = copy.deepcopy(segment)
        result = direct_segment(segment, variant="B", variant_delta="Wider reaction emphasis.")
        self.assertEqual(segment, before)
        self.assertEqual(result["module"], "Director")
        self.assertEqual(result["variant"], "B")
        self.assertEqual(result["variant_delta"], "Wider reaction emphasis.")
        self.assertEqual(set(result["panels"][0]), {"panel", "start", "end", "static_moment", "camera", "composition", "performance", "continuity", "human_presence"})
        self.assertEqual(result["script_mutation"], "forbidden")


if __name__ == "__main__":
    unittest.main()
