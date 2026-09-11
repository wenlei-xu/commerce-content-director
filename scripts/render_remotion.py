#!/usr/bin/env python3
"""Render a local Remotion composition without controlling a desktop editor."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def find_command(name: str) -> str | None:
    candidates = [name]
    if name == "npx":
        candidates.insert(0, "npx.cmd")
    for candidate in candidates:
        found = shutil.which(candidate)
        if found:
            return found
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--composition-id", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--props", type=Path, help="JSON props file passed to Remotion")
    parser.add_argument("--codec", default="h264", choices=["h264", "h265", "vp8", "vp9", "prores"])
    parser.add_argument("--concurrency", type=int)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    project_dir = args.project_dir.resolve()
    output = args.out.resolve()
    package_json = project_dir / "package.json"
    if not project_dir.is_dir() or not package_json.is_file():
        raise SystemExit(f"Remotion project_dir must contain package.json: {project_dir}")
    try:
        package = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"Cannot read Remotion package.json: {error}") from error
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    if not any(name in dependencies for name in ("remotion", "@remotion/cli")):
        raise SystemExit("package.json does not declare remotion or @remotion/cli")

    npx = find_command("npx")
    if not npx or not find_command("node"):
        raise SystemExit("Node.js and npx are required for the Remotion backend")
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Output exists: {output}. Pass --overwrite to replace it.")
    output.parent.mkdir(parents=True, exist_ok=True)

    command = [npx, "--no-install", "remotion", "render", args.composition_id, str(output), f"--codec={args.codec}"]
    if args.props:
        props = args.props.resolve()
        if not props.is_file():
            raise SystemExit(f"Missing Remotion props file: {props}")
        command.append(f"--props={props}")
    if args.concurrency is not None:
        if args.concurrency < 1:
            raise SystemExit("--concurrency must be at least 1")
        command.append(f"--concurrency={args.concurrency}")
    if args.overwrite:
        command.append("--overwrite")

    completed = subprocess.run(command, cwd=project_dir, check=False)
    if completed.returncode != 0:
        return completed.returncode
    if not output.is_file() or output.stat().st_size == 0:
        raise SystemExit(f"Remotion completed without a non-empty output: {output}")
    print(f"Wrote Remotion video: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
