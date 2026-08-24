#!/usr/bin/env python3
"""Add caption analysis and three subtitle modes for schema v9."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SKILL = Path(__file__).resolve().parent.parent
API_ROOT = "https://open.feishu.cn/open-apis"
CAPTION_FIELD = "字幕表达模板"
LEGACY_PLAIN = "最终音频自动生成"
PLAIN = "普通字幕"
EMPHASIS = "重点强调字幕"
NONE = "不生成"


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

    def create_text_field(self, app: str, table: str, name: str) -> None:
        self.call("POST", f"/bitable/v1/apps/{app}/tables/{table}/fields", headers={"Content-Type": "application/json"}, json={"field_name": name, "type": 1})

    def update_select(self, app: str, table: str, field: dict[str, Any]) -> None:
        options = []
        seen: set[str] = set()
        for option in field.get("property", {}).get("options", []):
            item = {key: option[key] for key in ("id", "color", "name") if key in option}
            if item.get("name") == LEGACY_PLAIN:
                item["name"] = PLAIN
            if item.get("name") in {PLAIN, EMPHASIS, NONE} and item["name"] not in seen:
                options.append(item)
                seen.add(item["name"])
        if PLAIN not in seen:
            options.insert(0, {"name": PLAIN, "color": 0})
        if EMPHASIS not in seen:
            none_index = next((index for index, item in enumerate(options) if item["name"] == NONE), len(options))
            options.insert(none_index, {"name": EMPHASIS, "color": 1})
        if NONE not in seen:
            options.append({"name": NONE, "color": 2})
        self.call(
            "PUT", f"/bitable/v1/apps/{app}/tables/{table}/fields/{field['field_id']}",
            headers={"Content-Type": "application/json"},
            json={"field_name": "字幕模式", "type": 3, "property": {"options": options}},
        )


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"schema-v9-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    app = schema["app_token"]
    tables = {
        "short_video_breakdowns": schema["tables"]["short_video_breakdowns"]["table_id"],
        "creative_directions": schema["tables"]["creative_directions"]["table_id"],
        "scripts": schema["tables"]["scripts"]["table_id"],
    }
    api = Feishu()
    root = SKILL / "migration-backups" / args.run_id
    if root.exists():
        fields_before = json.loads((root / "fields-before.json").read_text(encoding="utf-8"))
        records_before = json.loads((root / "records-before.json").read_text(encoding="utf-8"))
    else:
        root.mkdir(parents=True)
        fields_before = {key: api.fields(app, table) for key, table in tables.items()}
        records_before = {key: api.records(app, table) for key, table in tables.items()}
        write(root / "fields-before.json", fields_before)
        write(root / "records-before.json", records_before)
    report = {
        "run_id": args.run_id,
        "record_counts": {key: len(value) for key, value in records_before.items()},
        "created_caption_field": False,
        "updated_subtitle_mode_tables": [],
        "applied": False,
    }
    if args.apply:
        if args.confirm != "APPLY_EMPHASIS_SUBTITLES":
            raise RuntimeError("--apply requires --confirm APPLY_EMPHASIS_SUBTITLES")
        current_breakdown = {field["field_name"]: field for field in api.fields(app, tables["short_video_breakdowns"])}
        if CAPTION_FIELD not in current_breakdown:
            api.create_text_field(app, tables["short_video_breakdowns"], CAPTION_FIELD)
            report["created_caption_field"] = True
        for key in ("creative_directions", "scripts"):
            current = {field["field_name"]: field for field in api.fields(app, tables[key])}
            subtitle = current.get("字幕模式")
            if not subtitle or subtitle.get("type") != 3:
                raise RuntimeError(f"{key} missing single-select 字幕模式")
            names = [item["name"] for item in subtitle.get("property", {}).get("options", [])]
            if names != [PLAIN, EMPHASIS, NONE]:
                api.update_select(app, tables[key], subtitle)
                report["updated_subtitle_mode_tables"].append(key)
        fields_after = {key: api.fields(app, table) for key, table in tables.items()}
        breakdown_names = {field["field_name"]: field for field in fields_after["short_video_breakdowns"]}
        if CAPTION_FIELD not in breakdown_names or breakdown_names[CAPTION_FIELD]["type"] != 1:
            raise RuntimeError("字幕表达模板 verification failed")
        for key in ("creative_directions", "scripts"):
            subtitle = next(field for field in fields_after[key] if field["field_name"] == "字幕模式")
            names = [item["name"] for item in subtitle.get("property", {}).get("options", [])]
            if names != [PLAIN, EMPHASIS, NONE]:
                raise RuntimeError(f"{key} subtitle modes verification failed: {names}")
        write(root / "fields-after.json", fields_after)
        report["applied"] = True
    write(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
