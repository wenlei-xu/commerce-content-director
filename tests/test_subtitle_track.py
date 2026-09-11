import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "valid-workbook.md"


def load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SubtitleTrackTest(unittest.TestCase):
    def setUp(self):
        self.workbook = load("workbook").load_and_validate(FIXTURE)
        self.track = load("subtitle_track")

    def test_srt_uses_asr_time_and_approved_text(self):
        output = self.track.build_srt(self.workbook, {"cues": [
            {"start": 0.2, "end": 1.4, "text": "先别急着给它换新的"},
        ]})
        self.assertIn("00:00:00,200 --> 00:00:01,400", output)
        self.assertIn("先别急着给它换新的", output)

    def test_srt_rejects_text_not_in_workbook(self):
        with self.assertRaisesRegex(ValueError, "not present"):
            self.track.build_srt(self.workbook, {"cues": [
                {"start": 0, "end": 1, "text": "未经批准的台词"},
            ]})

    def test_layout_has_explicit_safe_area_and_two_line_limit(self):
        spec = self.track.subtitle_layout_spec()
        self.assertEqual(spec["canvas"], {"width": 720, "height": 1280})
        self.assertEqual(spec["anchor"], "bottom-center")
        self.assertEqual(spec["safe_area"], {
            "left": 28,
            "top": 820,
            "right": 692,
            "bottom": 940,
            "max_lines": 2,
            "line_height": 60,
        })
        self.track.validate_subtitle_layout(spec)

    def test_layout_rejects_position_drift(self):
        spec = self.track.subtitle_layout_spec()
        spec["margins"]["bottom"] = 80
        with self.assertRaisesRegex(ValueError, "canonical"):
            self.track.validate_subtitle_layout(spec)

    def test_ass_geometry_validator_accepts_canonical_style(self):
        ass = """[Script Info]
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,SimHei,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,1,0,2,28,28,340,1
"""
        self.track.validate_ass_text(ass)

    def test_ass_geometry_validator_rejects_margin_drift(self):
        ass = """[Script Info]
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,SimHei,50,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,1,0,2,28,28,80,1
"""
        with self.assertRaisesRegex(ValueError, "geometry/style drift"):
            self.track.validate_ass_text(ass)


if __name__ == "__main__":
    unittest.main()
