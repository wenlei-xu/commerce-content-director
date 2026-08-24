#!/usr/bin/env python3
"""Safely rename the external-analysis table for schema v7.

The new sentence-pattern table and the new shot-template field are additive.
This script changes only the table display name, after an immutable snapshot.
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
OLD_NAME = "数据分析表"
NEW_NAME = "短视频拆解库"


def env() -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in (SKILL / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Feishu:
    def __init__(self) -> None:
        values = env()
        response = requests.post(
            f"{API_ROOT}/auth/v3/tenant_access_token/internal",
            json={"app_id": values["FEISHU_APP_ID"], "app_secret": values["FEISHU_APP_SECRET"]}, timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        if body.get("code") not in (None, 0):
            raise RuntimeError(body.get("msg", "authentication failed"))
        self.headers = {"Authorization": f"Bearer {body['tenant_access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        response = requests.request(method, API_ROOT + path, headers=self.headers, timeout=60, **kwargs)
        response.raise_for_status()
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"{method} {path}: {body.get('msg', body)}")
        return body.get("data") or {}

    def tables(self, app: str) -> list[dict[str, Any]]:
        return self.call("GET", f"/bitable/v1/apps/{app}/tables", params={"page_size": 100}).get("items", [])

    def fields(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/fields", params={"page_size": 500}).get("items", [])

    def records(self, app: str, table: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500, "automatic_fields": "true"}
            if page_token:
                params["page_token"] = page_token
            page = self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/records", params=params)
            items.extend(page.get("items", []))
            if not page.get("has_more"):
                return items
            page_token = page.get("page_token")

    def rename(self, app: str, table: str) -> None:
        self.call("PATCH", f"/bitable/v1/apps/{app}/tables/{table}", json={"name": NEW_NAME})


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def snapshot(api: Feishu, app: str, table: str, root: Path) -> None:
    if root.exists():
        raise RuntimeError(f"run already exists: {root}")
    root.mkdir(parents=True)
    write(root / "table-before.json", next(item for item in api.tables(app) if item["table_id"] == table))
    write(root / "fields-before.json", api.fields(app, table))
    write(root / "records-before.json", api.records(app, table))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"schema-v7-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    table = schema["tables"]["short_video_breakdowns"]["table_id"]
    api, app = Feishu(), schema["app_token"]
    root = SKILL / "migration-backups" / args.run_id
    snapshot(api, app, table, root)
    current = json.loads((root / "table-before.json").read_text(encoding="utf-8"))
    fields = {item["field_name"] for item in json.loads((root / "fields-before.json").read_text(encoding="utf-8"))}
    if "逐镜头复刻模板" not in fields:
        raise RuntimeError("missing required additive field: 逐镜头复刻模板")
    if current["name"] not in {OLD_NAME, NEW_NAME}:
        raise RuntimeError(f"unexpected table name: {current['name']}")
    report = {"run_id": args.run_id, "table_id": table, "before_name": current["name"], "after_name": NEW_NAME, "snapshot": str(root), "record_count": len(json.loads((root / "records-before.json").read_text(encoding="utf-8"))), "applied": False}
    if args.apply:
        if args.confirm != "RENAME_SHORT_VIDEO_BREAKDOWN":
            raise RuntimeError("--apply requires --confirm RENAME_SHORT_VIDEO_BREAKDOWN")
        if current["name"] == OLD_NAME:
            api.rename(app, table)
        after = next(item for item in api.tables(app) if item["table_id"] == table)
        if after["name"] != NEW_NAME:
            raise RuntimeError(f"rename verification failed: {after['name']}")
        report["applied"] = True
        write(root / "table-after.json", after)
    write(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
