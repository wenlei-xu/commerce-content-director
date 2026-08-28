#!/usr/bin/env python3
"""Create the first three replacement dog identities in 主体资产库.

The seed is idempotent by 主体资产ID. It uploads the approved local anchor
first, creates the record with status=可用, and fresh-reads every record after
creation. Existing records with the same ID are reported and never duplicated.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
PROJECT = SKILL.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from feishu_attachment_uploader import FeishuAttachmentUploader  # noqa: E402
from migrate_schema_v6 import Feishu, config, write_json  # noqa: E402


AVAILABLE = "可用"
SUBJECTS: tuple[dict[str, Any], ...] = (
    {
        "asset_id": "subject-shiba-inu-01",
        "name": "柴犬 01",
        "breed": "柴犬",
        "identity": "成年赤色柴犬，奶油色口鼻、胸口和四肢，三角立耳、卷尾、中小型紧凑体型，固定为同一只狗的身份锚点。",
        "appearance": "赤色被毛、奶油色口鼻/胸口/四肢、三角立耳、卷尾、黑色鼻头、中小型紧凑体型",
        "notes": "白底四视图主体锚点：正面、左侧面、右侧面、背面；四个视角保持同一主体。",
        "file": "subject-shiba-inu-01.png",
    },
    {
        "asset_id": "subject-pembroke-corgi-01",
        "name": "柯基犬 01",
        "breed": "柯基（彭布罗克威尔士柯基）",
        "identity": "成年红白色彭布罗克威尔士柯基，白色额头鼻梁线、白胸白腿、短腿长身、大立耳、自然短尾，固定为同一只狗的身份锚点。",
        "appearance": "红棕色被毛、白色面部中线/胸口/四肢、大立耳、短腿长身、自然短尾、紧凑体型",
        "notes": "白底四视图主体锚点：正面、左侧面、右侧面、背面；四个视角保持同一主体。",
        "file": "subject-pembroke-corgi-01.png",
    },
    {
        "asset_id": "subject-yellow-labrador-01",
        "name": "拉布拉多犬 01",
        "breed": "黄色拉布拉多寻回犬",
        "identity": "成年浅黄色拉布拉多寻回犬，短而密的浅金色被毛、宽头、垂耳、深棕色眼睛、黑色鼻头、粗壮水獭尾、中大型体型，固定为同一只狗的身份锚点。",
        "appearance": "浅金黄色短密被毛、宽头、垂耳、深棕色眼睛、黑色鼻头、粗壮水獭尾、中大型体型",
        "notes": "白底四视图主体锚点：正面、左侧面、右侧面、背面；四个视角保持同一主体。",
        "file": "subject-yellow-labrador-01.png",
    },
)


def text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(text(item) for item in value if text(item))
    if isinstance(value, dict):
        return text(value.get("text") or value.get("name") or "")
    return "" if value is None else str(value)


def subject_fields(item: dict[str, Any], file_token: str) -> dict[str, Any]:
    return {
        "主体资产ID": item["asset_id"],
        "主体名称": item["name"],
        "主体锚点": [{"file_token": file_token}],
        "主体类型": "狗",
        "物种/角色": "犬",
        "品种": item["breed"],
        "主体身份描述": item["identity"],
        "外观特征": item["appearance"],
        "默认场景/服装": "中国和泰国普通家庭客厅、地垫、日常宠物互动",
        "状态": AVAILABLE,
        "备注": item["notes"],
    }


def existing_by_asset_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for record in records:
        asset_id = text((record.get("fields") or {}).get("主体资产ID"))
        if asset_id:
            result[asset_id] = record
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=f"subject-seed-v19-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    try:
        schema = config()
        table = schema["tables"]["subject_assets"]
        app = schema["app_token"]
        table_id = table["table_id"]
        api = Feishu()
        uploader = FeishuAttachmentUploader.from_env(SKILL / ".env")
        before = api.records(app, table_id)
        root = SKILL / "migration-backups" / args.run_id
        if root.exists():
            raise RuntimeError(f"snapshot exists: {root}")
        root.mkdir(parents=True)
        write_json(root / "subject-records-before.json", before)

        existing = existing_by_asset_id(before)
        report_items: list[dict[str, Any]] = []
        for item in SUBJECTS:
            old = existing.get(item["asset_id"])
            if old:
                report_items.append({
                    "asset_id": item["asset_id"],
                    "record_id": old["record_id"],
                    "status": "already_exists",
                })
                continue

            path = PROJECT / "assets" / "subject-assets" / item["file"]
            if not path.is_file():
                raise FileNotFoundError(path)
            token = uploader.upload_file(path, parent_node=app, parent_type="bitable_image")
            created = api.create_record(app, table_id, subject_fields(item, token))
            created_record = created.get("record") if isinstance(created.get("record"), dict) else {}
            record_id = (
                created.get("record_id")
                or created.get("id")
                or created_record.get("record_id")
                or created_record.get("id")
            )
            if not record_id:
                raise RuntimeError(f"创建主体记录失败：{item['asset_id']}")
            report_items.append({
                "asset_id": item["asset_id"],
                "record_id": record_id,
                "file": item["file"],
                "file_token": token,
                "status": "created",
            })

        fresh = api.records(app, table_id)
        by_id = existing_by_asset_id(fresh)
        for item in report_items:
            record = by_id.get(item["asset_id"])
            if not record:
                raise RuntimeError(f"主体记录回读失败：{item['asset_id']}")
            values = record.get("fields") or {}
            if text(values.get("状态")) != AVAILABLE:
                raise RuntimeError(f"主体状态回读失败：{item['asset_id']}")
            if text(values.get("主体类型")) != "狗" or not values.get("主体锚点"):
                raise RuntimeError(f"主体锚点或类型回读失败：{item['asset_id']}")
            item["record_id"] = record["record_id"]
            item["fresh_status"] = text(values.get("状态"))

        report = {"migration_run_id": args.run_id, "status": "applied", "items": report_items}
        write_json(root / "apply-report.json", report)
        print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=None if args.json else 2))
        return 0
    except Exception as exc:
        result = {"ok": False, "migration_run_id": args.run_id, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False, indent=None if args.json else 2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
