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
        for workflow in ("creative_direction", "script_production", "lifecycle"):
            with self.subTest(workflow=workflow):
                requirements = resolve_requirements(self.policy, workflow)
                self.assertEqual(requirements["feishu"], "required")
                self.assertEqual(requirements["flow2api"], "not_required")
                self.assertEqual(requirements["ffmpeg"], "not_required")
                self.assertEqual(requirements["asr"], "not_required")

    def test_standard_storyboard_requires_flow_but_not_media_runtime(self) -> None:
        requirements = resolve_requirements(self.policy, "storyboard_generation", mode="original")
        self.assertEqual(requirements["feishu"], "required")
        self.assertEqual(requirements["flow2api"], "required")
        self.assertEqual(requirements["ffmpeg"], "not_required")
        self.assertEqual(requirements["asr"], "not_required")

    def test_full_replication_only_requires_asr_when_source_has_audio(self) -> None:
        silent = resolve_requirements(self.policy, "storyboard_generation", mode="full_replication")
        voiced = resolve_requirements(
            self.policy, "storyboard_generation", mode="full_replication", source_has_audio=True
        )
        self.assertEqual(silent["ffmpeg"], "required")
        self.assertEqual(silent["asr"], "not_required")
        self.assertEqual(voiced["asr"], "required")

    def test_final_video_requires_asr_only_for_spoken_audio_modes(self) -> None:
        silent = resolve_requirements(self.policy, "final_video", audio_mode="natural_sound_only")
        spoken = resolve_requirements(self.policy, "final_video", audio_mode="spoken")
        self.assertEqual(silent["ffmpeg"], "required")
        self.assertEqual(silent["asr"], "not_required")
        self.assertEqual(spoken["asr"], "required")

    def test_final_video_requires_audio_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "--audio-mode"):
            resolve_requirements(self.policy, "final_video")


if __name__ == "__main__":
    unittest.main()
