#!/usr/bin/env python3
"""Regression checks for the GPT Image 2.5 portrait first-frame validator."""

from __future__ import annotations

import tempfile
import json
from pathlib import Path

from PIL import Image

from validate_generation_first_frames import load_profile, validate_image


def expect_failure(path: Path, expected: str) -> None:
    try:
        validate_image(path)
    except ValueError as error:
        if expected not in str(error):
            raise AssertionError(f"expected {expected!r}, got {error!r}") from error
    else:
        raise AssertionError(f"expected validation failure containing {expected!r}")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        valid = root / "valid.png"
        landscape = root / "landscape.png"
        profile = root / "content-system-config-snapshot.json"
        profile.write_text(json.dumps({"first_frame_layout": {"aspect_ratio": "9:16"}}), encoding="utf-8")
        Image.new("RGB", (1080, 1920), "white").save(valid)
        Image.new("RGB", (1920, 1080), "white").save(landscape)

        ratio = load_profile(profile)
        assert ratio == 9 / 16
        assert validate_image(valid, ratio) == (1080, 1920)
        expect_failure(landscape, "image ratio")

        legacy_profile = root / "legacy-profile.json"
        legacy_profile.write_text(json.dumps({"first_frame_layout": {"aspect_ratio": "1:1"}}), encoding="utf-8")
        try:
            load_profile(legacy_profile)
        except ValueError as error:
            assert "9:16" in str(error)
        else:
            raise AssertionError("non-portrait first-frame geometry must be rejected")

    print("generation first-frame contract tests passed")


if __name__ == "__main__":
    main()
