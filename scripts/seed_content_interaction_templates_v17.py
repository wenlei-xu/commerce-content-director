#!/usr/bin/env python3
"""Seed reviewed cross-SKU interaction templates and explicit product constraints."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from migrate_schema_v6 import Feishu, config, text  # noqa: E402


PRODUCT_SEED: dict[str, dict[str, Any]] = {
    "榴莲漏食玩具": {
        "constraints": "顶部织带用于手持和短暂轻拉；狗狗咬榴莲主体。底部开口用于装填食物，保持一体结构，不把织带画成弹力绳，不把侧面当成入口。",
    },
    "菠萝漏食玩具": {
        "constraints": "保持一体式菠萝结构；食物从倒置后的底部圆孔装入，侧面格栅不作装粮入口。当前确认可闻、扒、咬和推动，不展示拆件或侧孔出粮。",
    },
}

TEMPLATES = [
    {
        "name": "地面探索取食",
        "functions": ["兴趣", "互动", "情绪"],
        "flow": "主人把产品放到地面安全区域，镜头保持低位近距离；狗狗先主动接近闻嗅，再用鼻子或前爪连续扒动、推动，期间可短暂咬触并继续探索或取食。",
        "acceptance": "接近、闻嗅、扒动/推动的顺序清楚，至少一次完整行为链可见；产品接触点、移动方向、朝向和一体结构保持可辨。",
    },
    {
        "name": "引逗够取",
        "functions": ["兴趣", "互动", "情绪"],
        "flow": "主人第一人称视角从狗狗上方观察，手持产品在狗狗头顶上方逐步抬高并左右轻引，保持安全距离；狗狗连续2–3次自然起跳尝试，最后一次够到或短暂接触，主人随即降低产品结束互动。",
        "acceptance": "主人第一人称俯视视角稳定，手和产品位于画面上方；高度变化明显，至少2次完整起跳、落地和再次起跳清楚可见，最后一次接触明确；不得拍成单次站立抬头或把产品直接塞到嘴边。",
    },
    {
        "name": "追逐叼回",
        "functions": ["兴趣", "互动", "节奏"],
        "flow": "主人从狗狗前侧高位将产品抛向较远的安全区域，形成明显抛物线；狗狗立即快速起跑，沿路径跑到落点后叼起，再带回或回头寻找主人。",
        "acceptance": "抛出高度、前进距离、狗狗快速起跑和持续追逐路径清楚；落点处的叼取接触明确，产品结构在落地和叼取后仍可辨认；不得拍成近距离掉落或原地接住。",
    },
    {
        "name": "短暂拉扯",
        "functions": ["互动", "情绪", "节奏"],
        "flow": "主人和狗狗分别握住或咬住已确认的接触区域，先建立轻微张力，连续1–2次短促、轻柔、有人在场的拉扯后主动放松。",
        "acceptance": "双方接触点、受力方向、短拉次数和放松结果全程可见；产品连接关系保持清楚，不把织带拍成弹力绳或用遮挡掩盖结构。",
    },
]


def records_by_field(records: list[dict[str, Any]], field_name: str) -> dict[str, dict[str, Any]]:
    return {text(item.get("fields", {}).get(field_name)): item for item in records if text(item.get("fields", {}).get(field_name))}


def main() -> int:
    api = Feishu()
    schema = config()
    app = schema["app_token"]
    products_table = schema["tables"]["products"]
    templates_table = schema["tables"]["content_interaction_templates"]
    products = api.records(app, products_table["table_id"])
    templates = api.records(app, templates_table["table_id"])
    product_by_name = records_by_field(products, products_table["fields"]["name"])
    template_by_name = records_by_field(templates, templates_table["fields"]["template_name"])

    updated_products: list[str] = []
    for name, seed in PRODUCT_SEED.items():
        product = product_by_name.get(name)
        if not product:
            raise RuntimeError(f"product not found: {name}")
        api.update_record(
            app,
            products_table["table_id"],
            product["record_id"],
            {
                products_table["fields"]["interaction_constraints"]: seed["constraints"],
            },
        )
        updated_products.append(name)

    created_templates: list[str] = []
    updated_templates: list[str] = []
    template_fields = templates_table["fields"]
    for seed in TEMPLATES:
        fields = {
            template_fields["template_name"]: seed["name"],
            template_fields["content_function"]: seed["functions"],
            template_fields["behavior_flow"]: seed["flow"],
            template_fields["visual_acceptance"]: seed["acceptance"],
            templates_table["availability_field"]: templates_table["availability_active"],
        }
        existing = template_by_name.get(seed["name"])
        if existing:
            api.update_record(app, templates_table["table_id"], existing["record_id"], fields)
            updated_templates.append(seed["name"])
        else:
            api.create_record(app, templates_table["table_id"], fields)
            created_templates.append(seed["name"])

    fresh_products = api.records(app, products_table["table_id"])
    fresh_templates = api.records(app, templates_table["table_id"])
    fresh_product_by_name = records_by_field(fresh_products, products_table["fields"]["name"])
    fresh_template_by_name = records_by_field(fresh_templates, templates_table["fields"]["template_name"])
    for name, seed in PRODUCT_SEED.items():
        actual = fresh_product_by_name[name].get("fields", {})
        if text(actual.get(products_table["fields"]["interaction_constraints"])) != seed["constraints"]:
            raise RuntimeError(f"product interaction-constraint verification failed: {name}")
    for seed in TEMPLATES:
        actual = fresh_template_by_name[seed["name"]].get("fields", {})
        if text(actual.get(templates_table["availability_field"])) != templates_table["availability_active"]:
            raise RuntimeError(f"template status verification failed: {seed['name']}")
    print(json.dumps({
        "ok": True,
        "updated_products": updated_products,
        "created_templates": created_templates,
        "updated_templates": updated_templates,
        "fresh_read": {
            "product_count": len(fresh_products),
            "template_count": len(fresh_templates),
        },
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
