#!/usr/bin/env python3
"""Add the reversible subject availability state and disable the beagle asset.

The command is intentionally narrow and idempotent.  It updates only the
主体资产库 status select and the uniquely identified beagle record; it does
not delete assets or rewrite existing task/script relations.

Examples:
  python scripts/migrate_subject_assets_status_v18.py --json
  python scripts/migrate_subject_assets_status_v18.py --apply \
      --confirm DISABLE_BEAGLE_SUBJECT --json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feishu_api import Feishu, config, write_json


HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
AVAILABLE = "可用"
LEGACY_DISABLED = "停用"
DISABLED = "禁用"
CONFIRMATION = "DISABLE_BEAGLE_SUBJECT"


def text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return text(value.get("text") or value.get("name") or "")
    return "" if value is None else str(value)


def fields_by_name(api: Feishu, app: str, table: str) -> dict[str, dict[str, Any]]:
    return {field["field_name"]: field for field in api.fields(app, table)}


def normalized_status_options(field: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    if field.get("type") != 3:
        raise RuntimeError("主体资产库的状态字段必须是单选字段")
    options = (field.get("property") or {}).get("options") or []
    if not options:
        raise RuntimeError("主体资产库的状态字段没有任何选项")

    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    changed = False
    for index, option in enumerate(options):
        item = dict(option)
        name = text(item.get("name"))
        if name == LEGACY_DISABLED:
            name = DISABLED
            item["name"] = name
            changed = True
        if name not in seen:
            item.setdefault("color", index % 55)
            normalized.append(item)
            seen.add(name)

    if AVAILABLE not in seen:
        normalized.insert(0, {"name": AVAILABLE, "color": 0})
        changed = True
    if DISABLED not in seen:
        normalized.append({"name": DISABLED, "color": 1})
        changed = True
    return normalized, changed


def find_beagle(records: list[dict[str, Any]], record_id: str | None) -> dict[str, Any]:
    if record_id:
        matches = [record for record in records if record.get("record_id") == record_id]
    else:
        matches = []
        for record in records:
            values = record.get("fields") or {}
            searchable = " ".join(
                text(values.get(key))
                for key in ("主体资产ID", "主体名称", "品种", "主体身份描述", "外观特征")
            ).lower()
            subject_type = text(values.get("主体类型"))
            if subject_type == "狗" and ("beagle" in searchable or "比格" in searchable):
                matches.append(record)
    if not matches:
        raise RuntimeError("未找到唯一的比格犬主体；请用 --record-id 指定目标记录")
    if len(matches) > 1:
        ids = ", ".join(str(item.get("record_id")) for item in matches)
        raise RuntimeError(f"找到多条比格犬主体（{ids}）；请用 --record-id 指定目标记录")
    return matches[0]


def build_plan(api: Feishu, record_id: str | None) -> dict[str, Any]:
    schema = config()
    app = schema["app_token"]
    table = schema["tables"]["subject_assets"]
    table_id = table["table_id"]
    fields = fields_by_name(api, app, table_id)
    status_name = table["status_field"]
    status_field = fields.get(status_name)
    if not status_field:
        raise RuntimeError(f"主体资产库缺少状态字段：{status_name}")
    options, options_changed = normalized_status_options(status_field)
    beagle = find_beagle(api.records(app, table_id), record_id)
    beagle_fields = beagle.get("fields") or {}
    return {
        "schema_version": schema["schema_version"],
        "table_id": table_id,
        "status_field_id": status_field["field_id"],
        "status_options_before": (status_field.get("property") or {}).get("options") or [],
        "status_options_after": options,
        "status_options_changed": options_changed,
        "beagle_record_id": beagle["record_id"],
        "beagle_asset_id": text(beagle_fields.get("主体资产ID")),
        "beagle_name": text(beagle_fields.get("主体名称")),
        "beagle_status_before": text(beagle_fields.get(status_name)),
        "beagle_status_after": DISABLED,
    }


def apply(api: Feishu, run_id: str, record_id: str | None) -> dict[str, Any]:
    schema = config()
    app = schema["app_token"]
    table = schema["tables"]["subject_assets"]
    table_id = table["table_id"]
    root = SKILL / "migration-backups" / run_id
    if root.exists():
        raise RuntimeError(f"snapshot exists: {root}")
    root.mkdir(parents=True)

    before_fields = api.fields(app, table_id)
    before_records = api.records(app, table_id)
    write_json(root / "base-schema-before.json", schema)
    write_json(root / "subject-fields-before.json", before_fields)
    write_json(root / "subject-records-before.json", before_records)

    plan = build_plan(api, record_id)
    if plan["status_options_changed"]:
        api.update_field(
            app,
            table_id,
            plan["status_field_id"],
            {
                "field_name": table["status_field"],
                "type": 3,
                "property": {"options": plan["status_options_after"]},
            },
        )
    api.update_record(app, table_id, plan["beagle_record_id"], {table["status_field"]: DISABLED})

    fresh_fields = fields_by_name(api, app, table_id)
    fresh_records = api.records(app, table_id)
    fresh_status_field = fresh_fields.get(table["status_field"])
    fresh_beagle = next((item for item in fresh_records if item.get("record_id") == plan["beagle_record_id"]), None)
    if not fresh_status_field or DISABLED not in {
        text(option.get("name")) for option in (fresh_status_field.get("property") or {}).get("options", [])
    }:
        raise RuntimeError("状态字段回读失败：缺少‘禁用’选项")
    if not fresh_beagle or text((fresh_beagle.get("fields") or {}).get(table["status_field"])) != DISABLED:
        raise RuntimeError("比格主体回读失败：状态不是‘禁用’")

    report = {
        "migration_run_id": run_id,
        "status": "applied",
        "plan": plan,
        "fresh_read": {
            "status_options": (fresh_status_field.get("property") or {}).get("options") or [],
            "beagle_record_id": fresh_beagle["record_id"],
            "beagle_status": text((fresh_beagle.get("fields") or {}).get(table["status_field"])),
        },
    }
    write_json(root / "apply-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="执行远程变更；省略时只输出计划")
    parser.add_argument("--confirm")
    parser.add_argument("--record-id")
    parser.add_argument("--run-id", default=f"subject-assets-v18-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        api = Feishu()
        if args.apply:
            if args.confirm != CONFIRMATION:
                parser.error(f"--apply requires --confirm {CONFIRMATION}")
            result = apply(api, args.run_id, args.record_id)
        else:
            result = {"status": "planned", "plan": build_plan(api, args.record_id)}
    except Exception as exc:
        result = {"ok": False, "error": str(exc), "migration_run_id": args.run_id}
        print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
