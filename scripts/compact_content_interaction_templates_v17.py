#!/usr/bin/env python3
"""Remove non-core fields from the Feishu interaction-template table.

The table is snapshotted before deletion.  Only the six approved runtime
fields remain; historical values are recoverable from the snapshot.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from feishu_api import Feishu, config, write_json  # noqa: E402

CORE_FIELDS = {"互动模板", "内容功能", "行为流程", "可视验收点", "模板状态"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"compact-interaction-templates-v17-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        api = Feishu()
        schema = config()
        app = schema["app_token"]
        table = schema["tables"]["content_interaction_templates"]
        fields_before = api.fields(app, table["table_id"])
        records_before = api.records(app, table["table_id"])
        root = HERE.parent / "migration-backups" / args.run_id
        if root.exists():
            raise RuntimeError(f"backup already exists: {root}")
        root.mkdir(parents=True)
        write_json(root / "fields-before.json", fields_before)
        write_json(root / "records-before.json", records_before)
        names_before = {field["field_name"] for field in fields_before}
        missing = sorted(CORE_FIELDS - names_before)
        if missing:
            raise RuntimeError(f"core fields missing: {missing}")
        removable = [field for field in fields_before if field["field_name"] not in CORE_FIELDS and not field.get("is_primary")]
        report = {
            "run_id": args.run_id,
            "table_id": table["table_id"],
            "core_fields": sorted(CORE_FIELDS),
            "removable_fields": [field["field_name"] for field in removable],
            "legacy_record_count": len(records_before),
            "applied": False,
        }
        if args.apply:
            if args.confirm != "APPLY_COMPACT_INTERACTION_TEMPLATES_V17":
                raise RuntimeError("--apply requires --confirm APPLY_COMPACT_INTERACTION_TEMPLATES_V17")
            for field in removable:
                api.delete_field(app, table["table_id"], field["field_id"])
            fields_after = api.fields(app, table["table_id"])
            names_after = {field["field_name"] for field in fields_after}
            if names_after != CORE_FIELDS:
                raise RuntimeError(f"field verification failed; remaining fields: {sorted(names_after)}")
            write_json(root / "fields-after.json", fields_after)
            report["applied"] = True
        write_json(root / "migration-report.json", report)
        print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
