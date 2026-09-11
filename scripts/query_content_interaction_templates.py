#!/usr/bin/env python3
"""Return cross-SKU interaction templates eligible for one confirmed product.

This is a read-only adapter.  A product supplies confirmed interaction
capabilities; a template supplies a reusable content pattern. Compatibility is
reviewed by the script workflow against the current product record.
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

from feishu_api import Feishu, config, text  # noqa: E402


def values(value: Any) -> list[str]:
    """Normalize Feishu multi-select values without treating free text as tags."""
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            candidate = item.get("name") or item.get("text")
        else:
            candidate = item
        candidate = str(candidate or "").strip()
        if candidate and candidate not in result:
            result.append(candidate)
    return result


def template_record(record: dict[str, Any], fields: dict[str, str]) -> dict[str, Any]:
    source = record.get("fields", {})
    return {
        "record_id": record["record_id"],
        "template_name": text(source.get(fields["template_name"])),
        "content_function": values(source.get(fields["content_function"])),
        "behavior_flow": text(source.get(fields["behavior_flow"])),
        "visual_acceptance": text(source.get(fields["visual_acceptance"])),
    }


def query_templates(
    api: Any,
    schema: dict[str, Any],
    product_record_id: str,
    *,
    include_ineligible: bool = False,
) -> dict[str, Any]:
    product_table = schema["tables"]["products"]
    product = next(
        (record for record in api.records(schema["app_token"], product_table["table_id"]) if record["record_id"] == product_record_id),
        None,
    )
    if not product:
        raise ValueError(f"product record not found: {product_record_id}")
    product_fields = product.get("fields", {})
    if text(product_fields.get(product_table["status_field"])) != product_table["status_active"]:
        raise ValueError(f"product is not available: {product_record_id}")

    product_field_names = product_table["fields"]
    template_table = schema["tables"]["content_interaction_templates"]
    template_fields = template_table["fields"]
    candidates = []
    for record in api.records(schema["app_token"], template_table["table_id"]):
        if text(record.get("fields", {}).get(template_table["availability_field"])) != template_table["availability_active"]:
            continue
        candidates.append(template_record(record, template_fields))
    return {
        "ok": True,
        "product_record_id": product_record_id,
        "interaction_capabilities": text(product_fields.get(product_field_names["interaction_capabilities"])),
        "templates": candidates,
        "template_count": len(candidates),
        "include_ineligible": include_ineligible,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product-record-id", required=True)
    parser.add_argument("--include-ineligible", action="store_true")
    args = parser.parse_args()
    result = query_templates(
        Feishu(), config(), args.product_record_id, include_ineligible=args.include_ineligible
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
