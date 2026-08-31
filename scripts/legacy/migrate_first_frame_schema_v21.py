#!/usr/bin/env python3
"""One-time remote cutover from storyboard fields to first-frame fields.

This migration snapshots the affected Feishu fields and records first. It then
renames retained fields in place and removes obsolete multi-image layout and
mapping fields. It never creates duplicate compatibility fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR))

from feishu_api import Feishu, config, write_json  # noqa: E402


SKILL = SCRIPT_DIR.parent

RENAMES = {
    "system_config": {"单格画幅比例": "首帧画幅比例"},
    "scripts": {"最终分镜图": "最终首帧图", "分镜状态": "首帧状态", "分镜审核意见": "首帧审核意见"},
}
DELETE_FIELDS = {"system_config": {"每段分镜列数", "每段分镜行数"}, "scripts": {"分镜组合映射"}}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields_by_name(api: Feishu, app: str, table: str) -> dict[str, dict[str, Any]]:
    return {item["field_name"]: item for item in api.fields(app, table)}


def snapshot(api: Feishu, run_id: str) -> Path:
    schema = config()
    root = SKILL / "migration-backups" / run_id
    if root.exists():
        raise RuntimeError(f"snapshot exists: {root}")
    root.mkdir(parents=True)
    write_json(root / "base-schema-before.json", schema)
    fields: dict[str, Any] = {}
    records: dict[str, Any] = {}
    for table_key in RENAMES:
        table_id = schema["tables"][table_key]["table_id"]
        fields[table_key] = api.fields(schema["app_token"], table_id)
        records[table_key] = api.records(schema["app_token"], table_id)
    write_json(root / "fields-before.json", fields)
    write_json(root / "records-before.json", records)
    write_json(root / "sha256-manifest.json", {path.name: sha256(path) for path in root.glob("*.json")})
    return root


def load(run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root = SKILL / "migration-backups" / run_id
    if not root.is_dir():
        raise RuntimeError(f"snapshot missing: {root}")
    schema = json.loads((root / "base-schema-before.json").read_text(encoding="utf-8"))
    fields = json.loads((root / "fields-before.json").read_text(encoding="utf-8"))
    records = json.loads((root / "records-before.json").read_text(encoding="utf-8"))
    return root, schema, fields


def plan(run_id: str) -> dict[str, Any]:
    root, _schema, fields = load(run_id)
    actions: list[dict[str, Any]] = []
    for table_key, mapping in RENAMES.items():
        names = {item["field_name"] for item in fields[table_key]}
        for old, new in mapping.items():
            if old in names and new in names:
                raise RuntimeError(f"both old and new fields already exist: {table_key}/{old}/{new}")
            if old in names:
                actions.append({"table": table_key, "action": "rename", "old": old, "new": new})
        for old in DELETE_FIELDS.get(table_key, set()):
            if old in names:
                actions.append({"table": table_key, "action": "delete", "field": old})
    report = {"migration_run_id": run_id, "schema_version": 21, "actions": actions, "status": "planned"}
    write_json(root / "migration-plan.json", report)
    return report


def apply(api: Feishu, run_id: str) -> dict[str, Any]:
    root, schema, fields = load(run_id)
    report = plan(run_id)
    app = schema["app_token"]
    for action in report["actions"]:
        table_id = schema["tables"][action["table"]]["table_id"]
        current = fields_by_name(api, app, table_id)
        if action["action"] == "rename":
            field = current.get(action["old"])
            if field is None:
                if action["new"] in current:
                    continue
                raise RuntimeError(f"field disappeared before rename: {action}")
            spec: dict[str, Any] = {"field_name": action["new"], "type": field["type"]}
            if field.get("property") is not None:
                spec["property"] = field["property"]
            api.update_field(app, table_id, field["field_id"], spec)
        else:
            field = current.get(action["field"])
            if field is not None:
                api.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table_id}/fields/{field['field_id']}")
    verified: dict[str, Any] = {}
    for table_key, mapping in RENAMES.items():
        table_id = schema["tables"][table_key]["table_id"]
        current = fields_by_name(api, app, table_id)
        old_remaining = sorted((set(mapping) | DELETE_FIELDS.get(table_key, set())) & set(current))
        missing_new = sorted(set(mapping.values()) - set(current))
        if old_remaining or missing_new:
            raise RuntimeError(f"remote verification failed for {table_key}: old={old_remaining}, missing={missing_new}")
        verified[table_key] = sorted(current)
    result = {"migration_run_id": run_id, "schema_version": 21, "status": "applied", "verified_fields": verified}
    write_json(root / "apply-report.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    if sum((args.snapshot, args.plan, args.apply)) != 1:
        parser.error("choose exactly one of --snapshot, --plan, --apply")
    run_id = args.run_id or f"first-frame-v21-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    try:
        if args.snapshot:
            result: Any = {"snapshot": str(snapshot(Feishu(), run_id)), "migration_run_id": run_id}
        elif args.plan:
            result = plan(run_id)
        else:
            if args.confirm != "ONE_TIME_FIRST_FRAME_V21":
                parser.error("--apply requires --confirm ONE_TIME_FIRST_FRAME_V21")
            result = apply(Feishu(), run_id)
    except Exception as exc:
        print(json.dumps({"ok": False, "migration_run_id": run_id, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
