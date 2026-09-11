import importlib.util
import shutil
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load():
    path = ROOT / "scripts" / "run_context.py"
    spec = importlib.util.spec_from_file_location("run_context", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RunContextTest(unittest.TestCase):
    def test_run_is_created_under_skill_and_outputs_are_registered(self):
        run_context = load()
        run = run_context.create_run("RUN-test-context-001", workflow="test")
        try:
            self.assertEqual(run.root.parent, run_context.RUNS_DIR.resolve())
            output = run.write_json("planning/example.json", {"ok": True})
            self.assertTrue(output.is_file())
            manifest = (run.root / "run-manifest.json").read_text(encoding="utf-8")
            self.assertIn("planning/example.json", manifest)
        finally:
            shutil.rmtree(run.root)

    def test_path_escape_is_rejected(self):
        run_context = load()
        run = run_context.create_run("RUN-test-context-002", workflow="test")
        try:
            with self.assertRaises(ValueError):
                run.path("..", "outside.json")
        finally:
            shutil.rmtree(run.root)


if __name__ == "__main__":
    unittest.main()
