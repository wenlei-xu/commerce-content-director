"""Dry-run/apply soft-archive sweeper for the branching content chain.

The sweeper operates in-place in Feishu.  It only changes lifecycle fields on
内容母题、创意候选、内容策划任务 and 内容库; it never deletes, moves, copies or
repairs records.  A dry-run is the default and ``--apply`` is an explicit write.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
CONFIG_PATH = SKILL_DIR / "config" / "lifecycle-policy.json"
API_ROOT = "https://open.feishu.cn/open-apis"


def _auth() -> tuple[requests.Session, str]:
    sys.path.insert(0, str(HERE))
    from feishu_attachment_uploader import FeishuAttachmentUploader

    uploader = FeishuAttachmentUploader.from_env(SKILL_DIR / ".env")
    return uploader.session, uploader._headers_for_request()["Authorization"]


class Feishu:
    def __init__(self, app_token: str):
        self.app_token = app_token
        self.session, authorization = _auth()
        self.headers = {"Authorization": authorization}

    def _call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = self.session.request(method, API_ROOT + path, headers=headers, timeout=45, **kwargs)
        response.raise_for_status()
        body = response.json()
        if body.get("code") != 0:
            raise RuntimeError(f"Feishu {method} {path} failed: {body.get('msg', body)}")
        return body.get("data") or {}

    def fields(self, table_id: str) -> list[dict[str, Any]]:
        data = self._call("GET", f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/fields", params={"page_size": 500})
        return data.get("items", [])

    def records(self, table_id: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        token: str | None = None
        while True:
            params: dict[str, Any] = {"page_size": 500, "automatic_fields": "true"}
            if token:
                params["page_token"] = token
            data = self._call("GET", f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records", params=params)
            items.extend(data.get("items", []))
            if not data.get("has_more"):
                return items
            token = data.get("page_token")
            if not token:
                return items

    def record(self, table_id: str, record_id: str) -> dict[str, Any]:
        return self._call("GET", f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}")

    def update(self, table_id: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self._call(
            "PUT",
            f"/bitable/v1/apps/{self.app_token}/tables/{table_id}/records/{record_id}",
            headers={"Content-Type": "application/json"},
            json={"fields": fields},
        )


def scalar(value: Any) -> Any:
    if isinstance(value, list):
        return [scalar(item) for item in value]
    if isinstance(value, dict):
        for key in ("text", "name", "value", "value_text"):
            if key in value:
                return scalar(value[key])
        return value
    return value


def text(value: Any) -> str:
    value = scalar(value)
    if isinstance(value, list):
        return ",".join(text(item) for item in value if text(item))
    return "" if value is None else str(value).strip()


def truthy(value: Any) -> bool:
    value = scalar(value)
    if isinstance(value, list):
        return any(truthy(item) for item in value)
    return value is True or text(value).lower() in {"true", "1", "yes", "是", "已勾选"}


def linked_ids(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    result: set[str] = set()
    for item in value:
        if isinstance(item, dict):
            record_id = item.get("record_id") or item.get("id")
            if record_id:
                result.add(str(record_id))
        elif item:
            result.add(str(item))
    return result


def number(value: Any, default: float = 0) -> float:
    try:
        return float(text(value).replace(",", ""))
    except (TypeError, ValueError):
        return default


def now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def load_config() -> dict[str, Any]:
    policy = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    schema_path = CONFIG_PATH.parent / policy["schema"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    tables: dict[str, dict[str, Any]] = {}
    for key, policy_table in policy["tables"].items():
        table = {**schema["tables"][key], **policy_table}
        values = table.get("candidate_status_values", {})
        if "rejected_status_keys" in table:
            table["rejected_values"] = [values[value] for value in table.pop("rejected_status_keys")]
        if "selected_status_keys" in table:
            table["selected_values"] = [values[value] for value in table.pop("selected_status_keys")]
        if "terminal_process_keys" in table:
            process_values = table.get("process_values", {})
            table["terminal_process_values"] = [process_values[value] for value in table.pop("terminal_process_keys")]
        tables[key] = table
    return {**policy, "app_token": schema["app_token"], "tables": tables, "system_config": schema["tables"]["system_config"]}


def active_system_config(api: Feishu, config: dict[str, Any]) -> dict[str, Any]:
    table = config["system_config"]
    fields = table["fields"]
    matches = [record for record in api.records(table["table_id"])
               if text(record.get("fields", {}).get(table["status_field"])) == table["status_active"]]
    if len(matches) != 1:
        raise ValueError(f"内容系统配置必须恰好有一条{table['status_active']}记录，当前为 {len(matches)} 条")
    values = matches[0].get("fields", {})
    limit = number(values.get(fields["rotation_limit_default"]), 0)
    if limit <= 0:
        raise ValueError("内容系统配置的默认轮换上限必须为正数")
    return {"record_id": matches[0]["record_id"], "default_rotation_limit": limit}


def schema_check(api: Feishu, config: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {"ok": True, "tables": {}, "errors": []}
    for key, table in config["tables"].items():
        fields = api.fields(table["table_id"])
        by_name = {field.get("field_name"): field for field in fields}
        required = []
        for name_key in ("status_field", "archive_time_field", "archive_reason_field", "protect_field"):
            if table.get(name_key):
                required.append(table[name_key])
        for name_key in ("process_field", "candidate_link_field", "candidate_status_field", "task_link_field", "mother_link_field", "version_link_field", "count_formula_field", "limit_field", "source_task_link_field", "review_field", "content_link_field"):
            if table.get(name_key):
                required.append(table[name_key])
        missing = sorted({name for name in required if name not in by_name})
        formulas = [field.get("field_name") for field in fields if field.get("type") == 21 or (field.get("property") or {}).get("formula_expression")]
        table_report = {"table": table["name"], "field_count": len(fields), "missing": missing, "formula_fields": formulas}
        report["tables"][key] = table_report
        if missing:
            report["ok"] = False
            report["errors"].append(f"{table['name']} missing fields: {', '.join(missing)}")
    return report


def archive_action(table: dict[str, Any], record: dict[str, Any], reason: str) -> dict[str, Any]:
    fields = record.get("fields", {})
    return {
        "table": table["name"],
        "table_id": table["table_id"],
        "record_id": record.get("record_id"),
        "reason": reason,
        "protected": truthy(fields.get(table["protect_field"])),
        "fields": {
            table["status_field"]: table.get("status_archived", "已归档"),
            table["archive_time_field"]: now_ms(),
            table["archive_reason_field"]: reason,
        },
    }


def run(config: dict[str, Any], apply: bool, check_only: bool) -> dict[str, Any]:
    api = Feishu(config["app_token"])
    schema = schema_check(api, config)
    report: dict[str, Any] = {"mode": "apply" if apply else "dry-run", "schema": schema, "actions": [], "deferred": [], "warnings": []}
    if check_only:
        return report
    if not schema["ok"]:
        report["deferred"].append({"reason": "schema_invalid", "message": "schema check failed; no records evaluated"})
        return report

    tables = config["tables"]
    content_cfg = tables["content_library"]
    task_cfg = tables["planning_tasks"]
    candidate_cfg = tables["candidates"]
    mother_cfg = tables["mother_topics"]
    try:
        system_config = active_system_config(api, config)
    except ValueError as exc:
        report["deferred"].append({"reason": "system_config_invalid", "message": str(exc)})
        return report
    report["system_config"] = system_config
    content = api.records(content_cfg["table_id"])
    tasks = api.records(task_cfg["table_id"])
    candidates = api.records(candidate_cfg["table_id"])
    mothers = api.records(mother_cfg["table_id"])
    by_id = {"content": {r["record_id"]: r for r in content}, "tasks": {r["record_id"]: r for r in tasks}, "candidates": {r["record_id"]: r for r in candidates}, "mothers": {r["record_id"]: r for r in mothers}}

    def consider(action: dict[str, Any]) -> None:
        if action["protected"]:
            report["deferred"].append({**action, "reason": "归档保护=true"})
            return
        report["actions"].append(action)

    # Content versions: only clear rejection with a newer version. Pending/
    # broken records are deliberately kept; final-film creation is not a
    # lifecycle-archive signal.
    for record in content:
        f = record.get("fields", {})
        if text(f.get(content_cfg["status_field"])) != content_cfg["status_active"]:
            continue
        record_id = record["record_id"]
        task_ids = linked_ids(f.get(content_cfg["task_link_field"]))
        newer = [other for other in content if other["record_id"] != record_id and task_ids & linked_ids(other.get("fields", {}).get(content_cfg["task_link_field"])) and number(other.get("created_time")) > number(record.get("created_time"))]
        review = text(f.get(content_cfg["review_field"]))
        if review == content_cfg["review_reject"] and newer:
            consider(archive_action(content_cfg, record, "审核拒绝且同任务已有更新版本"))

    # Tasks: never invent a replacement. Rotation is archivable only when the
    # replacement explicitly links back through 轮换来源任务.
    for record in tasks:
        f = record.get("fields", {})
        if text(f.get(task_cfg["status_field"])) != task_cfg["status_active"]:
            continue
        count = len(linked_ids(f.get(task_cfg["version_link_field"])))
        limit = number(f.get(task_cfg["limit_field"]), system_config["default_rotation_limit"])
        replacement = any(record["record_id"] in linked_ids(other.get("fields", {}).get(task_cfg["source_task_link_field"])) and text(other.get("fields", {}).get(task_cfg["status_field"])) == task_cfg["status_active"] for other in tasks)
        if count >= limit and replacement:
            consider(archive_action(task_cfg, record, f"自动计数 {int(count)} 达到轮换上限 {int(limit)}，已有明确替代任务"))
        elif count >= limit:
            report["deferred"].append({"table": task_cfg["name"], "record_id": record["record_id"], "reason": "达到轮换上限但没有明确替代任务"})

    # Candidates: terminal outcomes or a linked task. A still-备选 candidate
    # follows its mother only after the mother itself is archived.
    archived_mothers = {a["record_id"] for a in report["actions"] if a["table"] == mother_cfg["name"]}
    for record in candidates:
        f = record.get("fields", {})
        if text(f.get(candidate_cfg["status_field"])) == candidate_cfg.get("status_archived"):
            continue
        status = text(f.get(candidate_cfg["candidate_status_field"]))
        if status in candidate_cfg["rejected_values"]:
            consider(archive_action(candidate_cfg, record, "候选状态为淘汰"))
        elif status in candidate_cfg["selected_values"] and linked_ids(f.get(candidate_cfg["task_link_field"])):
            consider(archive_action(candidate_cfg, record, "候选已落地为内容策划任务"))
        elif linked_ids(f.get(candidate_cfg["mother_link_field"])) & archived_mothers and status == "备选":
            consider(archive_action(candidate_cfg, record, "来源内容母题已归档且候选仍为备选"))

    # Mothers: archive only when explicitly terminal and every visible child is
    # terminal, preventing an archive from hiding unfinished ideation branches.
    for record in mothers:
        f = record.get("fields", {})
        if text(f.get(mother_cfg["status_field"])) == mother_cfg.get("status_archived"):
            continue
        if text(f.get(mother_cfg["process_field"])) not in mother_cfg["terminal_process_values"]:
            continue
        child_ids = linked_ids(f.get(mother_cfg["candidate_link_field"]))
        child_records = [by_id["candidates"].get(child_id) for child_id in child_ids]
        child_records = [child for child in child_records if child]
        if child_records and all(text(child.get("fields", {}).get(candidate_cfg["candidate_status_field"])) in candidate_cfg["rejected_values"] or (text(child.get("fields", {}).get(candidate_cfg["candidate_status_field"])) in candidate_cfg["selected_values"] and linked_ids(child.get("fields", {}).get(candidate_cfg["task_link_field"]))) for child in child_records):
            consider(archive_action(mother_cfg, record, "流程已终态且所有创意候选均已终结"))

    if apply:
        applied: list[dict[str, Any]] = []
        for action in report["actions"]:
            try:
                api.update(action["table_id"], action["record_id"], action["fields"])
                applied.append({"table": action["table"], "record_id": action["record_id"], "status": "updated"})
            except Exception as exc:  # keep independent records auditable
                report["warnings"].append({"table": action["table"], "record_id": action["record_id"], "error": str(exc)})
        report["applied"] = applied
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write soft-archive fields; default is dry-run")
    parser.add_argument("--check-schema", action="store_true", help="only validate required fields")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = run(load_config(), args.apply, args.check_schema)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2))
    return 0 if report["schema"]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
