#!/usr/bin/env python3
"""Create the additive storyboard-candidate table for schema v13.

The migration is intentionally non-destructive. It snapshots current Base
metadata, creates or reconciles one candidate table, creates a gallery view
when the API permits it, and fresh-reads every created object before reporting
success. The resulting table ID must then be recorded in base-schema.json.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


SKILL = Path(__file__).resolve().parent.parent
API_ROOT = "https://open.feishu.cn/open-apis"
TABLE_NAME = "分镜候选"
DEFAULT_VIEW_NAME = "全部候选"
GALLERY_VIEW_NAME = "人工选片"
STATUS_OPTIONS = ("提交中", "待选择", "已采用", "已淘汰", "生成失败")


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    path = SKILL / ".env"
    if not path.is_file():
        raise RuntimeError(f"missing credential file: {path}")
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Feishu:
    def __init__(self) -> None:
        values = read_env()
        app_id = values.get("FEISHU_APP_ID")
        app_secret = values.get("FEISHU_APP_SECRET")
        if not app_id or not app_secret:
            raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")
        response = requests.post(
            f"{API_ROOT}/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": app_secret},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("code") not in (None, 0):
            raise RuntimeError(body.get("msg", "authentication failed"))
        self.headers = {"Authorization": f"Bearer {body['tenant_access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = requests.request(
            method,
            API_ROOT + path,
            headers=headers,
            timeout=60,
            **kwargs,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"{method} {path}: HTTP {response.status_code}: {response.text[:1000]}"
            )
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"{method} {path}: {body.get('msg', body)}")
        return body.get("data") or {}

    def tables(self, app: str) -> list[dict[str, Any]]:
        return self.call(
            "GET", f"/bitable/v1/apps/{app}/tables", params={"page_size": 100}
        ).get("items", [])

    def fields(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call(
            "GET",
            f"/bitable/v1/apps/{app}/tables/{table}/fields",
            params={"page_size": 500},
        ).get("items", [])

    def records(self, app: str, table: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500, "automatic_fields": "true"}
            if page_token:
                params["page_token"] = page_token
            page = self.call(
                "GET",
                f"/bitable/v1/apps/{app}/tables/{table}/records",
                params=params,
            )
            items.extend(page.get("items", []))
            if not page.get("has_more"):
                return items
            page_token = page.get("page_token")

    def views(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call(
            "GET",
            f"/bitable/v1/apps/{app}/tables/{table}/views",
            params={"page_size": 100},
        ).get("items", [])

    def create_table(self, app: str) -> str:
        data = self.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables",
            headers={"Content-Type": "application/json"},
            json={
                "table": {
                    "name": TABLE_NAME,
                    "default_view_name": DEFAULT_VIEW_NAME,
                    "fields": [{"field_name": "候选名称", "type": 1}],
                }
            },
        )
        table_id = data.get("table_id")
        if not table_id and isinstance(data.get("table"), dict):
            table_id = data["table"].get("table_id")
        if not table_id:
            raise RuntimeError(f"create table returned no table_id: {data}")
        return str(table_id)

    def create_field(self, app: str, table: str, spec: dict[str, Any]) -> None:
        self.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table}/fields",
            headers={"Content-Type": "application/json"},
            json=spec,
        )

    def update_field(
        self, app: str, table: str, field_id: str, spec: dict[str, Any]
    ) -> None:
        self.call(
            "PUT",
            f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}",
            headers={"Content-Type": "application/json"},
            json=spec,
        )

    def create_gallery_view(self, app: str, table: str) -> None:
        self.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table}/views",
            headers={"Content-Type": "application/json"},
            json={"view_name": GALLERY_VIEW_NAME, "view_type": "gallery"},
        )


def text_field(name: str) -> dict[str, Any]:
    return {"field_name": name, "type": 1}


def number_field(name: str) -> dict[str, Any]:
    return {"field_name": name, "type": 2, "property": {"formatter": "0"}}


def select_field(name: str, options: tuple[str, ...]) -> dict[str, Any]:
    return {
        "field_name": name,
        "type": 3,
        "property": {
            "options": [
                {"name": option, "color": index % 55}
                for index, option in enumerate(options)
            ]
        },
    }


def field_specs(script_table_id: str) -> list[dict[str, Any]]:
    return [
        text_field("候选ID"),
        {
            "field_name": "脚本",
            "type": 18,
            "property": {"table_id": script_table_id, "multiple": False},
        },
        text_field("Segment ID"),
        number_field("Segment 序号"),
        text_field("目标时间范围"),
        {"field_name": "候选四宫格", "type": 17},
        select_field("候选状态", STATUS_OPTIONS),
        {"field_name": "是否采用", "type": 7},
        number_field("生成轮次"),
        text_field("Run ID"),
        text_field("Flow2API Job ID"),
        text_field("幂等键"),
        text_field("模型ID"),
        text_field("附件SHA256"),
        text_field("审核意见"),
    ]


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def table_by_name(tables: list[dict[str, Any]]) -> dict[str, Any] | None:
    matches = [item for item in tables if item.get("name") == TABLE_NAME]
    if len(matches) > 1:
        raise RuntimeError(f"multiple {TABLE_NAME} tables found")
    return matches[0] if matches else None


def option_names(field: dict[str, Any]) -> tuple[str, ...]:
    return tuple(
        str(item.get("name"))
        for item in field.get("property", {}).get("options", [])
    )


def ensure_fields(
    api: Feishu, app: str, table: str, specs: list[dict[str, Any]]
) -> list[str]:
    created: list[str] = []
    existing = {item["field_name"]: item for item in api.fields(app, table)}
    for spec in specs:
        name = spec["field_name"]
        current = existing.get(name)
        if not current:
            api.create_field(app, table, spec)
            created.append(name)
            existing = {item["field_name"]: item for item in api.fields(app, table)}
            continue
        if current.get("type") != spec.get("type"):
            raise RuntimeError(
                f"field {name} has type {current.get('type')}, expected {spec.get('type')}"
            )
        if spec.get("type") == 3 and option_names(current) != STATUS_OPTIONS:
            retained = {
                item.get("name"): item
                for item in current.get("property", {}).get("options", [])
            }
            options = []
            for index, option in enumerate(STATUS_OPTIONS):
                old = retained.get(option, {})
                options.append(
                    ({"id": old["id"]} if old.get("id") else {})
                    | {"name": option, "color": index % 55}
                )
            updated = {**spec, "property": {"options": options}}
            api.update_field(app, table, current["field_id"], updated)
    return created


def verify_fields(fields: list[dict[str, Any]], specs: list[dict[str, Any]]) -> None:
    by_name = {field["field_name"]: field for field in fields}
    for spec in specs:
        actual = by_name.get(spec["field_name"])
        if not actual:
            raise RuntimeError(f"missing field after migration: {spec['field_name']}")
        if actual.get("type") != spec.get("type"):
            raise RuntimeError(f"field type verification failed: {spec['field_name']}")
    status = by_name["候选状态"]
    if option_names(status) != STATUS_OPTIONS:
        raise RuntimeError(
            f"候选状态 options verification failed: {option_names(status)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-id",
        default=f"schema-v13-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()

    schema = json.loads(
        (SKILL / "config" / "base-schema.json").read_text(encoding="utf-8")
    )
    app = schema["app_token"]
    scripts_table = schema["tables"]["scripts"]["table_id"]
    specs = field_specs(scripts_table)
    api = Feishu()
    root = SKILL / "migration-backups" / args.run_id
    if root.exists():
        raise RuntimeError(f"migration run already exists: {root}")
    root.mkdir(parents=True)

    tables_before = api.tables(app)
    write_json(root / "tables-before.json", tables_before)
    existing = table_by_name(tables_before)
    if existing:
        table_id = str(existing["table_id"])
        write_json(root / "fields-before.json", api.fields(app, table_id))
        write_json(root / "records-before.json", api.records(app, table_id))
        write_json(root / "views-before.json", api.views(app, table_id))
    else:
        table_id = ""

    report: dict[str, Any] = {
        "run_id": args.run_id,
        "table_name": TABLE_NAME,
        "table_id": table_id or None,
        "table_exists_before": bool(existing),
        "created_table": False,
        "created_fields": [],
        "created_gallery_view": False,
        "manual_view_configuration": {
            "view": GALLERY_VIEW_NAME,
            "group_by": ["脚本", "Segment 序号"],
            "cover_field": "候选四宫格",
            "visible_fields": ["候选名称", "候选状态", "是否采用", "审核意见"],
        },
        "applied": False,
    }

    if args.apply:
        if args.confirm != "APPLY_STORYBOARD_CANDIDATES_V13":
            raise RuntimeError(
                "--apply requires --confirm APPLY_STORYBOARD_CANDIDATES_V13"
            )
        if not table_id:
            table_id = api.create_table(app)
            report["created_table"] = True
        report["table_id"] = table_id
        report["created_fields"] = ensure_fields(api, app, table_id, specs)

        views = api.views(app, table_id)
        if GALLERY_VIEW_NAME not in {item.get("view_name") for item in views}:
            try:
                api.create_gallery_view(app, table_id)
                report["created_gallery_view"] = True
            except RuntimeError as error:
                report["gallery_view_api_error"] = str(error)

        tables_after = api.tables(app)
        after = table_by_name(tables_after)
        if not after or str(after.get("table_id")) != table_id:
            raise RuntimeError("table fresh-read verification failed")
        fields_after = api.fields(app, table_id)
        verify_fields(fields_after, specs)
        records_after = api.records(app, table_id)
        views_after = api.views(app, table_id)
        write_json(root / "tables-after.json", tables_after)
        write_json(root / "fields-after.json", fields_after)
        write_json(root / "records-after.json", records_after)
        write_json(root / "views-after.json", views_after)
        report["record_count_after"] = len(records_after)
        report["view_names_after"] = [item.get("view_name") for item in views_after]
        report["applied"] = True

    write_json(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
