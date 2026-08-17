"""Cross-platform runtime discovery for the storyboard scripts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional


SKILL_DIR = Path(__file__).resolve().parent.parent


def find_binary(name: str) -> Optional[str]:
    """Find ffmpeg/ffprobe from explicit configuration, PATH, or local bundles."""
    executable = f"{name}.exe" if os.name == "nt" else name
    explicit = os.environ.get(f"AUTO_VIDEO_STORYBOARD_{name.upper()}")
    ffmpeg_home = os.environ.get("FFMPEG_HOME")
    candidates = [
        explicit,
        SKILL_DIR / "vendor" / "bin" / executable,
        Path(ffmpeg_home) / "bin" / executable if ffmpeg_home else None,
        shutil.which(name),
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "bin" / executable,
        Path("C:/ffmpeg/bin") / executable,
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


def skill_asr_python() -> Optional[Path]:
    candidates = [
        SKILL_DIR / ".venv-asr" / "Scripts" / "python.exe",
        SKILL_DIR / ".venv-asr" / "bin" / "python",
    ]
    return next((path for path in candidates if path.is_file()), None)
