from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from migrate_subject_assets_status_v18 import find_beagle, normalized_status_options  # noqa: E402


def test_status_options_rename_legacy_stop_to_disabled() -> None:
    options, changed = normalized_status_options(
        {
            "type": 3,
            "property": {
                "options": [
                    {"id": "available", "name": "可用", "color": 0},
                    {"id": "stopped", "name": "停用", "color": 1},
                ]
            },
        }
    )

    assert changed is True
    assert [option["name"] for option in options] == ["可用", "禁用"]
    assert options[1]["id"] == "stopped"


def test_find_beagle_requires_one_unique_dog() -> None:
    records = [
        {"record_id": "beagle", "fields": {"主体类型": "狗", "品种": "比格犬"}},
        {"record_id": "golden", "fields": {"主体类型": "狗", "品种": "金毛寻回犬"}},
    ]

    assert find_beagle(records, None)["record_id"] == "beagle"
