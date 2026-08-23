#!/usr/bin/env python3
"""Build one resumable local script package from a canonical structured script."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--output-root", type=Path, default=Path("runs"))
    args = parser.parse_args()
    script = json.loads(args.script.read_text(encoding="utf-8"))
    run_id = args.run_id or f"{script['script_id'].lower()}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    target = args.output_root / run_id
    target.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(args.script, target / "structured-script.json")
    validator = load_module("validate_structured_script", "validate_structured_script.py")
    report = validator.validate(script)
    (target / "validation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if not report["ok"]:
        print(json.dumps({"ok": False, "run_id": run_id, "package": str(target), "errors": report["errors"]}, ensure_ascii=False))
        return 2
    renderer = load_module("render_script_views", "render_script_views.py")
    views = renderer.render(script)
    render_dir = target / "render"
    render_dir.mkdir()
    for key, value in views.items():
        (render_dir / f"{key}.md").write_text(value, encoding="utf-8")
    manifest = {"run_id": run_id, "script_id": script["script_id"], "created_at": datetime.now(timezone.utc).isoformat(), "validation": "passed"}
    (target / "run-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "run_id": run_id, "package": str(target)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
