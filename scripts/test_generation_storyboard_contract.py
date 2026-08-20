#!/usr/bin/env python3
"""Regression checks for the Flow2API portrait-panel board validator."""

from __future__ import annotations

import tempfile
import json
from pathlib import Path

from PIL import Image

from validate_generation_storyboards import load_profile, validate_image


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
        profile.write_text(json.dumps({"storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"}}), encoding="utf-8")
        Image.new("RGB", (1080, 1920), "white").save(valid)
        Image.new("RGB", (1920, 1080), "white").save(landscape)

        columns, rows, ratio = load_profile(profile)
        assert (columns, rows) == (2, 2)
        assert validate_image(valid, columns, rows, ratio) == (1080, 1920, 540, 960)
        expect_failure(landscape, "panel ratio")

    print("generation storyboard contract tests passed")


if __name__ == "__main__":
    main()
