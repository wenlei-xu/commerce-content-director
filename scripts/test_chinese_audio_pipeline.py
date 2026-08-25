#!/usr/bin/env python3
"""Regression checks for the Chinese three-track post-production gate."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from assemble_final_video import chinese_audio_filter, validate_background_music_gate
from separate_reference_bgm import demucs_command


def main() -> None:
    command = demucs_command(Path("python"), Path("reference.wav"), Path("separated"), "htdemucs")
    assert command[1:4] == ["-m", "demucs.separate", "--two-stems"]
    assert "vocals" in command

    filter_graph = chinese_audio_filter(Path("final.srt"), "Microsoft YaHei", 95, "bold", 20, True)
    assert "[0:a]volume=0.45" in filter_graph
    assert "[2:a]volume=0.22" in filter_graph
    assert "sidechaincompress" in filter_graph
    assert "[environment][ducked_bgm][voice_mix]amix=inputs=3" in filter_graph

    silent_filter = chinese_audio_filter(Path("final.srt"), "Microsoft YaHei", 95, "bold", 20, False)
    assert "anullsrc" in silent_filter

    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        bgm = temp / "reference-bgm.wav"
        bgm.write_bytes(b"speech-free-bgm-test")
        digest = hashlib.sha256(bgm.read_bytes()).hexdigest()
        gate = temp / "gate.json"
        gate.write_text(json.dumps({
            "schema": "commerce-source-bgm-gate-v1",
            "status": "passed",
            "background_music_sha256": digest,
            "residual_speech_detected": False,
        }), encoding="utf-8")
        validate_background_music_gate(bgm, gate)

        failed = json.loads(gate.read_text(encoding="utf-8"))
        failed["residual_speech_detected"] = True
        gate.write_text(json.dumps(failed), encoding="utf-8")
        try:
            validate_background_music_gate(bgm, gate)
        except ValueError as error:
            assert "residual_speech_detected=false" in str(error)
        else:
            raise AssertionError("BGM with residual speech must block assembly")

    print("Chinese audio pipeline tests passed")


if __name__ == "__main__":
    main()
