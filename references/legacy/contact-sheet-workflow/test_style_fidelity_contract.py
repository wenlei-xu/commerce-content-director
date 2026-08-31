#!/usr/bin/env python3
"""Regression checks for reference-style capture and verbatim prompt passthrough."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from validate_package import validate_reference_style_profile, validate_style_passthrough


BASE_PROFILE = {
    "capture_style": "竖屏手机低机位宠物 UGC",
    "sharpness": "轻微软锐",
    "motion_blur": "轻微运动模糊",
    "white_balance": "暖黄",
    "exposure": "室内自然曝光",
    "contrast": "中低对比",
    "saturation": "中等",
    "lighting": "室内自然光",
    "compression": "社媒轻压缩",
    "camera_stability": "轻手持",
    "depth_of_field": "手机自然景深",
    "overall_impression": "随动作略显随意",
    "source_resolution": "720x1280",
    "source_aspect_ratio": "9:16",
    "platform_aesthetic": "小红书宠物 UGC 原帧",
    "subject_camera_distance": "宠物和玩具贴近镜头",
    "composition_discipline": "构图随动作略显随意",
    "image_degradation": "轻压缩、轻糊、非商业锐度",
    "style_fingerprint": "模拟源片720×1280小红书宠物UGC原帧，保持9:16手机低机位取景。",
    "anti_style_constraints": "禁止商业棚拍、电影级景深、广告级锐度和过度规整构图。",
}


def expect_failure(fn, expected: str) -> None:
    try:
        fn()
    except ValueError as exc:
        if expected not in str(exc):
            raise AssertionError(f"expected {expected!r}, got {exc!r}") from exc
    else:
        raise AssertionError(f"expected ValueError containing {expected!r}")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        profile_path = root / "reference_style_profile.json"
        prompt_path = root / "storyboard-image-prompt.md"

        incomplete = dict(BASE_PROFILE)
        del incomplete["style_fingerprint"]
        profile_path.write_text(json.dumps(incomplete, ensure_ascii=False), encoding="utf-8")
        expect_failure(
            lambda: validate_reference_style_profile(profile_path),
            "missing fields: style_fingerprint",
        )

        profile_path.write_text(json.dumps(BASE_PROFILE, ensure_ascii=False), encoding="utf-8")
        profile = validate_reference_style_profile(profile_path)

        prompt_path.write_text("温暖居家 UGC，专业导演故事板。", encoding="utf-8")
        expect_failure(
            lambda: validate_style_passthrough(prompt_path, profile, "storyboard", True),
            "style_fingerprint verbatim",
        )

        prompt_path.write_text(
            "故事板外框使用专业清晰排版；六个彩色关键帧内部保持原片拍摄质感。\n"
            + profile["style_fingerprint"]
            + "\n"
            + profile["anti_style_constraints"],
            encoding="utf-8",
        )
        validate_style_passthrough(prompt_path, profile, "storyboard", True)

    print("style fidelity contract tests passed")


if __name__ == "__main__":
    main()
