#!/usr/bin/env python3
"""Read and validate the unique active content-system configuration into a run snapshot."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from migrate_schema_v6 import Feishu, text


SKILL_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = SKILL_DIR / "config" / "base-schema.json"
FIXED_VIDEO_MODEL = "omni_portrait"
FIXED_IMAGE_EXECUTOR = "gpt_image_2"
FIXED_IMAGE_MODEL = "gpt-image-2"
FIXED_IMAGE_SIZE = "1152x2048"
FIXED_IMAGE_QUALITY = "high"
FIXED_IMAGE_FORMAT = "png"
FIXED_RAW_SEGMENT_SECONDS = 10
FIXED_VIDEO_RATIO = "9:16"


def number(value: Any, fallback: float) -> float:
    """Normalize a Base number field without relying on the retired lifecycle helper."""
    try:
        if isinstance(value, bool):
            return fallback
        return float(text(value))
    except (TypeError, ValueError):
        return fallback


def choices(value: Any) -> list[int]:
    raw = value if isinstance(value, list) else [value]
    result: list[int] = []
    for item in raw:
        parsed = number(item, -1)
        if parsed <= 0 or not parsed.is_integer():
            raise ValueError("允许视频时长（秒）必须是正整数选项")
        result.append(int(parsed))
    return sorted(set(result))


def active_record(api: Feishu, app_token: str, table: dict[str, Any]) -> dict[str, Any]:
    records = [record for record in api.records(app_token, table["table_id"])
               if text(record.get("fields", {}).get(table["status_field"])) == table["status_active"]]
    if len(records) != 1:
        raise ValueError(f"内容系统配置必须恰好有一条{table['status_active']}记录，当前为 {len(records)} 条")
    return records[0]


def snapshot(record: dict[str, Any], table: dict[str, Any], target: int, image_model: str, video_model: str,
             image_max_inputs: int, video_max_inputs: int) -> dict[str, Any]:
    fields, mapping = record.get("fields", {}), table["fields"]
    weights = [number(fields.get(mapping[key]), -1) for key in ("retention_weight", "conversion_weight", "execution_weight")]
    if any(weight < 0 for weight in weights) or abs(sum(weights) - 100) > 1e-6:
        raise ValueError("三项候选评分权重必须为非负且总和为 100")
    allowed = choices(fields.get(mapping["allowed_durations_seconds"]))
    raw = number(fields.get(mapping["raw_segment_seconds"]), -1)
    columns = number(fields.get(mapping["storyboard_columns"]), -1)
    rows = number(fields.get(mapping["storyboard_rows"]), -1)
    ratio = text(fields.get(mapping["panel_ratio"]))
    if raw != FIXED_RAW_SEGMENT_SECONDS or columns <= 0 or not columns.is_integer() or rows <= 0 or not rows.is_integer():
        raise ValueError("Omni 原始分段时长必须固定为 10 秒，且分镜行列数必须为正整数")
    if not re.fullmatch(r"[1-9]\d*:[1-9]\d*", ratio):
        raise ValueError("单格画幅比例必须采用正整数比，例如 9:16")
    if ratio != FIXED_VIDEO_RATIO:
        raise ValueError("Omni 最终视频必须采用 9:16 竖屏配置")
    raw_int = int(raw)
    if any(duration % raw_int for duration in allowed):
        raise ValueError("每个允许视频时长必须能被原始分段时长整除")
    if target not in allowed:
        raise ValueError("目标时长不在活动内容系统配置的允许列表中")
    if target % FIXED_RAW_SEGMENT_SECONDS:
        raise ValueError("目标时长必须能被 Omni 的 10 秒原始分段整除")
    if image_max_inputs < 1 or video_max_inputs < 1:
        raise ValueError("模型输入上限必须为正整数")
    if image_model != FIXED_IMAGE_MODEL:
        raise ValueError(f"分镜生图模型必须固定为 {FIXED_IMAGE_MODEL}")
    if video_model != FIXED_VIDEO_MODEL:
        raise ValueError(f"最终视频模型必须固定为 {FIXED_VIDEO_MODEL}")
    return {
        "config_record_id": record["record_id"],
        "config_id": text(fields.get(mapping["config_id"])),
        "target_duration_seconds": target,
        "allowed_durations_seconds": allowed,
        "raw_segment_seconds": raw_int,
        "weights": {"retention": weights[0], "conversion": weights[1], "execution": weights[2]},
        "storyboard": {"columns": int(columns), "rows": int(rows), "panel_ratio": ratio},
        "model_catalog": {
            "image_executor": FIXED_IMAGE_EXECUTOR,
            "image_model": FIXED_IMAGE_MODEL,
            "image_size": FIXED_IMAGE_SIZE,
            "image_quality": FIXED_IMAGE_QUALITY,
            "image_format": FIXED_IMAGE_FORMAT,
            "video_model": FIXED_VIDEO_MODEL,
            "image_max_inputs": image_max_inputs,
            "video_max_inputs": video_max_inputs,
            "raw_segment_seconds": FIXED_RAW_SEGMENT_SECONDS,
            "video_ratio": FIXED_VIDEO_RATIO,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-duration", type=int, required=True)
    parser.add_argument("--image-model", required=True)
    parser.add_argument("--video-model", required=True)
    parser.add_argument("--image-max-inputs", type=int, required=True)
    parser.add_argument("--video-max-inputs", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    table = schema["tables"]["system_config"]
    result = snapshot(active_record(Feishu(), schema["app_token"], table), table, args.target_duration,
                      args.image_model, args.video_model, args.image_max_inputs, args.video_max_inputs)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
