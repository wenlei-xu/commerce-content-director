#!/usr/bin/env python3
"""Resolve and check local dependencies for one director workflow.

Remote Feishu, GPT Image and Flow2API checks stay at their execution seams.
This script reports which checks the caller must make, and verifies only local
runtime requirements selected by config/workflow-capabilities.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any

from runtime import find_binary
from separate_reference_bgm import find_demucs_python


SKILL_DIR = Path(__file__).resolve().parent.parent
CAPABILITY_CONFIG = SKILL_DIR / "config" / "workflow-capabilities.json"
BASE_SCHEMA = SKILL_DIR / "config" / "base-schema.json"
ASR_BACKENDS = ("faster_whisper", "whisper", "mlx_whisper")
REMOTE_CAPABILITIES = {"feishu", "gpt_image", "flow2api"}
LANGUAGE_LOCK_WORKFLOWS = {"creative_direction", "script_production", "first_frame_generation", "final_video"}


def load_policy(path: Path = CAPABILITY_CONFIG) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_language_policy(path: Path = BASE_SCHEMA) -> dict[str, Any]:
    schema = json.loads(path.read_text(encoding="utf-8"))
    policy = schema.get("language_policy")
    if not isinstance(policy, dict):
        raise ValueError("base schema is missing language_policy")
    return policy


def resolve_target_spoken_language(
    language_policy: dict[str, Any],
    workflow: str,
    requested: str | None,
) -> tuple[str | None, str | None]:
    if workflow not in LANGUAGE_LOCK_WORKFLOWS:
        return requested, "user" if requested else None
    allowed = language_policy.get("allowed_spoken_languages")
    default = language_policy.get("default_target_spoken_language")
    if not isinstance(allowed, list) or not all(isinstance(value, str) for value in allowed):
        raise ValueError("allowed_spoken_languages must be a string list")
    resolved = requested or default
    if resolved not in allowed:
        raise ValueError(f"target_spoken_language must be one of {sorted(allowed)}")
    return resolved, "user" if requested else "schema_default"


def resolve_requirements(
    policy: dict[str, Any],
    workflow: str,
    *,
    mode: str | None = None,
    audio_mode: str | None = None,
    source_has_audio: bool = False,
    target_spoken_language: str | None = None,
    render_backend: str | None = None,
) -> dict[str, str]:
    """Resolve conditional capability states to required or not_required."""
    workflows = policy.get("workflows", {})
    if workflow not in workflows:
        raise ValueError(f"Unknown workflow: {workflow}")
    profile = workflows[workflow]
    requirements = dict(profile["capabilities"])
    conditions = dict(profile.get("conditions", {}))
    if mode and mode in profile.get("modes", {}):
        mode_profile = profile["modes"][mode]
        requirements.update(mode_profile.get("capabilities", {}))
        conditions.update(mode_profile.get("conditions", {}))

    for capability, state in list(requirements.items()):
        if state != "conditional":
            continue
        condition = conditions.get(capability)
        if condition == "source_has_audio=true":
            requirements[capability] = "required" if source_has_audio else "not_required"
        elif condition == "audio_mode=spoken|sparse_spoken":
            if audio_mode is None:
                raise ValueError(f"{workflow} requires --audio-mode to resolve {capability}")
            requirements[capability] = "required" if audio_mode in {"spoken", "sparse_spoken"} else "not_required"
        elif condition == "target_spoken_language=zh-CN&audio_mode=spoken|sparse_spoken":
            if audio_mode is None:
                raise ValueError(f"{workflow} requires --audio-mode to resolve {capability}")
            if target_spoken_language is None:
                raise ValueError(f"{workflow} requires target_spoken_language to resolve {capability}")
            requirements[capability] = (
                "required"
                if target_spoken_language == "zh-CN" and audio_mode in {"spoken", "sparse_spoken"}
                else "not_required"
            )
        elif condition == "render_backend=remotion|hybrid":
            requirements[capability] = "required" if render_backend in {"remotion", "hybrid"} else "not_required"
        else:
            raise ValueError(f"Unsupported condition for {capability}: {condition!r}")
    return requirements


def local_checks(requirements: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    checks: dict[str, Any] = {}
    missing: list[str] = []
    if requirements.get("ffmpeg") == "required":
        ffmpeg, ffprobe = find_binary("ffmpeg"), find_binary("ffprobe")
        checks["ffmpeg"] = ffmpeg or "not found"
        checks["ffprobe"] = ffprobe or "not found"
        if not ffmpeg:
            missing.append("ffmpeg")
        if not ffprobe:
            missing.append("ffprobe")
    if requirements.get("image_tools") == "required":
        available = importlib.util.find_spec("PIL") is not None
        checks["Pillow"] = available
        if not available:
            missing.append("Pillow")
    if requirements.get("asr") == "required":
        backends = {backend: importlib.util.find_spec(backend) is not None for backend in ASR_BACKENDS}
        checks["asr_backends"] = backends
        if not any(backends.values()):
            missing.append("a supported Whisper backend")
    if requirements.get("audio_separator") == "required":
        separator_python = find_demucs_python(None)
        checks["demucs_python"] = str(separator_python) if separator_python else "not found"
        if not separator_python:
            missing.append("a Python runtime with demucs and torch (set DEMUCS_PYTHON)")
    if requirements.get("remotion") == "required":
        node = shutil.which("node")
        npx = shutil.which("npx.cmd") or shutil.which("npx")
        checks["node"] = node or "not found"
        checks["npx"] = npx or "not found"
        if not node or not npx:
            missing.append("Node.js and npx for Remotion")
    return checks, missing


def report_for(
    policy: dict[str, Any],
    workflow: str,
    *,
    mode: str | None = None,
    audio_mode: str | None = None,
    source_has_audio: bool = False,
    require_asr: bool = False,
    target_spoken_language: str | None = None,
    render_backend: str | None = None,
    language_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_language, language_source = resolve_target_spoken_language(
        language_policy or load_language_policy(), workflow, target_spoken_language
    )
    requirements = resolve_requirements(
        policy,
        workflow,
        mode=mode,
        audio_mode=audio_mode,
        source_has_audio=source_has_audio,
        target_spoken_language=resolved_language,
        render_backend=render_backend,
    )
    if require_asr:
        requirements["asr"] = "required"
    checks, missing = local_checks(requirements)
    return {
        "workflow": workflow,
        "mode": mode,
        "audio_mode": audio_mode,
        "source_has_audio": source_has_audio,
        "target_spoken_language": resolved_language,
        "target_spoken_language_source": language_source,
        "render_backend": render_backend,
        "requirements": requirements,
        "remote_checks_required": sorted(
            capability for capability in REMOTE_CAPABILITIES if requirements.get(capability) == "required"
        ),
        "local_checks": checks,
        "missing_local_requirements": missing,
        "ok": not missing,
    }


def main() -> int:
    policy = load_policy()
    language_policy = load_language_policy()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow", required=True, choices=sorted(policy["workflows"]))
    parser.add_argument("--mode", help="Selected task mode, when the workflow is mode-dependent")
    parser.add_argument("--audio-mode", choices=("spoken", "sparse_spoken", "natural_sound_only"))
    parser.add_argument("--source-has-audio", action="store_true")
    parser.add_argument("--require-asr", action="store_true", help="Compatibility override: require a local ASR backend")
    parser.add_argument("--target-spoken-language", choices=sorted(language_policy["allowed_spoken_languages"]))
    parser.add_argument("--render-backend", choices=("ffmpeg", "remotion", "hybrid"), default="ffmpeg")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable report")
    args = parser.parse_args()
    try:
        report = report_for(
            policy,
            args.workflow,
            mode=args.mode,
            audio_mode=args.audio_mode,
            source_has_audio=args.source_has_audio,
            require_asr=args.require_asr,
            target_spoken_language=args.target_spoken_language,
            render_backend=args.render_backend,
            language_policy=language_policy,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(f"workflow: {report['workflow']}")
        if report["target_spoken_language"]:
            print(f"target spoken language: {report['target_spoken_language']} ({report['target_spoken_language_source']})")
        print("requirements: " + ", ".join(f"{key}={value}" for key, value in sorted(report["requirements"].items())))
        print("remote execution checks: " + (", ".join(report["remote_checks_required"]) or "none"))
        for name, value in report["local_checks"].items():
            print(f"{name}: {value}")
    if report["missing_local_requirements"]:
        if not args.json:
            print("PREFLIGHT BLOCKED: " + ", ".join(report["missing_local_requirements"]))
        return 2
    if not args.json:
        print("PREFLIGHT LOCAL CHECKS OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
