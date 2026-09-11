#!/usr/bin/env python3
"""Safely cut over the Feishu action library to interaction templates.

The migration intentionally does not infer how a product-specific action should
be generalized.  It snapshots first, adds the new fields, retires every legacy
row from runtime use, and leaves semantic normalization to a human reviewer.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from feishu_api import Feishu, config, write_json

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TEMPLATE_STATUS_OPTIONS = ["待整理", "待确认", "可用", "停用"]


def field(name: str, type_: int = 1, property_: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"field_name": name, "type": type_}
    if property_ is not None:
        result["property"] = property_
    return result


PRODUCT_FIELDS = (
    field("交互能力"),
)
TEMPLATE_FIELDS = (
    field("内容功能", 4, {"options": [{"name": option, "color": index % 55} for index, option in enumerate(["兴趣", "互动", "情绪", "节奏", "证明", "转场", "CTA"])]}),
    field("模板状态", 3, {"options": [{"name": option, "color": index % 55} for index, option in enumerate(TEMPLATE_STATUS_OPTIONS)]}),
)
RENAMES = (
    ("动作", "互动模板", 1),
    ("怎么玩", "行为流程", 1),
    ("画面重点", "可视验收点", 1),
    ("动作示意图", "互动示意图", 17),
)


def current_fields(api: Feishu, app: str, table: str) -> dict[str, dict[str, Any]]:
    return {item["field_name"]: item for item in api.fields(app, table)}


def snapshot(api: Feishu, run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root = SKILL / "migration-backups" / run_id
    if root.exists():
        raise RuntimeError(f"migration backup already exists: {root}")
    root.mkdir(parents=True)
    schema = config()
    products = schema["tables"]["products"]
    templates = schema["tables"]["content_interaction_templates"]
    before = {
        "schema": schema,
        "products": {
            "fields": api.fields(schema["app_token"], products["table_id"]),
            "records": api.records(schema["app_token"], products["table_id"]),
        },
        "templates": {
            "fields": api.fields(schema["app_token"], templates["table_id"]),
            "records": api.records(schema["app_token"], templates["table_id"]),
        },
    }
    write_json(root / "before.json", before)
    return root, schema, before


def load_snapshot(run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root = SKILL / "migration-backups" / run_id
    before_path = root / "before.json"
    if not before_path.exists():
        raise RuntimeError(f"migration snapshot missing: {before_path}")
    before = json.loads(before_path.read_text(encoding="utf-8"))
    return root, before["schema"], before


def plan(schema: dict[str, Any], before: dict[str, Any], run_id: str) -> dict[str, Any]:
    product_names = {item["field_name"] for item in before["products"]["fields"]}
    template_names = {item["field_name"] for item in before["templates"]["fields"]}
    return {
        "run_id": run_id,
        "schema_version": schema["schema_version"],
        "legacy_action_record_count": len(before["templates"]["records"]),
        "add_product_fields": [spec["field_name"] for spec in PRODUCT_FIELDS if spec["field_name"] not in product_names],
        "add_template_fields": [spec["field_name"] for spec in TEMPLATE_FIELDS if spec["field_name"] not in template_names],
        "rename_template_fields": [
            {"from": old, "to": new}
            for old, new, _type in RENAMES
            if old in template_names and new not in template_names
        ],
        "retained_legacy_fields": ["产品", "关联卖点（可选）", "是否可用"],
        "post_apply_required": [
            "Keep product interaction capabilities and 关键结构锁 authoritative.",
            "Create or normalize only genuinely cross-SKU interaction templates.",
            "Set 模板状态=可用 only after template review; legacy rows are set to 待整理.",
            "Do not delete retained legacy fields or rows until the normalized templates have been verified.",
        ],
    }


def ensure(api: Feishu, app: str, table: str, spec: dict[str, Any]) -> None:
    existing = current_fields(api, app, table).get(spec["field_name"])
    if not existing:
        api.create_field(app, table, spec)
        return
    if existing.get("type") != spec["type"]:
        raise RuntimeError(f"field {spec['field_name']} has incompatible type {existing.get('type')}")


def rename(api: Feishu, app: str, table: str, old: str, new: str, expected_type: int) -> None:
    fields = current_fields(api, app, table)
    if new in fields:
        return
    source = fields.get(old)
    if not source:
        return
    if source.get("type") != expected_type:
        raise RuntimeError(f"cannot rename {old}: expected field type {expected_type}, got {source.get('type')}")
    # Feishu requires the field type on PUT, even for a name-only rename.
    api.update_field(app, table, source["field_id"], {"field_name": new, "type": expected_type})


def apply(api: Feishu, schema: dict[str, Any], before: dict[str, Any]) -> dict[str, Any]:
    app = schema["app_token"]
    products = schema["tables"]["products"]
    templates = schema["tables"]["content_interaction_templates"]
    for spec in PRODUCT_FIELDS:
        ensure(api, app, products["table_id"], spec)
    for old, new, expected_type in RENAMES:
        rename(api, app, templates["table_id"], old, new, expected_type)
    for spec in TEMPLATE_FIELDS:
        ensure(api, app, templates["table_id"], spec)
    api.rename_table(app, templates["table_id"], templates["name"])

    legacy_ids = [record["record_id"] for record in before["templates"]["records"]]
    for record_id in legacy_ids:
        api.update_record(app, templates["table_id"], record_id, {"模板状态": "待整理"})

    after_product_fields = current_fields(api, app, products["table_id"])
    after_template_fields = current_fields(api, app, templates["table_id"])
    required_product = {spec["field_name"] for spec in PRODUCT_FIELDS}
    required_template = {new for _old, new, _type in RENAMES} | {spec["field_name"] for spec in TEMPLATE_FIELDS}
    missing = sorted((required_product - set(after_product_fields)) | (required_template - set(after_template_fields)))
    if missing:
        raise RuntimeError(f"field verification failed: {missing}")
    fresh_records = api.records(app, templates["table_id"])
    legacy_status = {
        record["record_id"]: record.get("fields", {}).get("模板状态")
        for record in fresh_records if record["record_id"] in legacy_ids
    }
    if any(status != "待整理" for status in legacy_status.values()):
        raise RuntimeError("legacy action rows were not retired from template selection")
    return {"retired_legacy_records": len(legacy_ids), "template_table_id": templates["table_id"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"interaction-templates-v17-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        api = Feishu()
        existing_snapshot = SKILL / "migration-backups" / args.run_id / "before.json"
        if existing_snapshot.exists():
            root, schema, before = load_snapshot(args.run_id)
        else:
            root, schema, before = snapshot(api, args.run_id)
        report = plan(schema, before, args.run_id)
        if args.apply:
            if args.confirm != "APPLY_CONTENT_INTERACTION_TEMPLATES_V17":
                raise RuntimeError("--apply requires --confirm APPLY_CONTENT_INTERACTION_TEMPLATES_V17")
            report["apply"] = apply(api, schema, before)
            report["applied"] = True
        else:
            report["applied"] = False
        write_json(root / "migration-report.json", report)
        print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
