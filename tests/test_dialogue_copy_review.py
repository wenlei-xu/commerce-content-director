import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "valid-workbook.md"


def load():
    path = ROOT / "scripts" / "review_dialogue_copy.py"
    spec = importlib.util.spec_from_file_location("review_dialogue_copy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class DialogueCopyReviewTest(unittest.TestCase):
    def test_workbook_copy_review_is_advisory(self):
        reviewer = load()
        workbook_module = importlib.util.spec_from_file_location("workbook", ROOT / "scripts" / "workbook.py")
        module = importlib.util.module_from_spec(workbook_module)
        assert workbook_module and workbook_module.loader
        workbook_module.loader.exec_module(module)
        report = reviewer.review(module.load_and_validate(FIXTURE))
        self.assertEqual(report["schema"], "commerce-dialogue-review-v2")
        self.assertFalse(report["blocking"])

    def test_missing_visual_event_blocks_only_invalid_workbook(self):
        reviewer = load()
        workbook_module = importlib.util.spec_from_file_location("workbook", ROOT / "scripts" / "workbook.py")
        module = importlib.util.module_from_spec(workbook_module)
        assert workbook_module and workbook_module.loader
        workbook_module.loader.exec_module(module)
        workbook = module.load_and_validate(FIXTURE)
        workbook["segments"][0]["voiceover"] = "打开以后就能马上用"
        workbook["segments"][0]["visual_event"] = ""
        report = reviewer.review(workbook)
        self.assertTrue(report["blocking"])
        self.assertIn("ACTION_WITHOUT_VISUAL", {item["code"] for item in report["checks"]})


if __name__ == "__main__":
    unittest.main()
