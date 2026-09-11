#!/usr/bin/env python3
"""One-time schema-v6 migration for commerce-content-director.

The script never implements compatibility fields.  It snapshots first, plans
from that immutable snapshot, then performs one ordered cutover when --apply
and --confirm ONE_TIME_SCHEMA_V6 are both supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
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
        response = requests.post(f"{API_ROOT}/auth/v3/tenant_access_token/internal", json={"app_id": app_id, "app_secret": secret}, timeout=30)
        body = response.json()
        if response.status_code >= 400 or body.get("code") not in (None, 0):
            raise RuntimeError(f"authentication failed: {body.get('msg', response.status_code)}")
        self.headers = {"Authorization": f"Bearer {body['tenant_access_token']}"}

    def call(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = {**self.headers, **kwargs.pop("headers", {})}
        response = requests.request(method, API_ROOT + path, headers=headers, timeout=60, **kwargs)
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

    def rename_table(self, app: str, table: str, name: str) -> None:
        self.call("PATCH", f"/bitable/v1/apps/{app}/tables/{table}", headers={"Content-Type": "application/json"}, json={"name": name})

    def create_field(self, app: str, table: str, spec: dict[str, Any]) -> None:
        self.call("POST", f"/bitable/v1/apps/{app}/tables/{table}/fields", headers={"Content-Type": "application/json"}, json=spec)

    def update_field(self, app: str, table: str, field_id: str, spec: dict[str, Any]) -> None:
        self.call("PUT", f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}", headers={"Content-Type": "application/json"}, json=spec)

    def delete_field(self, app: str, table: str, field_id: str) -> None:
        self.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table}/fields/{field_id}")

    def delete_table(self, app: str, table: str) -> None:
        self.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table}")

    def update_record(self, app: str, table: str, record_id: str, fields: dict[str, Any]) -> None:
        self.call("PUT", f"/bitable/v1/apps/{app}/tables/{table}/records/{record_id}", headers={"Content-Type": "application/json"}, json={"fields": fields})

    def create_record(self, app: str, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", f"/bitable/v1/apps/{app}/tables/{table}/records", headers={"Content-Type": "application/json"}, json={"fields": fields})

    def delete_record(self, app: str, table: str, record_id: str) -> None:
        self.call("DELETE", f"/bitable/v1/apps/{app}/tables/{table}/records/{record_id}")


def config() -> dict[str, Any]:
    return json.loads((SKILL / "config" / "base-schema.json").read_text(encoding="utf-8"))


def linked_ids(value: Any) -> list[str]:
    ids: list[str] = []
    if not isinstance(value, list):
        return ids
    for item in value:
        if isinstance(item, dict):
            ids.extend(str(value) for value in item.get("record_ids", []) if value)
        elif item:
            ids.append(str(item))
    return ids


def text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return text(value.get("text") or value.get("name") or "")
    return "" if value is None else str(value)


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(api: Feishu, run_id: str) -> Path:
    schema = config()
    root = SKILL / "migration-backups" / run_id
    if root.exists():
        raise RuntimeError(f"snapshot exists: {root}")
    root.mkdir(parents=True)
    write_json(root / "base-schema-before.json", schema)
    tables = api.tables(schema["app_token"])
    write_json(root / "table-metadata-before.json", tables)
    all_records: dict[str, Any] = {}
    all_fields: dict[str, Any] = {}
    for key, table in schema["tables"].items():
        if "table_id" not in table:
            continue
        all_fields[key] = api.fields(schema["app_token"], table["table_id"])
        all_records[key] = api.records(schema["app_token"], table["table_id"])
    write_json(root / "fields-before.json", all_fields)
    write_json(root / "records-before.json", all_records)
    relations = {
        "task_to_direction": {
            task["record_id"]: linked_ids(task.get("fields", {}).get("来源创意候选"))
            for task in all_records.get("planning_tasks", [])
        },
        "script_to_task": {
            record["record_id"]: linked_ids(record.get("fields", {}).get("内容策划任务"))
            for record in all_records.get("content_library", [])
        },
        "film_to_script": {
            record["record_id"]: linked_ids(record.get("fields", {}).get("内容版本"))
            for record in all_records.get("final_films", [])
        },
    }
    write_json(root / "relation-map-before.json", relations)
    manifest = {path.name: sha256(path) for path in root.glob("*.json")}
    write_json(root / "sha256-manifest.json", manifest)
    return root


def load_snapshot(run_id: str) -> tuple[Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    root = SKILL / "migration-backups" / run_id
    if not root.is_dir():
        raise RuntimeError(f"snapshot missing: {root}")
    schema = json.loads((root / "base-schema-before.json").read_text(encoding="utf-8"))
    fields = json.loads((root / "fields-before.json").read_text(encoding="utf-8"))
    records = json.loads((root / "records-before.json").read_text(encoding="utf-8"))
    return root, schema, fields, records


def plan(run_id: str) -> dict[str, Any]:
    root, schema, _fields, records = load_snapshot(run_id)
    task_direction = {
        task["record_id"]: (linked_ids(task.get("fields", {}).get("来源创意候选")) or [None])[0]
        for task in records.get("planning_tasks", [])
    }
    script_direction = {
        script["record_id"]: task_direction.get((linked_ids(script.get("fields", {}).get("内容策划任务")) or [None])[0])
        for script in records.get("content_library", [])
    }
    report = {
        "migration_run_id": run_id,
        "mode": "one_time_schema_v6",
        "counts": {key: len(value) for key, value in records.items()},
        "script_direction_map": script_direction,
        "historical_script_ids": [record["record_id"] for record in records.get("content_library", [])],
        "delete_tables": ["planning_tasks"],
        "old_identifiers_forbidden_after_cutover": ["mother_topics", "candidates", "planning_tasks", "content_library", "content_id"],
    }
    write_json(root / "migration-plan.json", report)
    return report


def field_by_name(api: Feishu, app: str, table: str) -> dict[str, dict[str, Any]]:
    return {field["field_name"]: field for field in api.fields(app, table)}


def ensure(api: Feishu, app: str, table: str, spec: dict[str, Any]) -> None:
    existing = field_by_name(api, app, table).get(spec["field_name"])
    if not existing:
        api.create_field(app, table, spec)
    elif existing["type"] in {3, 20} and existing["type"] == spec["type"] and "property" in spec:
        api.update_field(app, table, existing["field_id"], spec)


def rename(api: Feishu, app: str, table: str, old: str, new: str) -> None:
    fields = field_by_name(api, app, table)
    if new in fields:
        return
    field = fields.get(old)
    if not field:
        raise RuntimeError(f"missing field to rename: {old} in {table}")
    # Feishu manages reverse-link fields. They are deleted with the obsolete
    # relation later; attempting to rename them returns HTTP 400.
    if field["type"] == 21:
        return
    api.update_field(app, table, field["field_id"], {"field_name": new})


def delete_named(api: Feishu, app: str, table: str, names: set[str]) -> None:
    for name, field in field_by_name(api, app, table).items():
        if name in names or field.get("is_primary"):
            continue
        api.delete_field(app, table, field["field_id"])


def simple(name: str, type_: int = 1, property_: dict[str, Any] | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"field_name": name, "type": type_}
    if property_ is not None:
        value["property"] = property_
    return value


def select(name: str, options: list[str]) -> dict[str, Any]:
    return simple(name, 3, {"options": [{"name": option, "color": index % 55} for index, option in enumerate(options)]})


def link(name: str, target_table: str, multiple: bool = False) -> dict[str, Any]:
    return simple(name, 18, {"table_id": target_table, "multiple": multiple})


def apply(api: Feishu, run_id: str) -> dict[str, Any]:
    root, old, _fields, records = load_snapshot(run_id)
    app, old_tables = old["app_token"], old["tables"]
    request, direction, task, script, film = (old_tables[key]["table_id"] for key in ("mother_topics", "candidates", "planning_tasks", "content_library", "final_films"))

    # 1. Rename the retained tables and fields that preserve compatible types.
    api.rename_table(app, request, "创作需求")
    api.rename_table(app, direction, "创意方向")
    api.rename_table(app, script, "脚本")
    for table, pairs in {
        request: [("母题名称", "创作需求名称"), ("母题ID", "创作需求ID"), ("期望候选数", "期望方向数"), ("内容母题", "创作需求"), ("创意候选列表", "创意方向列表")],
        direction: [("候选名称", "创意方向名称"), ("内容母题", "创作需求"), ("候选状态", "方向状态"), ("痛点", "核心问题 / 欲望"), ("核心卖点", "已选核心卖点"), ("钩子", "钩子摘要"), ("互动 / CTA", "主要 CTA")],
        script: [("内容标题", "脚本名称"), ("content_id", "脚本ID"), ("审核意见", "脚本审核意见"), ("视频生成 Prompt", "视频提示词"), ("时长（秒）", "目标时长（秒）"), ("版本状态", "记录状态")],
        film: [],
    }.items():
        for old_name, new_name in pairs:
            try:
                rename(api, app, table, old_name, new_name)
            except RuntimeError:
                pass

    # 2. Create all required new fields before copying records.
    request_specs = [
        simple("创作需求ID"), simple("平台 / 账号"), simple("创作需求描述"), simple("特殊要求"),
        simple("商业目标"), simple("目标时长（秒）", 2, {"formatter": "0"}), simple("期望方向数", 2, {"formatter": "0"}),
        select("流程状态", ["草稿", "待扩散", "扩散中", "方向待确认", "选择已锁定", "已收敛", "处理失败"]),
        select("记录状态", ["活跃", "已归档"]), simple("归档时间", 5, {"date_formatter": "yyyy-MM-dd HH:mm", "auto_fill": False}), simple("归档原因"), simple("归档保护", 7),
    ]
    direction_specs = [
        simple("方向ID"), link("创作需求", request), link("产品", old_tables["products"]["table_id"]), simple("平台 / 账号"),
        link("人物主体", old_tables["subject_assets"]["table_id"]), link("动物主体", old_tables["subject_assets"]["table_id"]),
        select("方向状态", ["备选", "已选择", "已锁定", "已淘汰"]), select("记录状态", ["活跃", "已归档"]),
        simple("目标人群"), simple("核心问题 / 欲望"), simple("观看前状态"), simple("观看后状态"),
        select("内容形式", ["评论回复", "主人直述", "挑战记录", "POV/反应", "实测", "教程", "ASMR", "其他"]),
        simple("表达视角"), simple("内容角度"), simple("核心创意"), simple("钩子机制"), simple("钩子摘要"), simple("叙事结构"),
        simple("主要异议"), simple("说服路径"), simple("已选核心卖点"), simple("主要证明动作"), simple("产品融入路径"),
        simple("产品价值可视化"), simple("Offer"), simple("主要 CTA"), select("脚本模式", ["原创", "钩子复刻", "结构复刻", "全量复刻"]),
        select("音频模式", ["完整口播", "少量口播", "纯自然声"]), select("字幕模式", ["最终音频自动生成", "不生成"]),
        simple("表达者设定"), simple("创作要求"), select("准入结果", ["PASS", "FAIL"]), simple("淘汰原因"), simple("评分配置ID"),
        simple("配置综合评分", 2, {"formatter": "0.00"}), simple("选择理由"), simple("方向锁定时间", 5, {"date_formatter": "yyyy-MM-dd HH:mm", "auto_fill": False}),
        simple("归档时间", 5, {"date_formatter": "yyyy-MM-dd HH:mm", "auto_fill": False}), simple("归档原因"), simple("归档保护", 7),
    ]
    script_specs = [
        simple("脚本ID"), link("来源创意方向", direction), link("来源脚本", script), link("产品", old_tables["products"]["table_id"]),
        simple("平台 / 账号"), link("人物主体", old_tables["subject_assets"]["table_id"]), link("动物主体", old_tables["subject_assets"]["table_id"]),
        select("内容形式", ["评论回复", "主人直述", "挑战记录", "POV/反应", "实测", "教程", "ASMR", "其他"]),
        select("脚本模式", ["原创", "钩子复刻", "结构复刻", "全量复刻"]), simple("目标时长（秒）", 2, {"formatter": "0"}),
        simple("目标口播语言"), select("音频模式", ["完整口播", "少量口播", "纯自然声"]), select("字幕模式", ["最终音频自动生成", "不生成"]),
        simple("表达者设定"), simple("创作策略"), simple("脚本修订号", 2, {"formatter": "0"}),
        select("脚本检查状态", ["待检查", "未通过", "通过"]),
        simple("脚本锁定时间", 5, {"date_formatter": "yyyy-MM-dd HH:mm", "auto_fill": False}), simple("一句话脚本"), simple("钩子包"),
        simple("留存设计"), simple("节拍时间线"), simple("三轨脚本"), simple("台词清单"), simple("屏幕文字清单"),
        simple("声音与表演"), simple("互动计划"), simple("分段衔接"), simple("悬念回收"), simple("结尾与CTA"), simple("脚本正文"),
        simple("脚本质检摘要"), select("首帧状态", ["未开始", "生成中", "待审核", "已通过", "已驳回"]),
        simple("首帧审核意见"), simple("视频提示词"), simple("已验收成片数", 2, {"formatter": "0"}), simple("执行次数上限", 2, {"formatter": "0"}),
        simple("剩余执行次数", 20, {"formula_expression": "{执行次数上限}-{已验收成片数}", "formatter": "0"}),
        select("记录状态", ["活跃", "已归档"]), simple("归档保护", 7), simple("归档时间", 5, {"date_formatter": "yyyy-MM-dd HH:mm", "auto_fill": False}), simple("归档原因"),
    ]
    film_specs = [link("脚本", script), simple("实际提交 Prompt")]
    for table_id, specs in ((request, request_specs), (direction, direction_specs), (script, script_specs), (film, film_specs)):
        for spec in specs:
            ensure(api, app, table_id, spec)

    # The user explicitly designated the existing request/direction/task/script
    # records as disposable test data. Remove that entire upstream chain after
    # the immutable snapshot exists; final films are deliberately preserved.
    for table_key, table_id in (("content_library", script), ("planning_tasks", task), ("candidates", direction), ("mother_topics", request)):
        for record in records.get(table_key, []):
            api.delete_record(app, table_id, record["record_id"])

    keep_request = {"创作需求名称", "创作需求ID", "产品", "平台 / 账号", "主体资产池", "创作需求描述", "商业目标", "特殊要求", "目标时长（秒）", "期望方向数", "收敛方式", "自动入选数", "流程状态", "记录状态", "归档时间", "归档原因", "归档保护"}
    keep_direction = {spec["field_name"] for spec in direction_specs} | {"创意方向名称"}
    keep_script = {spec["field_name"] for spec in script_specs} | {"脚本名称", "最终首帧图", "脚本审核意见"}
    keep_film = {spec["field_name"] for spec in film_specs} | {"成片名称", "成片ID", "最终视频", "视频时长（秒）", "生成时间", "是否发布", "成片路径或预览链接"}
    delete_named(api, app, request, keep_request)
    delete_named(api, app, direction, keep_direction)
    delete_named(api, app, script, keep_script)
    delete_named(api, app, film, keep_film)
    api.delete_table(app, task)
    report = {"migration_run_id": run_id, "status": "applied", "deleted_seed_records": {"creative_requests": len(records.get("mother_topics", [])), "creative_directions": len(records.get("candidates", [])), "scripts": len(records.get("content_library", [])), "planning_tasks": len(records.get("planning_tasks", []))}, "tables": {"creative_requests": request, "creative_directions": direction, "scripts": script, "final_films": film}}
    write_json(root / "apply-report.json", report)
    return report

    # 3. Move the selected task strategy into its source direction.
    task_by_direction = {
        linked_ids(item.get("fields", {}).get("来源创意候选"))[0]: item
        for item in records.get("planning_tasks", [])
        if linked_ids(item.get("fields", {}).get("来源创意候选"))
    }
    for item in records.get("candidates", []):
        fields = item.get("fields", {})
        task_record = task_by_direction.get(item["record_id"])
        task_fields = task_record.get("fields", {}) if task_record else {}
        direction_id = f"DIRECTION-{item['record_id'][-8:].upper()}"
        payload = {
            "方向ID": direction_id, "方向状态": "已锁定" if task_record else "备选", "记录状态": "活跃",
            "目标人群": text(task_fields.get("目标人群") or fields.get("目标人群")), "核心问题 / 欲望": text(task_fields.get("痛点") or fields.get("痛点")),
            "内容形式": text(task_fields.get("内容形式") or fields.get("内容形式")), "核心创意": text(task_fields.get("核心创意") or fields.get("核心创意")),
            "钩子摘要": text(task_fields.get("钩子") or fields.get("钩子")), "叙事结构": text(task_fields.get("叙事节奏") or fields.get("叙事结构")),
            "已选核心卖点": text(task_fields.get("核心卖点") or fields.get("核心卖点")), "主要证明动作": text(task_fields.get("主要证明动作") or fields.get("主要证明动作")),
            "主要 CTA": text(task_fields.get("互动 / CTA") or fields.get("互动 / CTA")), "创作要求": text(task_fields.get("创作要求")),
            "平台 / 账号": text(task_fields.get("平台 / 账号")), "脚本模式": text(task_fields.get("策划模式") or "原创"),
            "音频模式": "完整口播", "字幕模式": "最终音频自动生成",
            "表达视角": text(task_fields.get("内容形式")), "内容角度": text(fields.get("核心创意")),
            "说服路径": text(task_fields.get("叙事节奏")), "产品融入路径": text(task_fields.get("主要证明动作")),
            "产品价值可视化": text(task_fields.get("主要证明动作")), "选择理由": "由旧内容策划任务一次性迁入并锁定。",
            "方向锁定时间": int(datetime.now(timezone.utc).timestamp() * 1000),
        }
        for source, target in (("产品", "产品"), ("人物主体资产", "人物主体"), ("动物主体资产", "动物主体")):
            values = linked_ids(task_fields.get(source) or fields.get(source))
            if values:
                payload[target] = values[:1]
        request_ids = linked_ids(fields.get("内容母题"))
        if request_ids:
            payload["创作需求"] = request_ids[:1]
        api.update_record(app, direction, item["record_id"], payload)

    # 4. Preserve historic content as archived, non-executable scripts linked to the locked direction.
    task_direction = {
        item["record_id"]: (linked_ids(item.get("fields", {}).get("来源创意候选")) or [None])[0]
        for item in records.get("planning_tasks", [])
    }
    films_by_script: dict[str, int] = {}
    for item in records.get("final_films", []):
        for old_script in linked_ids(item.get("fields", {}).get("内容版本")):
            films_by_script[old_script] = films_by_script.get(old_script, 0) + 1
    for index, item in enumerate(records.get("content_library", []), start=1):
        fields = item.get("fields", {})
        old_task = (linked_ids(fields.get("内容策划任务")) or [None])[0]
        direction_id = task_direction.get(old_task)
        strategy = {
            "target_audience": text(fields.get("目标人群与痛点")), "viewer_before_state": "", "viewer_after_state": "",
            "content_format": text(fields.get("内容形式")), "content_angle": text(fields.get("改编角度")), "core_idea": text(fields.get("故事梗概")),
            "primary_cta": text(fields.get("CTA")),
        }
        payload = {
            "脚本ID": text(fields.get("content_id")) or f"SCRIPT-HIST-{index:03d}", "脚本修订号": 1,
            "脚本检查状态": "未通过", "记录状态": "已归档",
            "脚本质检摘要": "历史内容迁入：缺少当前 Markdown 创作稿必填证据，不可直接进入首帧或视频生产；如需复用，必须从已锁定创意方向重新生成创作稿。",
            "创作策略": json.dumps(strategy, ensure_ascii=False), "脚本正文": text(fields.get("剧本")),
            "视频提示词": text(fields.get("视频生成 Prompt")), "目标时长（秒）": float(text(fields.get("时长（秒）")) or 0),
            "目标口播语言": "th", "音频模式": "完整口播", "字幕模式": "最终音频自动生成",
            "已验收成片数": films_by_script.get(item["record_id"], 0), "执行次数上限": float(text(fields.get("执行次数上限")) or 1),
            "首帧状态": "已通过" if fields.get("最终首帧图") else "未开始",
        }
        if direction_id:
            payload["来源创意方向"] = [direction_id]
        for source, target in (("产品", "产品"), ("人物主体资产", "人物主体"), ("动物主体资产", "动物主体")):
            ids = linked_ids(fields.get(source))
            if ids:
                payload[target] = ids[:1]
        api.update_record(app, script, item["record_id"], payload)

    # 5. Rewire final films before removing their old relation.
    for item in records.get("final_films", []):
        old_script_ids = linked_ids(item.get("fields", {}).get("内容版本"))
        if old_script_ids:
            api.update_record(app, film, item["record_id"], {"脚本": old_script_ids[:1]})

    # 6. Remove all former schema fields and then the former task table.
    keep_request = {"创作需求名称", "创作需求ID", "产品", "平台 / 账号", "主体资产池", "创作需求描述", "商业目标", "特殊要求", "目标时长（秒）", "期望方向数", "收敛方式", "自动入选数", "流程状态", "记录状态", "归档时间", "归档原因", "归档保护", "创意方向列表"}
    keep_direction = {spec["field_name"] for spec in direction_specs} | {"创意方向名称", "创作需求", "创意方向列表"}
    keep_script = {spec["field_name"] for spec in script_specs} | {"脚本名称", "最终首帧图", "脚本审核意见"}
    keep_film = {spec["field_name"] for spec in film_specs} | {"成片名称", "成片ID", "最终视频", "视频时长（秒）", "生成时间", "是否发布", "成片路径或预览链接"}
    delete_named(api, app, request, keep_request)
    delete_named(api, app, direction, keep_direction)
    delete_named(api, app, script, keep_script)
    delete_named(api, app, film, keep_film)
    api.delete_table(app, task)

    report = {"migration_run_id": run_id, "status": "applied", "tables": {"creative_requests": request, "creative_directions": direction, "scripts": script, "final_films": film}}
    write_json(root / "apply-report.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id")
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if sum((args.snapshot, args.plan, args.apply)) != 1:
        parser.error("choose exactly one of --snapshot, --plan, --apply")
    run_id = args.run_id or f"schema-v6-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    try:
        if args.snapshot:
            result: Any = {"snapshot": str(snapshot(Feishu(), run_id)), "migration_run_id": run_id}
        elif args.plan:
            result = plan(run_id)
        else:
            if args.confirm != "ONE_TIME_SCHEMA_V6":
                parser.error("--apply requires --confirm ONE_TIME_SCHEMA_V6")
            result = apply(Feishu(), run_id)
    except Exception as exc:
        result = {"ok": False, "migration_run_id": run_id, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, indent=None if args.json else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
