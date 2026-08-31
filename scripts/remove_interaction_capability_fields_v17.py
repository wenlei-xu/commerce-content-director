#!/usr/bin/env python3
"""Remove the rejected capability-tag fields after a recoverable snapshot."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default=f"remove-interaction-capabilities-v17-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    try:
        api = Feishu()
        schema = config()
        app = schema["app_token"]
        product_table = schema["tables"]["products"]
        template_table = schema["tables"]["content_interaction_templates"]
        root = HERE.parent / "migration-backups" / args.run_id
        if root.exists():
            raise RuntimeError(f"backup already exists: {root}")
        root.mkdir(parents=True)
        product_fields = api.fields(app, product_table["table_id"])
        template_fields = api.fields(app, template_table["table_id"])
        write_json(root / "product-fields-before.json", product_fields)
        write_json(root / "template-fields-before.json", template_fields)
        targets = {
            "product": [field for field in product_fields if field["field_name"] == "交互能力标签"],
            "template": [field for field in template_fields if field["field_name"] == "所需交互能力"],
        }
        report = {
            "run_id": args.run_id,
            "targets": {key: [field["field_id"] for field in value] for key, value in targets.items()},
            "applied": False,
        }
        if args.apply:
            if args.confirm != "APPLY_REMOVE_INTERACTION_CAPABILITIES_V17":
                raise RuntimeError("--apply requires --confirm APPLY_REMOVE_INTERACTION_CAPABILITIES_V17")
            for field in targets["product"]:
                api.delete_field(app, product_table["table_id"], field["field_id"])
            for field in targets["template"]:
                api.delete_field(app, template_table["table_id"], field["field_id"])
            product_after = {field["field_name"] for field in api.fields(app, product_table["table_id"])}
            template_after = {field["field_name"] for field in api.fields(app, template_table["table_id"])}
            if "交互能力标签" in product_after or "所需交互能力" in template_after:
                raise RuntimeError("capability field deletion verification failed")
            write_json(root / "product-fields-after.json", sorted(product_after))
            write_json(root / "template-fields-after.json", sorted(template_after))
            report["applied"] = True
        write_json(root / "migration-report.json", report)
        print(json.dumps({"ok": True, **report}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
