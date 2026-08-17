#!/usr/bin/env python3
"""Check local dependencies required before the automated storyboard workflow."""

from __future__ import annotations

import argparse
import importlib.util

from runtime import find_binary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-asr", action="store_true", help="Fail when no supported local Whisper backend is available")
    args = parser.parse_args()
    checks = {
        "ffmpeg": find_binary("ffmpeg"),
        "ffprobe": find_binary("ffprobe"),
        "Pillow": importlib.util.find_spec("PIL") is not None,
        "faster-whisper": importlib.util.find_spec("faster_whisper") is not None,
        "openai-whisper": importlib.util.find_spec("whisper") is not None,
        "mlx-whisper": importlib.util.find_spec("mlx_whisper") is not None,
    }
    for name, value in checks.items():
        print(f"{name}: {value or 'not found'}")
    missing = []
    if not checks["ffmpeg"]:
        missing.append("ffmpeg")
    if not checks["ffprobe"]:
        missing.append("ffprobe")
    if checks["Pillow"] is not True:
        missing.append("Pillow")
    asr_available = any(checks[name] is True for name in ("faster-whisper", "openai-whisper", "mlx-whisper"))
    if args.require_asr and not asr_available:
        missing.append("a supported Whisper backend")
    if missing:
        raise SystemExit("PREFLIGHT BLOCKED: " + ", ".join(missing))
    print("PREFLIGHT OK")


if __name__ == "__main__":
    main()
