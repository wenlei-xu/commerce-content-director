#!/usr/bin/env python3
"""Schema check and dry-run archive report for 创作需求 → 创意方向 → 脚本."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from migrate_schema_v6 import Feishu, linked_ids, text

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent


def load() -> dict[str, Any]:
    return json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))


def required_names(table: dict[str, Any]) -> set[str]:
    result = set(table.get("fields", {}).values())
    for key in ("status_field", "process_field", "direction_status_field", "validation_status_field", "direction_link_field", "script_link_field", "script_link_field", "archive_time_field", "archive_reason_field", "protect_field", "execution_limit_field", "accepted_film_count_field"):
        if table.get(key):
            result.add(table[key])
    return result


def schema_check(api: Feishu, cfg: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": True, "tables": {}, "errors": []}
    for key in ("creative_requests", "creative_directions", "scripts", "final_films"):
        table = cfg["tables"][key]
        available = {field["field_name"] for field in api.fields(cfg["app_token"], table["table_id"])}
        missing = sorted(required_names(table) - available)
        report["tables"][key] = {"table": table["name"], "missing": missing}
        if missing:
            report["ok"] = False
            report["errors"].append(f"{table['name']} missing: {', '.join(missing)}")
    return report


def dry_run(api: Feishu, cfg: dict[str, Any]) -> dict[str, Any]:
    schema = schema_check(api, cfg)
    report: dict[str, Any] = {"mode": "dry-run", "schema": schema, "actions": [], "deferred": []}
    if not schema["ok"]:
        return report
    scripts = api.records(cfg["app_token"], cfg["tables"]["scripts"]["table_id"])
    directions = api.records(cfg["app_token"], cfg["tables"]["creative_directions"]["table_id"])
    requests = api.records(cfg["app_token"], cfg["tables"]["creative_requests"]["table_id"])
    direction_cfg, request_cfg = cfg["tables"]["creative_directions"], cfg["tables"]["creative_requests"]
    script_direction = {
        record["record_id"]: set(linked_ids(record.get("fields", {}).get(cfg["tables"]["scripts"]["direction_link_field"])))
        for record in scripts
    }
    for direction in directions:
        fields = direction.get("fields", {})
        status = text(fields.get(direction_cfg["direction_status_field"]))
        protected = bool(fields.get(direction_cfg["protect_field"]))
        has_scripts = any(direction["record_id"] in links for links in script_direction.values())
        if status == direction_cfg["direction_status_values"]["rejected"] and not has_scripts and not protected:
            report["actions"].append({"table": direction_cfg["name"], "record_id": direction["record_id"], "reason": "方向已淘汰且无脚本"})
    active_direction_requests = set()
    for direction in directions:
        active_direction_requests.update(linked_ids(direction.get("fields", {}).get(direction_cfg["request_link_field"])))
    for request in requests:
        fields = request.get("fields", {})
        terminal = text(fields.get(request_cfg["process_field"])) in {request_cfg["process_values"]["converged"], request_cfg["process_values"]["failed"]}
        if terminal and request["record_id"] not in active_direction_requests and not bool(fields.get(request_cfg["protect_field"])):
            report["actions"].append({"table": request_cfg["name"], "record_id": request["record_id"], "reason": "流程终态且无方向"})
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-schema", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true", help="reserved: lifecycle writes require an explicit future policy")
    args = parser.parse_args()
    cfg, api = load(), Feishu()
    report = schema_check(api, cfg) if args.check_schema else dry_run(api, cfg)
    if args.apply:
        report.setdefault("warnings", []).append("No lifecycle records were changed; apply is intentionally disabled until a write policy is approved.")
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if report.get("ok", report.get("schema", {}).get("ok")) else 2


if __name__ == "__main__":
    raise SystemExit(main())
