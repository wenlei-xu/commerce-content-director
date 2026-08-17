#!/usr/bin/env python3
"""Extract a video's audio and transcribe speech with timestamps using a local Whisper backend."""

import argparse
import importlib.util
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from runtime import find_binary, skill_asr_python


SKILL_DIR = Path(__file__).resolve().parent.parent


def available_backends():
    backends = []
    if importlib.util.find_spec("whisper"):
        backends.append("openai-whisper")
    if importlib.util.find_spec("faster_whisper"):
        backends.append("faster-whisper")
    if importlib.util.find_spec("mlx_whisper"):
        backends.append("mlx-whisper")
    if shutil.which("whisper"):
        backends.append("whisper-cli")
    return backends


def enter_skill_asr_environment():
    """Re-exec in the skill-local ASR venv when the caller uses system Python."""
    asr_python = skill_asr_python()
    in_skill_venv = asr_python is not None and Path(sys.executable).resolve() == asr_python.resolve()
    if asr_python is not None and not in_skill_venv and not available_backends():
        os.execv(str(asr_python), [str(asr_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def extract_audio(video, audio_out):
    ffmpeg = find_binary("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found; cannot extract audio")
    audio_out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio_out)],
        check=True,
    )


def expose_ffmpeg_on_path():
    """OpenAI Whisper invokes `ffmpeg` by name even for WAV input."""
    ffmpeg = find_binary("ffmpeg")
    if ffmpeg:
        os.environ["PATH"] = str(Path(ffmpeg).parent) + os.pathsep + os.environ.get("PATH", "")


def wav_duration(path):
    with wave.open(str(path), "rb") as wav:
        return wav.getnframes() / float(wav.getframerate())


def normalize_result(result, backend, model, source, audio_path):
    normalized = []
    for index, segment in enumerate(result.get("segments", [])):
        words = []
        for word in segment.get("words") or []:
            probability = word.get("probability")
            words.append(
                {
                    "start": round(float(word.get("start", segment.get("start", 0))), 3),
                    "end": round(float(word.get("end", segment.get("end", 0))), 3),
                    "text": str(word.get("word", word.get("text", ""))),
                    "confidence": round(float(probability), 4) if probability is not None else None,
                }
            )
        probabilities = [word["confidence"] for word in words if word["confidence"] is not None]
        confidence = sum(probabilities) / len(probabilities) if probabilities else None
        if confidence is None and segment.get("avg_logprob") is not None:
            confidence = max(0.0, min(1.0, math.exp(float(segment["avg_logprob"]))))
        normalized.append(
            {
                "id": index,
                "start": round(float(segment.get("start", 0)), 3),
                "end": round(float(segment.get("end", 0)), 3),
                "text": str(segment.get("text", "")).strip(),
                "confidence": round(confidence, 4) if confidence is not None else None,
                "no_speech_probability": round(float(segment["no_speech_prob"]), 4) if segment.get("no_speech_prob") is not None else None,
                "words": words,
            }
        )
    full_text = " ".join(segment["text"] for segment in normalized if segment["text"]).strip()
    language = result.get("language")
    language_probability = result.get("language_probability")
    return {
        "status": "complete",
        "source_video": str(source),
        "audio_path": str(audio_path),
        "backend": backend,
        "model": model,
        "language": language,
        "language_probability": round(float(language_probability), 4) if language_probability is not None else None,
        "duration_seconds": round(wav_duration(audio_path), 3),
        "has_detected_speech": bool(full_text),
        "full_text": full_text,
        "segments": normalized,
    }


def transcribe_mlx(audio, model, language):
    import mlx_whisper

    kwargs = {"path_or_hf_repo": model, "word_timestamps": True}
    if language:
        kwargs["language"] = language
    return mlx_whisper.transcribe(str(audio), **kwargs)


def transcribe_faster(audio, model, language):
    from faster_whisper import WhisperModel

    engine = WhisperModel(model, device="auto", compute_type="int8")
    segments, info = engine.transcribe(str(audio), language=language, word_timestamps=True, vad_filter=True)
    converted = []
    for segment in segments:
        converted.append(
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": [
                    {"start": word.start, "end": word.end, "word": word.word, "probability": word.probability}
                    for word in (segment.words or [])
                ],
            }
        )
    return {"language": info.language, "language_probability": info.language_probability, "segments": converted}


def transcribe_openai(audio, model, language):
    import whisper

    engine = whisper.load_model(model)
    return engine.transcribe(str(audio), language=language, word_timestamps=True, verbose=False)


def transcribe_cli(audio, model, language):
    command = shutil.which("whisper")
    if not command:
        raise RuntimeError("whisper CLI not found")
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = [command, str(audio), "--model", model, "--output_format", "json", "--output_dir", temp_dir, "--word_timestamps", "True", "--verbose", "False"]
        if language:
            cmd.extend(["--language", language])
        subprocess.run(cmd, check=True)
        return json.loads((Path(temp_dir) / f"{audio.stem}.json").read_text(encoding="utf-8"))


def main():
    enter_skill_asr_environment()
    expose_ffmpeg_on_path()
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", required=True, type=Path, help="Normalized timestamped transcript JSON")
    parser.add_argument("--audio-out", type=Path, help="Extracted mono 16 kHz WAV evidence")
    parser.add_argument("--backend", choices=["auto", "mlx-whisper", "faster-whisper", "openai-whisper", "whisper-cli"], default="auto")
    parser.add_argument("--model", help="Backend model; defaults to small or mlx-community/whisper-small-mlx")
    parser.add_argument("--language", help="Optional ISO language hint; omit for auto-detection")
    parser.add_argument("--extract-only", action="store_true", help="Diagnostic only; Stage 1 may not use this as a transcription substitute")
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Video not found: {args.video}")
    audio_out = args.audio_out or args.out.with_suffix(".wav")
    extract_audio(args.video, audio_out)
    if args.extract_only:
        write_json(args.out, {"status": "audio_extracted_only", "source_video": str(args.video), "audio_path": str(audio_out), "duration_seconds": round(wav_duration(audio_out), 3)})
        return

    installed = available_backends()
    backend = installed[0] if args.backend == "auto" and installed else args.backend
    if backend == "auto" or backend not in installed:
        write_json(
            args.out,
            {
                "status": "blocked",
                "reason": "no_asr_backend",
                "source_video": str(args.video),
                "audio_path": str(audio_out),
                "available_backends": installed,
                "required_action": "Install mlx-whisper, faster-whisper, or openai-whisper; or provide a timestamped transcript.",
            },
        )
        raise SystemExit("Audio extracted, but no supported ASR backend is installed; Stage 1 transcription is blocked.")

    model = args.model or ("mlx-community/whisper-small-mlx" if backend == "mlx-whisper" else "small")
    functions = {
        "mlx-whisper": transcribe_mlx,
        "faster-whisper": transcribe_faster,
        "openai-whisper": transcribe_openai,
        "whisper-cli": transcribe_cli,
    }
    result = functions[backend](audio_out, model, args.language)
    write_json(args.out, normalize_result(result, backend, model, args.video, audio_out))


if __name__ == "__main__":
    main()
