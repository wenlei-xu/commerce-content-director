import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(__file__).parent / "fixtures" / "valid-workbook.md"


def load():
    path = ROOT / "scripts" / "validate_batch_creativity.py"
    spec = importlib.util.spec_from_file_location("validate_batch_creativity", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class BatchCreativityTest(unittest.TestCase):
    def test_identical_workbooks_are_blocked(self):
        validator = load()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "one.md"
            second = Path(directory) / "two.md"
            content = FIXTURE.read_text(encoding="utf-8")
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")
            report = validator.validate([first, second])
            self.assertFalse(report["ok"])
            self.assertEqual(report["collision_count"], 1)

    def test_shared_structure_requires_reason(self):
        validator = load()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "one.md"
            second = Path(directory) / "two.md"
            content = FIXTURE.read_text(encoding="utf-8")
            first.write_text(content, encoding="utf-8")
            second.write_text(content, encoding="utf-8")
            report = validator.validate([first, second], allow_shared_structure=True)
            self.assertFalse(report["ok"])
            report = validator.validate(
                [first, second],
                allow_shared_structure=True,
                reason="同一广告系列统一创意方向",
            )
            self.assertTrue(report["ok"])


if __name__ == "__main__":
    unittest.main()
