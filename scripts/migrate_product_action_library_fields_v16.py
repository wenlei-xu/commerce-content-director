#!/usr/bin/env python3
"""Add optional action reference images and related benefits to the product action library."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SKILL = Path(__file__).resolve().parent.parent
API_ROOT = "https://open.feishu.cn/open-apis"
FIELD_SPECS = (
    {"field_name": "动作示意图", "type": 17},
    {"field_name": "关联卖点（可选）", "type": 1},
)


def read_env() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (SKILL / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Feishu:
    def __init__(self) -> None:
        values = read_env()
        response = requests.post(
            f"{API_ROOT}/auth/v3/tenant_access_token/internal",
            json={"app_id": values["FEISHU_APP_ID"], "app_secret": values["FEISHU_APP_SECRET"]},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("code") not in (None, 0):
            raise RuntimeError(body.get("msg", "authentication failed"))
        self.headers = {"Authorization": f"Bearer {body['tenant_access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = requests.request(method, API_ROOT + path, headers=headers, timeout=60, **kwargs)
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path}: HTTP {response.status_code}: {response.text[:1000]}")
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"{method} {path}: {body.get('msg', body)}")
        return body.get("data") or {}

    def fields(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/fields", params={"page_size": 500}).get("items", [])

    def records(self, app: str, table: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500, "automatic_fields": "true"}
            if token:
                params["page_token"] = token
            page = self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/records", params=params)
            items.extend(page.get("items", []))
            if not page.get("has_more"):
                return items
            token = page.get("page_token")

    def create_field(self, app: str, table: str, spec: dict[str, Any]) -> None:
        self.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table}/fields",
            headers={"Content-Type": "application/json"},
            json=spec,
        )


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"schema-v16-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()

    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    app = schema["app_token"]
    table = schema["tables"]["product_action_library"]["table_id"]
    api = Feishu()
    root = SKILL / "migration-backups" / args.run_id
    root.mkdir(parents=True, exist_ok=True)

    fields_before = api.fields(app, table)
    records_before = api.records(app, table)
    write(root / "fields-before.json", fields_before)
    write(root / "records-before.json", records_before)

    current_by_name = {field["field_name"]: field for field in fields_before}
    mismatches = [
        {"field_name": spec["field_name"], "expected_type": spec["type"], "actual_type": current_by_name[spec["field_name"]].get("type")}
        for spec in FIELD_SPECS
        if spec["field_name"] in current_by_name and current_by_name[spec["field_name"]].get("type") != spec["type"]
    ]
    if mismatches:
        raise RuntimeError(f"existing action-library fields have incompatible types: {mismatches}")

    missing = [spec for spec in FIELD_SPECS if spec["field_name"] not in current_by_name]
    report: dict[str, Any] = {
        "run_id": args.run_id,
        "schema_version": schema["schema_version"],
        "table_id": table,
        "record_count": len(records_before),
        "missing_fields": [spec["field_name"] for spec in missing],
        "created_fields": [],
        "applied": False,
    }

    if args.apply:
        if args.confirm != "APPLY_PRODUCT_ACTION_LIBRARY_FIELDS":
            raise RuntimeError("--apply requires --confirm APPLY_PRODUCT_ACTION_LIBRARY_FIELDS")
        for spec in missing:
            api.create_field(app, table, spec)
            report["created_fields"].append(spec["field_name"])

        fields_after = api.fields(app, table)
        after_by_name = {field["field_name"]: field for field in fields_after}
        for spec in FIELD_SPECS:
            actual = after_by_name.get(spec["field_name"])
            if not actual or actual.get("type") != spec["type"]:
                raise RuntimeError(f"{spec['field_name']} verification failed")
        write(root / "fields-after.json", fields_after)
        report["applied"] = True

    write(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
