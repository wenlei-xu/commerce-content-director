#!/usr/bin/env python3
"""Separate speech-free BGM from an approved reference video and enforce an ASR gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from runtime import find_binary


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def demucs_command(python: Path, audio: Path, output_dir: Path, model: str) -> list[str]:
    return [
        str(python), "-m", "demucs.separate", "--two-stems", "vocals",
        "--name", model, "--out", str(output_dir), str(audio),
    ]


def find_demucs_python(explicit: Path | None) -> Path | None:
    candidates = [explicit, Path(os.environ["DEMUCS_PYTHON"]) if os.environ.get("DEMUCS_PYTHON") else None, Path(sys.executable)]
    for candidate in candidates:
        if not candidate or not candidate.is_file():
            continue
        result = subprocess.run(
            [str(candidate), "-c", "import demucs, torch"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return candidate.resolve()
    return None


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_video", type=Path)
    parser.add_argument("--background-music", required=True, type=Path)
    parser.add_argument("--gate", required=True, type=Path)
    parser.add_argument("--asr-report", required=True, type=Path)
    parser.add_argument("--separator-python", type=Path, help="Python environment containing demucs and torch; or set DEMUCS_PYTHON")
    parser.add_argument("--model", default="htdemucs")
    parser.add_argument("--asr-backend", default="auto", choices=["auto", "mlx-whisper", "faster-whisper", "openai-whisper", "whisper-cli"])
    parser.add_argument("--asr-model")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = args.source_video.resolve()
    bgm = args.background_music.resolve()
    gate = args.gate.resolve()
    asr_report = args.asr_report.resolve()
    if not source.is_file():
        raise SystemExit(f"Reference video not found: {source}")
    existing = [path for path in (bgm, gate, asr_report) if path.exists()]
    if existing and not args.overwrite:
        raise SystemExit("Output exists; pass --overwrite: " + ", ".join(str(path) for path in existing))
    ffmpeg = find_binary("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg was not found; run scripts/preflight.py")
    separator_python = find_demucs_python(args.separator_python)
    if not separator_python:
        raise SystemExit("No Python runtime with demucs and torch was found; set DEMUCS_PYTHON")

    if args.dry_run:
        preview = demucs_command(separator_python, Path("reference-audio.wav"), Path("separated"), args.model)
        print(json.dumps({"separator_command": preview, "asr_gate_required": True}, ensure_ascii=False, indent=2))
        return 0

    bgm.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="source-bgm-", dir=bgm.parent) as temp_name:
        temp_dir = Path(temp_name)
        extracted = temp_dir / "reference-audio.wav"
        separated = temp_dir / "separated"
        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(source), "-vn", "-c:a", "pcm_s24le", str(extracted)],
            check=True,
        )
        subprocess.run(demucs_command(separator_python, extracted, separated, args.model), check=True)
        candidates = list(separated.rglob("no_vocals.wav"))
        if len(candidates) != 1:
            raise SystemExit(f"Expected one no_vocals.wav from Demucs, found {len(candidates)}")
        shutil.copy2(candidates[0], bgm)

    transcribe = Path(__file__).with_name("transcribe_audio.py")
    asr_command = [str(sys.executable), str(transcribe), str(bgm), "--out", str(asr_report), "--backend", args.asr_backend]
    if args.asr_model:
        asr_command.extend(["--model", args.asr_model])
    subprocess.run(asr_command, check=True)
    asr = json.loads(asr_report.read_text(encoding="utf-8"))
    residual_speech = asr.get("has_detected_speech") is not False
    payload = {
        "schema": "commerce-source-bgm-gate-v1",
        "status": "failed" if residual_speech else "passed",
        "source_video": str(source),
        "source_video_sha256": sha256_file(source),
        "background_music": str(bgm),
        "background_music_sha256": sha256_file(bgm),
        "separator": "demucs",
        "separator_model": args.model,
        "residual_asr_report": str(asr_report),
        "residual_speech_detected": residual_speech,
    }
    write_json(gate, payload)
    if residual_speech:
        raise SystemExit("Separated BGM still contains detected speech; re-separate or stop before assembly")
    print(f"Wrote speech-free background music and passed gate: {bgm}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
