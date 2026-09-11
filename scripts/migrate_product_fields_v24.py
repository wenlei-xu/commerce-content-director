#!/usr/bin/env python3
"""Simplify the product table and preserve a resumable migration snapshot."""

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

OLD_FIELDS = [
    "可用表达 / 可用宣称",
    "禁用表达 / 禁用宣称",
    "产品硬事实与禁忌",
    "生成注意事项",
    "产品审核要求",
]
RENAME_FROM = "交互限制"
RENAME_TO = "交互能力"
NEW_FIELD = "关键结构锁"


def field_map(api: Feishu, app: str, table: str) -> dict[str, dict[str, Any]]:
    return {item["field_name"]: item for item in api.fields(app, table)}


def snapshot(api: Feishu, schema: dict[str, Any], run_id: str) -> tuple[Path, dict[str, Any]]:
    root = SKILL / "migration-backups" / run_id
    if root.exists():
        raise RuntimeError(f"migration backup already exists: {root}")
    root.mkdir(parents=True)
    table = schema["tables"]["products"]
    before = {
        "schema": schema,
        "table_id": table["table_id"],
        "fields": api.fields(schema["app_token"], table["table_id"]),
        "records": api.records(schema["app_token"], table["table_id"]),
    }
    write_json(root / "before.json", before)
    return root, before


def apply(api: Feishu, schema: dict[str, Any]) -> dict[str, Any]:
    app = schema["app_token"]
    table_id = schema["tables"]["products"]["table_id"]
    fields = field_map(api, app, table_id)

    if RENAME_TO not in fields and RENAME_FROM in fields:
        source = fields[RENAME_FROM]
        api.update_field(app, table_id, source["field_id"], {"field_name": RENAME_TO, "type": source["type"]})

    fields = field_map(api, app, table_id)
    if NEW_FIELD not in fields:
        api.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table_id}/fields",
            headers={"Content-Type": "application/json"},
            json={"field_name": NEW_FIELD, "type": 1},
        )

    deleted: list[str] = []
    fields = field_map(api, app, table_id)
    for name in OLD_FIELDS:
        item = fields.get(name)
        if item:
            api.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table_id}/fields/{item['field_id']}")
            deleted.append(name)

    after = field_map(api, app, table_id)
    missing = sorted({RENAME_TO, NEW_FIELD} - set(after))
    remaining = sorted(set(OLD_FIELDS + [RENAME_FROM]) & set(after))
    if missing or remaining:
        raise RuntimeError(f"field verification failed: missing={missing}, remaining={remaining}")
    return {"deleted": deleted, "renamed": RENAME_FROM if RENAME_TO in after else None, "added": NEW_FIELD}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=f"product-fields-v24-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()

    api = Feishu()
    schema = config()
    root, before = snapshot(api, schema, args.run_id)
    existing = {item["field_name"] for item in before["fields"]}
    report: dict[str, Any] = {
        "run_id": args.run_id,
        "backup": str(root / "before.json"),
        "delete": [name for name in OLD_FIELDS if name in existing],
        "rename": {"from": RENAME_FROM, "to": RENAME_TO},
        "add": NEW_FIELD,
        "applied": False,
    }
    if args.apply:
        if args.confirm != "APPLY_PRODUCT_FIELDS_V24":
            raise RuntimeError("--apply requires --confirm APPLY_PRODUCT_FIELDS_V24")
        report["result"] = apply(api, schema)
        report["applied"] = True
    write_json(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
