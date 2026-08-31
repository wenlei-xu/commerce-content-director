#!/usr/bin/env python3
"""Merge duplicate exploration flows and remove migrated SKU-specific rows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from feishu_api import Feishu, config, text, write_json  # noqa: E402

DUPLICATE_TEMPLATE_NAMES = {"推动探索", "闻扒寻找", "闻扒咬推动"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"dedupe-interaction-templates-v17-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        api = Feishu()
        schema = config()
        app = schema["app_token"]
        table = schema["tables"]["content_interaction_templates"]
        fields = table["fields"]
        records = api.records(app, table["table_id"])
        snapshot_root = HERE.parent / "migration-backups" / args.run_id
        before_path = snapshot_root / "records-before.json"
        if before_path.exists():
            before_records = json.loads(before_path.read_text(encoding="utf-8"))
        else:
            snapshot_root.mkdir(parents=True)
            before_records = records
            write_json(before_path, before_records)

        # The first run snapshot is the immutable set used for this dedupe.
        # It already contains the post-cutover field names and is resilient to
        # a retry after an interrupted batch of deletes.
        legacy_ids = {
            item["record_id"] for item in before_records
            if text(item.get("fields", {}).get(fields["template_name"])) in DUPLICATE_TEMPLATE_NAMES
        }
        current_by_id = {item["record_id"]: item for item in records}
        stale_ids = sorted(
            record_id for record_id in legacy_ids
            if record_id in current_by_id
            and text(current_by_id[record_id].get("fields", {}).get(table["availability_field"])) == "待整理"
        )
        if any(
            text(current_by_id[record_id].get("fields", {}).get(table["availability_field"])) != "待整理"
            for record_id in legacy_ids & set(current_by_id) - set(stale_ids)
        ):
            raise RuntimeError("duplicate source row is no longer in 待整理 state; refusing deletion")

        active = next(
            (record for record in records if text(record.get("fields", {}).get(fields["template_name"])) == "地面探索取食"),
            None,
        )
        if not active:
            raise RuntimeError("canonical template not found: 地面探索取食")
        report: dict[str, Any] = {
            "run_id": args.run_id,
            "duplicate_source_records": stale_ids,
            "canonical_template_record": active["record_id"],
            "merged_behavior_flow": "产品放到地面后，狗狗先接近闻嗅，再用鼻子或爪子推动，可短暂咬触并持续探索或取食。",
            "merged_visual_acceptance": "闻嗅、扒动、推动和可选短暂咬触清楚可见；产品接触点、朝向和一体结构保持可辨。",
            "applied": False,
        }
        if args.apply:
            if args.confirm != "APPLY_DEDUPE_INTERACTION_TEMPLATES_V17":
                raise RuntimeError("--apply requires --confirm APPLY_DEDUPE_INTERACTION_TEMPLATES_V17")
            api.update_record(
                app,
                table["table_id"],
                active["record_id"],
                {
                    fields["behavior_flow"]: report["merged_behavior_flow"],
                    fields["visual_acceptance"]: report["merged_visual_acceptance"],
                },
            )
            for record_id in stale_ids:
                api.delete_record(app, table["table_id"], record_id)
            fresh = api.records(app, table["table_id"])
            fresh_ids = {record["record_id"] for record in fresh}
            if any(record_id in fresh_ids for record_id in stale_ids):
                raise RuntimeError("duplicate legacy record deletion verification failed")
            canonical = next(record for record in fresh if record["record_id"] == active["record_id"])
            canonical_fields = canonical.get("fields", {})
            if text(canonical_fields.get(fields["behavior_flow"])) != report["merged_behavior_flow"]:
                raise RuntimeError("canonical behavior-flow verification failed")
            report["remaining_record_count"] = len(fresh)
            report["applied"] = True
        write_json(snapshot_root / "migration-report.json", report)
        print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
