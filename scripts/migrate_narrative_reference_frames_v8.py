#!/usr/bin/env python3
"""Add narrative start frames and rename the replication template for schema v8."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SKILL = Path(__file__).resolve().parent.parent
API_ROOT = "https://open.feishu.cn/open-apis"
OLD_FIELD = "逐镜头复刻模板"
NEW_FIELD = "逐段复刻模板"
FRAME_FIELD = "叙事节点参考帧"


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
            json={"app_id": values["FEISHU_APP_ID"], "app_secret": values["FEISHU_APP_SECRET"]}, timeout=30,
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

    def rename_field(self, app: str, table: str, field_id: str) -> None:
        self.call("PUT", f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}", headers={"Content-Type": "application/json"}, json={"field_name": NEW_FIELD, "type": 1})

    def create_attachment_field(self, app: str, table: str) -> None:
        self.call("POST", f"/bitable/v1/apps/{app}/tables/{table}/fields", headers={"Content-Type": "application/json"}, json={"field_name": FRAME_FIELD, "type": 17})


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"schema-v8-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    app = schema["app_token"]
    table = schema["tables"]["short_video_breakdowns"]["table_id"]
    api = Feishu()
    root = SKILL / "migration-backups" / args.run_id
    if root.exists():
        before_fields = json.loads((root / "fields-before.json").read_text(encoding="utf-8"))
        before_records = json.loads((root / "records-before.json").read_text(encoding="utf-8"))
    else:
        root.mkdir(parents=True)
        before_fields = api.fields(app, table)
        before_records = api.records(app, table)
        write(root / "fields-before.json", before_fields)
        write(root / "records-before.json", before_records)
    by_name = {field["field_name"]: field for field in before_fields}
    current_fields = api.fields(app, table)
    current_by_name = {field["field_name"]: field for field in current_fields}
    if OLD_FIELD not in current_by_name and NEW_FIELD not in current_by_name:
        raise RuntimeError(f"neither {OLD_FIELD} nor {NEW_FIELD} exists")
    nonempty_old = sum(1 for record in before_records if record.get("fields", {}).get(OLD_FIELD))
    report = {
        "run_id": args.run_id,
        "table_id": table,
        "record_count": len(before_records),
        "nonempty_legacy_template_count": nonempty_old,
        "renamed_field": False,
        "created_reference_frame_field": False,
        "applied": False,
    }
    if args.apply:
        if args.confirm != "APPLY_NARRATIVE_REFERENCE_FRAMES":
            raise RuntimeError("--apply requires --confirm APPLY_NARRATIVE_REFERENCE_FRAMES")
        if OLD_FIELD in current_by_name and NEW_FIELD not in current_by_name:
            api.rename_field(app, table, current_by_name[OLD_FIELD]["field_id"])
            report["renamed_field"] = True
        if FRAME_FIELD not in current_by_name:
            api.create_attachment_field(app, table)
            report["created_reference_frame_field"] = True
        after_fields = api.fields(app, table)
        after_by_name = {field["field_name"]: field for field in after_fields}
        if NEW_FIELD not in after_by_name or after_by_name[NEW_FIELD]["type"] != 1:
            raise RuntimeError("逐段复刻模板 verification failed")
        if FRAME_FIELD not in after_by_name or after_by_name[FRAME_FIELD]["type"] != 17:
            raise RuntimeError("叙事节点参考帧 verification failed")
        write(root / "fields-after.json", after_fields)
        report["applied"] = True
    write(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
