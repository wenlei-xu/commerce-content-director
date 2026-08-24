#!/usr/bin/env python3
"""Publish a validated script package as one pending-review Feishu script record."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--direction-record-id", required=True)
    parser.add_argument("--product-record-id", required=True)
    parser.add_argument("--record-id")
    args = parser.parse_args()

    value = json.loads(args.script.read_text(encoding="utf-8"))
    validator = load_module("validate_structured_script")
    report = validator.validate(value)
    if not report["ok"]:
        print(json.dumps({"ok": False, "errors": report["errors"]}, ensure_ascii=False))
        return 2
    renderer = load_module("render_script_views").render(value)
    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    table = schema["tables"]["scripts"]
    strategy = value["strategy_snapshot"]
    runtime = value["runtime"]
    fields = {
        "脚本名称": f"{value['script_id']}｜{strategy['content_angle']}",
        "脚本ID": value["script_id"],
        "来源创意方向": [args.direction_record_id],
        "产品": [args.product_record_id],
        "内容形式": strategy["content_format"],
        "目标时长（秒）": runtime["target_duration_seconds"],
        "目标口播语言": runtime["target_spoken_language"],
        "音频模式": {"spoken": "完整口播", "sparse_spoken": "少量口播", "natural_sound_only": "纯自然声"}[runtime["audio_mode"]],
        "字幕模式": {"auto_from_final_audio": "普通字幕", "emphasis_from_final_audio": "重点强调字幕", "none": "不生成"}[runtime["subtitle_mode"]],
        "创作策略": json.dumps(strategy, ensure_ascii=False),
        "脚本修订号": value["script_revision"],
        "脚本状态": "待审核",
        "脚本检查状态": "通过",
        "结构化脚本": json.dumps(value, ensure_ascii=False),
        "脚本质检摘要": json.dumps(report, ensure_ascii=False),
        "一句话脚本": renderer["script_summary"],
        "钩子包": renderer["hook_package"],
        "留存设计": renderer["retention_plan"],
        "节拍时间线": renderer["beat_timeline"],
        "三轨脚本": renderer["three_track_script"],
        "台词清单": renderer["dialogue_manifest"],
        "屏幕文字清单": renderer["screen_text_manifest"],
        "声音与表演": renderer["audio_performance_plan"],
        "产品动作": renderer["product_action_plan"],
        "分段衔接": renderer["segment_handoff_plan"],
        "悬念回收": renderer["loop_ledger"],
        "结尾与CTA": renderer["ending_and_cta"],
        "脚本正文": renderer["script_body"],
    }
    api = load_module("migrate_schema_v6").Feishu()
    if args.record_id:
        api.update_record(schema["app_token"], table["table_id"], args.record_id, fields)
        record_id = args.record_id
    else:
        result = api.create_record(schema["app_token"], table["table_id"], fields)
        record_id = result["record"]["record_id"]
    record = api.call("GET", f"/bitable/v1/apps/{schema['app_token']}/tables/{table['table_id']}/records/{record_id}")
    print(json.dumps({"ok": True, "record_id": record_id, "script_id": value["script_id"], "fresh_read": bool(record)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
