"""Create and guard the Skill-local directory for one production run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import shutil
from typing import Any

from runtime import SKILL_DIR


RUNS_DIR = SKILL_DIR / "runs"
RUN_SUBDIRECTORIES = (
    "inputs",
    "audio",
    "planning",
    "prompts",
    "assets",
    "generation",
    "subtitles",
    "qa",
    "delivery",
    "tmp",
)


def _new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"RUN-{stamp}-{secrets.token_hex(3)}"


def _safe_run_root(run_id: str) -> Path:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ValueError("run_id must be a single directory name")
    root = (RUNS_DIR / run_id).resolve()
    if root.parent != RUNS_DIR.resolve():
        raise ValueError("run_id must resolve directly under the Skill runs directory")
    return root


@dataclass(frozen=True)
class RunContext:
    """The small interface shared by active scripts that write run artifacts."""

    root: Path
    run_id: str

    def path(self, *parts: str) -> Path:
        candidate = (self.root.joinpath(*parts)).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ValueError(f"artifact path escapes run directory: {parts}") from exc
        return candidate

    def write_json(self, relative: str, value: Any, *, artifact_type: str = "json") -> Path:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.register(target, artifact_type=artifact_type)
        return target

    def write_text(self, relative: str, value: str, *, artifact_type: str = "text") -> Path:
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")
        self.register(target, artifact_type=artifact_type)
        return target

    def snapshot(self, source: Path, relative: str, *, artifact_type: str = "input") -> Path:
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        target = self.path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise FileExistsError(f"run input already contains a different file: {target}")
        if not target.exists():
            shutil.copy2(source, target)
        self.register(target, artifact_type=artifact_type)
        return target

    def register(self, path: Path, *, artifact_type: str) -> None:
        path = path.resolve()
        try:
            relative = path.relative_to(self.root).as_posix()
        except ValueError as exc:
            raise ValueError(f"artifact is outside run directory: {path}") from exc
        if relative == "run-manifest.json":
            return
        manifest_path = self.root / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        artifacts = manifest.setdefault("artifacts", {})
        artifacts[relative] = {"type": artifact_type, "status": "present"}
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def update(self, **fields: Any) -> None:
        manifest_path = self.root / "run-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.update(fields)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_run(run_id: str | None = None, *, workflow: str = "commerce_content") -> RunContext:
    resolved_id = run_id or _new_run_id()
    root = _safe_run_root(resolved_id)
    if root.exists():
        raise FileExistsError(f"run already exists: {root}")
    root.mkdir(parents=True)
    for name in RUN_SUBDIRECTORIES:
        (root / name).mkdir()
    manifest = {
        "schema": "commerce-run-manifest-v1",
        "run_id": resolved_id,
        "workflow": workflow,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "artifacts": {},
    }
    (root / "run-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return RunContext(root=root, run_id=resolved_id)


def open_run(run_id: str) -> RunContext:
    root = _safe_run_root(run_id)
    manifest = root / "run-manifest.json"
    if not root.is_dir() or not manifest.is_file():
        raise FileNotFoundError(f"run does not exist or has no manifest: {root}")
    return RunContext(root=root, run_id=run_id)


def get_run(run_id: str | None, *, workflow: str = "commerce_content") -> RunContext:
    if run_id:
        root = _safe_run_root(run_id)
        return open_run(run_id) if root.exists() else create_run(run_id, workflow=workflow)
    return create_run(workflow=workflow)
