import importlib.util
import json
import tempfile
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


class WorkbookExecutionTest(unittest.TestCase):
    def setUp(self):
        self.workbook = load("workbook")
        self.prepare = load("prepare_execution")
        self.compiler = load("compile_generation_prompts")
        self.validator = load("validate_prompt_bundle")

    def test_parse_keeps_one_authored_visual_event_per_segment(self):
        result = self.workbook.load_and_validate(FIXTURE)
        self.assertEqual(result["schema"], "commerce-creation-workbook-v1")
        self.assertEqual([item["segment_id"] for item in result["segments"]], ["S01", "S02"])
        self.assertIn("护在身下", result["segments"][0]["visual_event"])

    def test_adapter_requires_prompts_without_inventing_them(self):
        with self.assertRaisesRegex(ValueError, "missing Agent prompt"):
            self.prepare.build_plan(
                FIXTURE,
                stage="final_video",
                require_prompts=True,
            )

    def test_adapter_and_compiler_pass_through_agent_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_dir = Path(directory)
            (prompt_dir / "S01.final_video.prompt.md").write_text(
                "A dog takes the toy away from the person's hand and protects it under its chest.",
                encoding="utf-8",
            )
            (prompt_dir / "S02.final_video.prompt.md").write_text(
                "The dog carries the toy to the mat and shakes it independently.",
                encoding="utf-8",
            )
            plan = self.prepare.build_plan(
                FIXTURE,
                stage="final_video",
                prompt_dir=prompt_dir,
                require_prompts=True,
            )
            bundle = self.compiler.compile_plan(plan)
            self.assertEqual(bundle["schema"], "commerce-execution-bundle-v1")
            self.assertIn("takes the toy away", bundle["prompts"][0]["prompt"])
            self.assertTrue(self.validator.validate_bundle(bundle) == [])

    def test_compiler_rejects_missing_visual_event_and_chinese_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            prompt_dir = Path(directory)
            for segment_id in ("S01", "S02"):
                (prompt_dir / f"{segment_id}.final_video.prompt.md").write_text("狗狗玩玩具", encoding="utf-8")
            plan = self.prepare.build_plan(FIXTURE, stage="final_video", prompt_dir=prompt_dir, require_prompts=True)
            plan["segments"][0]["prompt"] = "狗狗玩玩具"
            with self.assertRaisesRegex(ValueError, "English control text"):
                self.compiler.compile_plan(plan)


if __name__ == "__main__":
    unittest.main()
