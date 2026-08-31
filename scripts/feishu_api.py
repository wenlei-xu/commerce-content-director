#!/usr/bin/env python3
"""Shared Feishu API helpers for the active content-system workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests


HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
API_ROOT = "https://open.feishu.cn/open-apis"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.lstrip().startswith("#"):
            key, value = raw.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


class Feishu:
    def __init__(self) -> None:
        values = read_env(SKILL / ".env")
        app_id, secret = values.get("FEISHU_APP_ID"), values.get("FEISHU_APP_SECRET")
        if not app_id or not secret:
            raise RuntimeError("FEISHU_APP_ID and FEISHU_APP_SECRET are required")
        response = requests.post(
            f"{API_ROOT}/auth/v3/tenant_access_token/internal",
            json={"app_id": app_id, "app_secret": secret},
            timeout=30,
        )
        body = response.json()
        if response.status_code >= 400 or body.get("code") not in (None, 0):
            raise RuntimeError(f"authentication failed: {body.get('msg', response.status_code)}")
        self.headers = {"Authorization": f"Bearer {body['tenant_access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = requests.request(method, API_ROOT + path, headers=headers, timeout=60, **kwargs)
        body = response.json()
        if response.status_code >= 400:
            raise RuntimeError(f"{method} {path}: HTTP {response.status_code}: {body.get('msg', body)}")
        if body.get("code") != 0:
            raise RuntimeError(f"{method} {path}: {body.get('msg', body)}")
        return body.get("data") or {}

    def fields(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/fields", params={"page_size": 500}).get("items", [])

    def records(self, app: str, table: str) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500, "automatic_fields": "true"}
            if token:
                params["page_token"] = token
            payload = self.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/records", params=params)
            result.extend(payload.get("items", []))
            if not payload.get("has_more"):
                return result
            token = payload.get("page_token")

    def update_field(self, app: str, table: str, field_id: str, spec: dict[str, Any]) -> None:
        self.call(
            "PUT",
            f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}",
            headers={"Content-Type": "application/json"},
            json=spec,
        )

    def update_record(self, app: str, table: str, record_id: str, fields: dict[str, Any]) -> None:
        self.call(
            "PUT",
            f"/bitable/v1/apps/{app}/tables/{table}/records/{record_id}",
            headers={"Content-Type": "application/json"},
            json={"fields": fields},
        )


def config() -> dict[str, Any]:
    return json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))


def linked_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            result.extend(str(record_id) for record_id in item.get("record_ids", []) if record_id)
            if item.get("record_id"):
                result.append(str(item["record_id"]))
        elif item:
            result.append(str(item))
    return result


def text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return text(value.get("text") or value.get("name") or value.get("value") or "")
    return "" if value is None else str(value)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
