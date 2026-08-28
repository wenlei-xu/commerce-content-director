import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_scene_asset_table_is_registered():
    schema = json.loads((ROOT / "config" / "base-schema.json").read_text(encoding="utf-8"))
    scene = schema["tables"]["scene_assets"]

    assert scene["name"] == "场景资产库"
    assert scene["table_id"] == "tbl9qloJm1V5Yooa"
    assert scene["status_values"] == {"available": "可用", "disabled": "禁用"}
    assert scene["fields"]["anchor"] == "场景锚点"
    assert scene["fields"]["use_cases"] == "适用用途"
