import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "review_dialogue_copy.py"


def load_reviewer():
    spec = importlib.util.spec_from_file_location("review_dialogue_copy", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class DialogueCopyReviewTest(unittest.TestCase):
    def setUp(self):
        self.reviewer = load_reviewer()
        self.script = {
            "script_id": "DIALOGUE-TEST-001",
            "runtime": {"audio_mode": "spoken", "target_spoken_language": "zh-CN"},
            "beats": [
                {"beat_id": "B1", "visual_action": "狗狗盯着家具，主人拿出玩具"},
                {"beat_id": "B2", "visual_action": "狗狗主动扒拉玩具"},
            ],
            "dialogue": [
                {"line_id": "L1", "text": "它又开始无聊了", "beat_id": "B1", "segment_id": "S1", "start": 0, "end": 2},
                {"line_id": "L2", "text": "你看，它自己就玩起来了", "beat_id": "B2", "segment_id": "S1", "start": 2, "end": 5},
                {"line_id": "L3", "text": "喜欢的话，带回去试试", "beat_id": "B2", "segment_id": "S1", "start": 5, "end": 7},
            ],
            "dialogue_quality_gate": {
                "instruction_manual_restatement_only": False,
                "pain_line_ids": ["L1"],
                "benefit_line_ids": ["L2"],
                "proof_line_ids": ["L2"],
                "natural_cta_line_ids": ["L3"],
            },
            "ending": {"cta_line_id": "L3"},
        }

    def test_good_copy_passes(self):
        report = self.reviewer.review(self.script)
        self.assertEqual(report["status"], "reviewed")
        self.assertFalse(report["blocking"])
        self.assertEqual(report["lines"][1]["roles"], ["benefit", "proof"])

    def test_quality_suggestions_do_not_block_production(self):
        self.script["dialogue_quality_gate"]["instruction_manual_restatement_only"] = True
        self.script["dialogue_quality_gate"]["benefit_line_ids"] = []
        report = self.reviewer.review(self.script)
        self.assertEqual(report["status"], "advisory")
        self.assertFalse(report["blocking"])
        codes = {item["code"] for item in report["checks"]}
        self.assertIn("INSTRUCTION_MANUAL_DIALOGUE", codes)
        self.assertIn("MISSING_DIALOGUE_QUALITY_ROLE", codes)

    def test_soft_warning_does_not_block_confirmation(self):
        self.script["dialogue"][0]["text"] = "直到这个特别特别好用的玩具终于出现了"
        report = self.reviewer.review(self.script)
        self.assertEqual(report["status"], "advisory")
        self.assertFalse(report["blocking"])
        self.assertIn("WRITTEN_CONNECTOR", {item["code"] for item in report["checks"]})

    def test_natural_sound_is_not_applicable(self):
        self.script["runtime"]["audio_mode"] = "natural_sound_only"
        report = self.reviewer.review(self.script)
        self.assertEqual(report["status"], "not_applicable")
        self.assertFalse(report["blocking"])


if __name__ == "__main__":
    unittest.main()
