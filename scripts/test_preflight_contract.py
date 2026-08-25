#!/usr/bin/env python3
"""Contract tests for workflow-scoped preflight requirements."""

from __future__ import annotations

import unittest

from preflight import load_policy, resolve_requirements


class PreflightContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = load_policy()

    def test_feishu_only_workflows_never_require_generation_or_local_media(self) -> None:
        for workflow in ("creative_direction", "sentence_pattern_learning", "script_production", "lifecycle"):
            with self.subTest(workflow=workflow):
                requirements = resolve_requirements(self.policy, workflow)
                self.assertEqual(requirements["feishu"], "required")
                self.assertEqual(requirements["gpt_image"], "not_required")
                self.assertEqual(requirements["flow2api"], "not_required")
                self.assertEqual(requirements["ffmpeg"], "not_required")
                self.assertEqual(requirements["asr"], "not_required")

    def test_short_video_breakdown_requires_media_tools_and_audio_scoped_asr(self) -> None:
        silent = resolve_requirements(self.policy, "short_video_breakdown")
        with_audio = resolve_requirements(self.policy, "short_video_breakdown", source_has_audio=True)
        self.assertEqual(silent["feishu"], "required")
        self.assertEqual(silent["gpt_image"], "not_required")
        self.assertEqual(silent["flow2api"], "not_required")
        self.assertEqual(silent["ffmpeg"], "required")
        self.assertEqual(silent["image_tools"], "required")
        self.assertEqual(silent["asr"], "not_required")
        self.assertEqual(with_audio["asr"], "required")

    def test_standard_storyboard_requires_gpt_image_but_not_flow_or_media_runtime(self) -> None:
        requirements = resolve_requirements(self.policy, "storyboard_generation", mode="original")
        self.assertEqual(requirements["feishu"], "required")
        self.assertEqual(requirements["gpt_image"], "required")
        self.assertEqual(requirements["flow2api"], "not_required")
        self.assertEqual(requirements["ffmpeg"], "not_required")
        self.assertEqual(requirements["asr"], "not_required")

    def test_full_replication_uses_reviewed_segment_frames_without_media_runtime(self) -> None:
        requirements = resolve_requirements(self.policy, "storyboard_generation", mode="full_replication")
        self.assertEqual(requirements["ffmpeg"], "not_required")
        self.assertEqual(requirements["asr"], "not_required")

    def test_final_video_requires_asr_only_for_spoken_audio_modes(self) -> None:
        silent = resolve_requirements(self.policy, "final_video", audio_mode="natural_sound_only", target_spoken_language="zh-CN")
        spoken = resolve_requirements(self.policy, "final_video", audio_mode="spoken", target_spoken_language="zh-CN")
        thai_spoken = resolve_requirements(self.policy, "final_video", audio_mode="spoken", target_spoken_language="th")
        self.assertEqual(silent["ffmpeg"], "required")
        self.assertEqual(silent["gpt_image"], "not_required")
        self.assertEqual(silent["flow2api"], "required")
        self.assertEqual(silent["asr"], "not_required")
        self.assertEqual(silent["audio_separator"], "not_required")
        self.assertEqual(spoken["asr"], "required")
        self.assertEqual(spoken["audio_separator"], "required")
        self.assertEqual(thai_spoken["audio_separator"], "not_required")

    def test_final_video_requires_audio_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "--audio-mode"):
            resolve_requirements(self.policy, "final_video", target_spoken_language="zh-CN")


if __name__ == "__main__":
    unittest.main()
