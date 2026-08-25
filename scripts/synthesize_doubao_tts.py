"""Synthesize Chinese or Thai voiceover with Doubao TTS 2.0."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import websockets

from doubao_tts_protocol import EventType, Message, MsgType, event_message


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = SKILL_DIR / "config" / "doubao-tts.json"
DEFAULT_ENV = SKILL_DIR / ".env"


def load_local_env(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text", help="Literal text to synthesize")
    source.add_argument("--text-file", type=Path, help="UTF-8 text file to synthesize")
    parser.add_argument("--output", type=Path, required=True, help="Output .mp3 path")
    parser.add_argument("--language", choices=("zh-CN", "th"), default="zh-CN")
    parser.add_argument("--speaker", help="Override the configured speaker ID")
    parser.add_argument("--context", action="append", default=[], help="Optional 2.0 voice instruction")
    parser.add_argument("--speech-rate", type=int, help="Speech rate from -50 to 100")
    parser.add_argument("--loudness-rate", type=int, help="Loudness from -50 to 100")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--env-file", type=Path, default=DEFAULT_ENV)
    parser.add_argument("--report", type=Path, help="Write a non-secret JSON execution report")
    parser.add_argument("--dry-run", action="store_true", help="Validate configuration without calling the API")
    return parser.parse_args()


def read_text(args: argparse.Namespace) -> str:
    text = args.text if args.text is not None else args.text_file.read_text(encoding="utf-8-sig")
    text = text.strip()
    if not text:
        raise SystemExit("TTS input text is empty")
    if args.language == "zh-CN" and not any("\u4e00" <= ch <= "\u9fff" for ch in text):
        raise SystemExit("zh-CN TTS input must contain Chinese Han characters")
    if args.language == "th" and not any("\u0e00" <= ch <= "\u0e7f" for ch in text):
        raise SystemExit("Thai TTS input must contain Thai script")
    return text


def resolve_settings(args: argparse.Namespace) -> tuple[dict[str, Any], str, str, dict[str, Any]]:
    config = json.loads(args.config.read_text(encoding="utf-8"))
    load_local_env(args.env_file)
    key_env = config["api_key_env"]
    api_key = os.environ.get(key_env, "").strip()
    if not api_key:
        raise SystemExit(f"Missing required environment variable: {key_env}")

    speaker_env = config["speaker_env"][args.language]
    speaker = args.speaker or os.environ.get(speaker_env) or config["default_speakers"][args.language]
    audio = dict(config["audio"])
    language_speech_rates = config.get("speech_rate_by_language") or {}
    if args.language in language_speech_rates:
        audio["speech_rate"] = language_speech_rates[args.language]
    if args.speech_rate is not None:
        audio["speech_rate"] = args.speech_rate
    if args.loudness_rate is not None:
        audio["loudness_rate"] = args.loudness_rate
    for field in ("speech_rate", "loudness_rate"):
        if not -50 <= int(audio[field]) <= 100:
            raise SystemExit(f"{field} must be between -50 and 100")
    return config, api_key, speaker, audio


async def receive(websocket: Any) -> Message:
    raw = await websocket.recv()
    if not isinstance(raw, bytes):
        raise RuntimeError("Doubao TTS returned an unexpected text frame")
    message = Message.from_bytes(raw)
    if message.msg_type == MsgType.ERROR:
        raise RuntimeError(f"Doubao TTS error {message.error_code}: {message.payload_text()}")
    if message.event in {EventType.CONNECTION_FAILED, EventType.SESSION_FAILED}:
        raise RuntimeError(f"Doubao TTS event {message.event}: {message.payload_text()}")
    return message


async def wait_for(websocket: Any, event: EventType) -> Message:
    message = await receive(websocket)
    if message.msg_type != MsgType.FULL_SERVER_RESPONSE or message.event != event:
        raise RuntimeError(f"Expected Doubao event {event}, received {message.event}: {message.payload_text()}")
    return message


async def synthesize(
    *, config: dict[str, Any], api_key: str, speaker: str, language: str,
    text: str, audio: dict[str, Any], contexts: list[str]
) -> tuple[bytes, dict[str, Any]]:
    headers = {
        "X-Api-Key": api_key,
        "X-Api-Resource-Id": config["resource_id"],
        "X-Api-Connect-Id": str(uuid.uuid4()),
        "X-Control-Require-Usage-Tokens-Return": "*",
    }
    session_id = str(uuid.uuid4())
    req_params: dict[str, Any] = {
        "speaker": speaker,
        "audio_params": audio,
        "additions": json.dumps(
            {"explicit_language": config["language_map"][language]},
            ensure_ascii=False,
        ),
    }
    if contexts:
        req_params["context_texts"] = contexts
    base_request = {"req_params": req_params}
    audio_data = bytearray()
    usage: dict[str, Any] = {}
    connection_started = False

    async with websockets.connect(
        config["endpoint"],
        additional_headers=headers,
        max_size=10 * 1024 * 1024,
        open_timeout=20,
        close_timeout=10,
    ) as websocket:
        try:
            await websocket.send(event_message(EventType.START_CONNECTION))
            await wait_for(websocket, EventType.CONNECTION_STARTED)
            connection_started = True

            start_payload = dict(base_request)
            start_payload["event"] = int(EventType.START_SESSION)
            await websocket.send(
                event_message(
                    EventType.START_SESSION,
                    session_id=session_id,
                    payload=json.dumps(start_payload, ensure_ascii=False).encode("utf-8"),
                )
            )
            await wait_for(websocket, EventType.SESSION_STARTED)

            request_payload = json.loads(json.dumps(base_request))
            request_payload["event"] = int(EventType.TASK_REQUEST)
            request_payload["req_params"]["text"] = text
            await websocket.send(
                event_message(
                    EventType.TASK_REQUEST,
                    session_id=session_id,
                    payload=json.dumps(request_payload, ensure_ascii=False).encode("utf-8"),
                )
            )
            await websocket.send(event_message(EventType.FINISH_SESSION, session_id=session_id))

            while True:
                message = await receive(websocket)
                if message.msg_type == MsgType.AUDIO_ONLY_SERVER:
                    audio_data.extend(message.payload)
                elif message.event in {EventType.USAGE_RESPONSE, EventType.SESSION_FINISHED}:
                    if message.payload:
                        try:
                            usage.update(json.loads(message.payload_text()))
                        except json.JSONDecodeError:
                            pass
                    if message.event == EventType.SESSION_FINISHED:
                        break

            if not audio_data:
                raise RuntimeError("Doubao TTS returned no audio data")
        finally:
            if connection_started:
                await websocket.send(event_message(EventType.FINISH_CONNECTION))
                await wait_for(websocket, EventType.CONNECTION_FINISHED)

    return bytes(audio_data), usage


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    text = read_text(args)
    config, api_key, speaker, audio = resolve_settings(args)
    report = {
        "schema": "commerce-doubao-tts-report-v1",
        "provider": config["provider"],
        "resource_id": config["resource_id"],
        "language": args.language,
        "speaker": speaker,
        "audio": audio,
        "text_chars": len(text),
        "status": "configuration_valid" if args.dry_run else "pending",
    }
    if args.dry_run:
        if args.report:
            write_json(args.report, report)
        print(json.dumps(report, ensure_ascii=False))
        return 0

    audio_bytes, usage = asyncio.run(
        synthesize(
            config=config,
            api_key=api_key,
            speaker=speaker,
            language=args.language,
            text=text,
            audio=audio,
            contexts=args.context,
        )
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".part")
    temporary.write_bytes(audio_bytes)
    temporary.replace(args.output)
    report.update({"status": "succeeded", "output": str(args.output.resolve()), "bytes": len(audio_bytes), "usage": usage})
    if args.report:
        write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Doubao TTS synthesis interrupted", file=sys.stderr)
        raise SystemExit(130)
