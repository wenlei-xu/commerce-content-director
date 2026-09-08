#!/usr/bin/env python3
"""Create and verify the two clip-first Feishu Bitable tables.

The operation is idempotent by table name: an existing table is reused and
its fields are checked instead of creating a duplicate.  The script only
creates the fields owned by the clip-library contract; it does not add a
product-anchor column or source/extraction metadata.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from feishu_api import Feishu, config  # noqa: E402


def select_field(name: str, options: list[str]) -> dict[str, Any]:
    return {
        "field_name": name,
        "type": 3,
        "ui_type": "SingleSelect",
        "property": {
            "options": [
                {"name": option, "color": index % 55}
                for index, option in enumerate(options)
            ]
        },
    }


TABLE_SPECS: list[dict[str, Any]] = [
    {
        "key": "draft_clips",
        "name": "草稿库",
        "fields": [
            # Bitable's primary field must be a text field.
            {"field_name": "产品 / SKU", "type": 1, "ui_type": "Text"},
            {"field_name": "原始10秒视频", "type": 17, "ui_type": "Attachment"},
            {"field_name": "生成 Prompt", "type": 1, "ui_type": "Text"},
            {
                "field_name": "生成日期",
                "type": 5,
                "ui_type": "DateTime",
                "property": {
                    "auto_fill": False,
                    "date_formatter": "yyyy-MM-dd HH:mm",
                },
            },
            select_field("当前状态", ["待筛选", "入选", "淘汰"]),
        ],
    },
    {
        "key": "selected_clips",
        "name": "精选片段库",
        "fields": [
            # Keep a useful record title without adding a contract field.
            {"field_name": "产品 / SKU", "type": 1, "ui_type": "Text"},
            {"field_name": "片段视频", "type": 17, "ui_type": "Attachment"},
            {"field_name": "片段标签", "type": 4, "ui_type": "MultiSelect"},
            {"field_name": "画面描述", "type": 1, "ui_type": "Text"},
            {"field_name": "适合的口播方向", "type": 1, "ui_type": "Text"},
            select_field("当前状态", ["待筛选", "可用", "淘汰"]),
        ],
    },
]


def list_tables(api: Feishu, app: str) -> list[dict[str, Any]]:
    return api.call(
        "GET", f"/bitable/v1/apps/{app}/tables", params={"page_size": 100}
    ).get("items", [])


def create_table(api: Feishu, app: str, spec: dict[str, Any]) -> str:
    data = api.call(
        "POST",
        f"/bitable/v1/apps/{app}/tables",
        headers={"Content-Type": "application/json; charset=utf-8"},
        json={
            "table": {
                "name": spec["name"],
                "default_view_name": "表格视图",
                "fields": spec["fields"],
            }
        },
    )
    table = data.get("table") or {}
    table_id = table.get("table_id") or data.get("table_id")
    if not table_id:
        raise RuntimeError(f"创建表后未返回 table_id: {data}")
    return str(table_id)


def field_summary(fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "field_id": item.get("field_id"),
            "field_name": item.get("field_name"),
            "type": item.get("type"),
            "ui_type": item.get("ui_type"),
            "options": [
                option.get("name")
                for option in (item.get("property") or {}).get("options", [])
            ],
        }
        for item in fields
    ]


def main() -> int:
    schema = config()
    app = schema["app_token"]
    api = Feishu()
    tables = list_tables(api, app)
    by_name = {item.get("name"): item for item in tables}
    report: dict[str, Any] = {"tables": {}}

    for spec in TABLE_SPECS:
        existing = by_name.get(spec["name"])
        table_id = existing.get("table_id") if existing else None
        created = False
        if not table_id:
            table_id = create_table(api, app, spec)
            created = True

        fields = api.fields(app, table_id)
        actual_names = [item.get("field_name") for item in fields]
        expected_names = [item["field_name"] for item in spec["fields"]]
        missing = [name for name in expected_names if name not in actual_names]
        if missing:
            raise RuntimeError(
                f"表 {spec['name']} ({table_id}) 缺少字段: {missing}; "
                f"实际字段: {actual_names}"
            )

        report["tables"][spec["key"]] = {
            "name": spec["name"],
            "table_id": table_id,
            "created": created,
            "fields": field_summary(fields),
        }

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
