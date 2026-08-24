#!/usr/bin/env python3
"""Refocus the short-video breakdown table on reusable assets for schema v10."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SKILL = Path(__file__).resolve().parent.parent
API_ROOT = "https://open.feishu.cn/open-apis"
ASSET_STATUS_FIELD = "资产状态"
ASSET_STATUS_OPTIONS = ("待审核", "可用", "仅留档", "已合并")
RETIRED_FIELDS = (
    "高光帧",
    "最强高光帧",
    "高光帧时间点",
    "最强高光帧说明",
    "关键转折点及时间",
    "关键信息释放节奏",
    "一句话故事线",
    "叙事结构路径",
    "情绪曲线",
    "视频分辨率",
    "视频帧率",
    "是否有音轨",
    "抽帧总数",
)
REQUIRED_RETAINED_FIELDS = (
    "开始分析时间",
    "完成分析时间",
    "目标受众与使用场景",
    "叙事视角与表达形式",
    "开头钩子类型",
    "核心冲突或问题",
    "钩子兑现时间与方式",
    "产品首次出现时间",
    "核心卖点及出现顺序",
    "证明链条及出现顺序",
    "主要说服机制",
    "CTA类型",
    "逐秒帧分析",
    "ASR原文",
    "OCR覆盖情况",
    "分析证据时间码",
    "整体判断置信度",
    "质量检查结果",
    "可参考的叙事模板",
    "逐段复刻模板",
    "叙事节点参考帧",
    "字幕表达模板",
)
EVIDENCE_FIELDS_FOR_HIDDEN_VIEW = (
    "逐秒帧分析",
    "ASR原文",
    "OCR覆盖情况",
    "分析证据时间码",
    "整体判断置信度",
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
        return self.call(
            "GET",
            f"/bitable/v1/apps/{app}/tables/{table}/fields",
            params={"page_size": 500},
        ).get("items", [])

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

    def views(self, app: str, table: str) -> list[dict[str, Any]]:
        return self.call(
            "GET",
            f"/bitable/v1/apps/{app}/tables/{table}/views",
            params={"page_size": 100},
        ).get("items", [])

    def delete_field(self, app: str, table: str, field_id: str) -> None:
        self.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}")

    def create_asset_status(self, app: str, table: str) -> None:
        self.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table}/fields",
            headers={"Content-Type": "application/json"},
            json={
                "field_name": ASSET_STATUS_FIELD,
                "type": 3,
                "property": {
                    "options": [
                        {"name": name, "color": index}
                        for index, name in enumerate(ASSET_STATUS_OPTIONS)
                    ]
                },
            },
        )

    def update_asset_status(self, app: str, table: str, field: dict[str, Any]) -> None:
        existing = {
            item.get("name"): item
            for item in field.get("property", {}).get("options", [])
            if item.get("name") in ASSET_STATUS_OPTIONS
        }
        options = []
        for index, name in enumerate(ASSET_STATUS_OPTIONS):
            source = existing.get(name, {})
            options.append({key: source[key] for key in ("id",) if key in source} | {"name": name, "color": index})
        self.call(
            "PUT",
            f"/bitable/v1/apps/{app}/tables/{table}/fields/{field['field_id']}",
            headers={"Content-Type": "application/json"},
            json={"field_name": ASSET_STATUS_FIELD, "type": 3, "property": {"options": options}},
        )


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"schema-v10-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()

    schema = json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))
    app = schema["app_token"]
    table = schema["tables"]["short_video_breakdowns"]["table_id"]
    api = Feishu()
    root = SKILL / "migration-backups" / args.run_id
    if root.exists():
        fields_before = json.loads((root / "fields-before.json").read_text(encoding="utf-8"))
        records_before = json.loads((root / "records-before.json").read_text(encoding="utf-8"))
        views_before = json.loads((root / "views-before.json").read_text(encoding="utf-8"))
    else:
        root.mkdir(parents=True)
        fields_before = api.fields(app, table)
        records_before = api.records(app, table)
        views_before = api.views(app, table)
        write(root / "fields-before.json", fields_before)
        write(root / "records-before.json", records_before)
        write(root / "views-before.json", views_before)

    current = {field["field_name"]: field for field in api.fields(app, table)}
    missing_retained = sorted(set(REQUIRED_RETAINED_FIELDS) - set(current))
    if missing_retained:
        raise RuntimeError(f"required retained fields are missing: {missing_retained}")

    report: dict[str, Any] = {
        "run_id": args.run_id,
        "table_id": table,
        "record_count": len(records_before),
        "field_count_before": len(fields_before),
        "retired_fields_requested": list(RETIRED_FIELDS),
        "deleted_fields": [],
        "already_absent_fields": [],
        "created_asset_status": False,
        "updated_asset_status": False,
        "evidence_fields_for_hidden_view": list(EVIDENCE_FIELDS_FOR_HIDDEN_VIEW),
        "view_column_visibility_api_supported": False,
        "manual_view_configuration": {
            "action": "在日常资产视图隐藏证据字段；在单独证据视图显示这些字段",
            "fields": list(EVIDENCE_FIELDS_FOR_HIDDEN_VIEW),
        },
        "applied": False,
    }

    if args.apply:
        if args.confirm != "APPLY_SHORT_VIDEO_BREAKDOWN_ASSET_SCHEMA":
            raise RuntimeError("--apply requires --confirm APPLY_SHORT_VIDEO_BREAKDOWN_ASSET_SCHEMA")
        for name in RETIRED_FIELDS:
            field = current.get(name)
            if field:
                api.delete_field(app, table, field["field_id"])
                report["deleted_fields"].append(name)
            else:
                report["already_absent_fields"].append(name)

        current = {field["field_name"]: field for field in api.fields(app, table)}
        asset_status = current.get(ASSET_STATUS_FIELD)
        if not asset_status:
            api.create_asset_status(app, table)
            report["created_asset_status"] = True
        elif asset_status.get("type") != 3:
            raise RuntimeError("资产状态 exists but is not a single-select field")
        else:
            names = tuple(item.get("name") for item in asset_status.get("property", {}).get("options", []))
            if names != ASSET_STATUS_OPTIONS:
                api.update_asset_status(app, table, asset_status)
                report["updated_asset_status"] = True

        fields_after = api.fields(app, table)
        after = {field["field_name"]: field for field in fields_after}
        unexpected_retired = sorted(set(RETIRED_FIELDS) & set(after))
        missing_retained = sorted(set(REQUIRED_RETAINED_FIELDS) - set(after))
        if unexpected_retired:
            raise RuntimeError(f"retired fields still exist: {unexpected_retired}")
        if missing_retained:
            raise RuntimeError(f"retained fields were lost: {missing_retained}")
        asset_status = after.get(ASSET_STATUS_FIELD)
        if not asset_status or asset_status.get("type") != 3:
            raise RuntimeError("资产状态 creation verification failed")
        names = tuple(item.get("name") for item in asset_status.get("property", {}).get("options", []))
        if names != ASSET_STATUS_OPTIONS:
            raise RuntimeError(f"资产状态 options verification failed: {names}")
        write(root / "fields-after.json", fields_after)
        write(root / "views-after.json", api.views(app, table))
        report["field_count_after"] = len(fields_after)
        report["retired_fields_absent_after"] = sorted(set(RETIRED_FIELDS) - set(after))
        report["asset_status_ready_after"] = True
        report["asset_status_options_after"] = list(names)
        report["applied"] = True

    write(root / "migration-report.json", report)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
