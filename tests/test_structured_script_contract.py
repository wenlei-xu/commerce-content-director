import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class StructuredScriptContractTest(unittest.TestCase):
    def setUp(self):
        self.script = json.loads((Path(__file__).parent / "fixtures" / "valid-structured-script.json").read_text(encoding="utf-8"))
        self.validator = load("validate_structured_script")
        self.renderer = load("render_script_views")

    def test_valid_script_passes(self):
        self.assertTrue(self.validator.validate(self.script)["ok"])

    def test_dialogue_cannot_cross_segment(self):
        self.script["dialogue"][1]["end"] = 11
        self.assertFalse(self.validator.validate(self.script)["ok"])

    def test_chinese_language_lock_passes_with_chinese_dialogue(self):
        self.script["runtime"]["target_spoken_language"] = "zh-CN"
        self.script["dialogue"][0]["text"] = "出门前，我先给它一个任务"
        self.script["dialogue"][1]["text"] = "点击看看这个菠萝玩具"
        self.assertTrue(self.validator.validate(self.script)["ok"])

    def test_language_mismatch_fails(self):
        self.script["runtime"]["target_spoken_language"] = "zh-CN"
        report = self.validator.validate(self.script)
        self.assertFalse(report["ok"])
        self.assertTrue(any(error["code"] == "DIALOGUE_LANGUAGE_MISMATCH" for error in report["errors"]))

    def test_unsupported_language_fails(self):
        self.script["runtime"]["target_spoken_language"] = "en"
        report = self.validator.validate(self.script)
        self.assertFalse(report["ok"])
        self.assertTrue(any(error["code"] == "INVALID_TARGET_SPOKEN_LANGUAGE" for error in report["errors"]))

    def test_spoken_script_requires_dialogue_quality_gate(self):
        self.script.pop("dialogue_quality_gate")
        report = self.validator.validate(self.script)
        self.assertFalse(report["ok"])
        self.assertIn("MISSING_DIALOGUE_QUALITY_GATE", {error["code"] for error in report["errors"]})

    def test_instruction_manual_only_dialogue_fails(self):
        self.script["dialogue_quality_gate"]["instruction_manual_restatement_only"] = True
        report = self.validator.validate(self.script)
        self.assertFalse(report["ok"])
        self.assertIn("INSTRUCTION_MANUAL_DIALOGUE", {error["code"] for error in report["errors"]})

    def test_every_dialogue_quality_role_is_required(self):
        self.script["dialogue_quality_gate"]["benefit_line_ids"] = []
        report = self.validator.validate(self.script)
        self.assertFalse(report["ok"])
        self.assertIn("MISSING_DIALOGUE_QUALITY_ROLE", {error["code"] for error in report["errors"]})

    def test_renderer_has_canonical_views(self):
        result = self.renderer.render(self.script)
        self.assertIn("BEAT-01", result["three_track_script"])
        self.assertIn("LINE-01", result["dialogue_manifest"])
        self.assertIn("台词质量门禁", result["script_body"])


if __name__ == "__main__":
    unittest.main()
