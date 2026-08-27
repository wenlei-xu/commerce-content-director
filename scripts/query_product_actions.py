#!/usr/bin/env python3
"""Read confirmed product actions from the Feishu product action library.

This is a read-only adapter. Product hard facts remain authoritative in the
products table, and the caller owns writing the selected action into the
structured script.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from migrate_schema_v6 import Feishu, config, linked_ids, text  # noqa: E402


def attachment_refs(value: Any) -> list[dict[str, Any]]:
    """Return stable attachment metadata for optional action references."""
    if not isinstance(value, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or not item.get("file_token"):
            continue
        ref = {"file_token": str(item["file_token"])}
        for key in ("name", "type"):
            if item.get(key):
                ref[key] = str(item[key])
        refs.append(ref)
    return refs


def query_actions(api: Feishu, schema: dict[str, Any], product_record_id: str, *, include_unavailable: bool = False) -> dict[str, Any]:
    table = schema["tables"]["product_action_library"]
    records = api.records(schema["app_token"], table["table_id"])
    availability_field = table["availability_field"]
    active_value = table["availability_active"]
    fields = table["fields"]
    actions = []
    for record in records:
        values = record.get("fields", {})
        if product_record_id not in linked_ids(values.get(table["product_link_field"])):
            continue
        availability = text(values.get(availability_field))
        if not include_unavailable and availability != active_value:
            continue
        actions.append(
            {
                "record_id": record["record_id"],
                "product_record_id": product_record_id,
                "action": text(values.get(fields["action"])),
                "how_to": text(values.get(fields["how_to"])),
                "visual_focus": text(values.get(fields["visual_focus"])),
                "action_reference_images": attachment_refs(values.get(fields["action_reference_images"])),
                "related_benefit": text(values.get(fields["related_benefit"])),
                "availability": availability,
            }
        )
    return {
        "ok": True,
        "table_id": table["table_id"],
        "product_record_id": product_record_id,
        "include_unavailable": include_unavailable,
        "actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-record-id", required=True)
    parser.add_argument("--include-unavailable", action="store_true")
    args = parser.parse_args()
    result = query_actions(Feishu(), config(), args.product_record_id, include_unavailable=args.include_unavailable)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
