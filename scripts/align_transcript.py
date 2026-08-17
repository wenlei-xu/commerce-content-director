#!/usr/bin/env python3
"""Align a normalized ASR transcript to approved S-shot time ranges."""

import argparse
import json
from pathlib import Path


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def midpoint(start, end):
    return (float(start) + float(end)) / 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("shots", type=Path, help='JSON list or {"shots": [{"id":"S01","start":0,"end":3.5}]}')
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--uncertain-below", type=float, default=0.65)
    args = parser.parse_args()

    transcript = read_json(args.transcript)
    if transcript.get("status") != "complete":
        raise SystemExit(f"Transcript is not complete: {transcript.get('status')}")
    shots_data = read_json(args.shots)
    shots = shots_data.get("shots", shots_data) if isinstance(shots_data, dict) else shots_data
    aligned = []

    all_words = []
    for segment in transcript.get("segments", []):
        if segment.get("words"):
            for word in segment["words"]:
                all_words.append({**word, "segment_id": segment["id"]})
        else:
            all_words.append(
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                    "confidence": segment.get("confidence"),
                    "segment_id": segment["id"],
                }
            )

    for shot in shots:
        start, end = float(shot["start"]), float(shot["end"])
        items = [word for word in all_words if start <= midpoint(word["start"], word["end"]) < end or (float(word["end"]) == end and end == float(shots[-1]["end"]))]
        confidences = [float(item["confidence"]) for item in items if item.get("confidence") is not None]
        confidence = sum(confidences) / len(confidences) if confidences else None
        text = "".join(item["text"] for item in items).strip()
        aligned.append(
            {
                "shot_id": shot["id"],
                "start": start,
                "end": end,
                "speech_text": text,
                "confidence": round(confidence, 4) if confidence is not None else None,
                "needs_human_check": confidence is None or confidence < args.uncertain_below,
                "items": items,
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"language": transcript.get("language"), "shots": aligned}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
