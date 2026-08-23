#!/usr/bin/env python3
"""Render human-review fields from one canonical structured script."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def sec(value: float | int) -> str:
    return f"{value:g}秒"


def render(script: dict[str, Any]) -> dict[str, str]:
    strategy = script["strategy_snapshot"]
    beats = script["beats"]
    dialogue = {line["line_id"]: line for line in script["dialogue"]}
    texts = {item["text_id"]: item for item in script["screen_texts"]}
    hook = script["hook"]
    beat_rows = ["| 时间 | Beat | 叙事功能 | 画面与动作 | 口播 / 声音 | 屏幕文字 | 产品状态 | 下一步衔接 |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for beat in beats:
        sound = "；".join(
            dialogue[item]["text"] if item in dialogue else item for item in beat.get("audio_refs", [])
        )
        screen = "；".join(
            texts[item]["text"] if item in texts else item for item in beat.get("screen_text_refs", [])
        )
        beat_rows.append(
            f"| {sec(beat['start'])}—{sec(beat['end'])} | {beat['beat_id']} | {beat['function']} | "
            f"{beat['visual_action']} | {sound} | {screen} | {beat['product_state']} | {beat.get('transition', '')} |"
        )
    dialogue_rows = ["| Line | 时间 | 说话者 | 台词 | 功能 | 表现 |", "| --- | --- | --- | --- | --- | --- |"]
    for line in script["dialogue"]:
        dialogue_rows.append(f"| {line['line_id']} | {sec(line['start'])}—{sec(line['end'])} | {line['speaker_id']} | {line['text']} | {line['function']} | {line['delivery']} |")
    text_rows = ["| Text | 时间 | 屏幕文字 | 功能 |", "| --- | --- | --- | --- |"]
    for item in script["screen_texts"]:
        text_rows.append(f"| {item['text_id']} | {sec(item['start'])}—{sec(item['end'])} | {item['text']} | {item['function']} |")
    loops = "\n".join(
        f"- {item['loop_id']}：{item['viewer_question']} → {item['payoff']}（{item['open_beat_id']} → {item['close_beat_id']}）"
        for item in script["loops"]
    )
    return {
        "script_summary": f"{strategy['content_angle']}：{strategy['core_idea']}，最后引导“{strategy['primary_cta']}”。",
        "hook_package": "\n".join([
            f"机制：{hook.get('mechanism', '')}",
            f"第一帧：{hook['first_frame']}",
            f"观众问题：{hook['viewer_question']}",
            f"承诺：{hook['promise']}",
            f"回收 Beat：{hook['payoff_beat_id']}",
        ]),
        "retention_plan": "\n".join(f"- {beat['beat_id']}：{beat.get('next_pull', '')}" for beat in beats),
        "beat_timeline": "\n".join(beat_rows),
        "three_track_script": "\n".join(beat_rows),
        "dialogue_manifest": "\n".join(dialogue_rows),
        "screen_text_manifest": "\n".join(text_rows),
        "audio_performance_plan": json.dumps(script.get("audio_performance", {}), ensure_ascii=False, indent=2),
        "product_action_plan": json.dumps(script.get("product_actions", []), ensure_ascii=False, indent=2),
        "segment_handoff_plan": json.dumps(script.get("segments", []), ensure_ascii=False, indent=2),
        "loop_ledger": loops,
        "ending_and_cta": json.dumps(script["ending"], ensure_ascii=False, indent=2),
        "script_body": "\n\n".join([
            f"# {script['script_id']}",
            f"## 创作策略\n{json.dumps(strategy, ensure_ascii=False, indent=2)}",
            "## 三轨脚本\n" + "\n".join(beat_rows),
            "## 台词\n" + "\n".join(dialogue_rows),
            "## 结尾\n" + json.dumps(script["ending"], ensure_ascii=False, indent=2),
        ]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = render(json.loads(args.script.read_text(encoding="utf-8")))
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
