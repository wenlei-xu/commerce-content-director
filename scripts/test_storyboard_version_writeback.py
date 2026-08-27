#!/usr/bin/env python3
"""Regression tests for the single A/B storyboard writeback seam."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from publish_storyboard_versions import build_version_fields, write_versions


def schema() -> dict[str, Any]:
    return {
        "app_token": "app-test",
        "tables": {
            "scripts": {
                "table_id": "scripts",
                "validation_status_field": "脚本检查状态",
                "duration_field": "目标时长（秒）",
                "fields": {
                    "name": "脚本名称", "script_id": "脚本ID", "parent_script_link": "来源脚本",
                    "parent_script_record_id": "父脚本记录ID", "storyboard_attachments": "最终分镜图",
                    "storyboard_status": "分镜状态", "storyboard_review_notes": "分镜审核意见",
                    "script_version": "脚本版本",
                },
            }
        },
    }


class FakeApi:
    def __init__(self) -> None:
        self.records_by_table: dict[str, dict[str, dict[str, Any]]] = {"scripts": {}}
        self.next_id = 0

    def add(self, record_id: str, fields: dict[str, Any]) -> None:
        self.records_by_table["scripts"][record_id] = {"record_id": record_id, "fields": copy.deepcopy(fields)}

    def call(self, method: str, path: str, **_kwargs: Any) -> dict[str, Any]:
        record_id = path.rstrip("/").split("/")[-1]
        return {"record": copy.deepcopy(self.records_by_table["scripts"][record_id])}

    def records(self, _app: str, _table: str) -> list[dict[str, Any]]:
        return copy.deepcopy(list(self.records_by_table["scripts"].values()))

    def create_record(self, _app: str, _table: str, fields: dict[str, Any]) -> dict[str, Any]:
        self.next_id += 1
        record_id = f"version-{self.next_id}"
        self.add(record_id, fields)
        return {"record": copy.deepcopy(self.records_by_table["scripts"][record_id])}

    def update_record(self, _app: str, _table: str, record_id: str, fields: dict[str, Any]) -> None:
        self.records_by_table["scripts"][record_id]["fields"].update(copy.deepcopy(fields))


class FakeUploader:
    def __init__(self, api: FakeApi) -> None:
        self.api = api

    def upload_and_attach(self, *, table_id: str, record_id: str, field: str, files: list[Path], **_kwargs: Any) -> list[str]:
        tokens = [f"token-{path.name}" for path in files]
        self.api.records_by_table[table_id][record_id]["fields"][field] = [{"file_token": token} for token in tokens]
        return tokens


class StoryboardVersionWritebackTests(unittest.TestCase):
    def test_build_fields_uses_real_parent_relation(self) -> None:
        source = {"fields": {"脚本名称": "源脚本", "脚本ID": "SCRIPT-1", "脚本检查状态": "通过", "目标时长（秒）": 20}}
        fields = build_version_fields(source, schema()["tables"]["scripts"]["fields"], "rec-source", "A")
        self.assertEqual(fields["来源脚本"], ["rec-source"])
        self.assertEqual(fields["父脚本记录ID"], "rec-source")
        self.assertEqual(fields["脚本版本"], "A")
        self.assertEqual(fields["脚本ID"], "SCRIPT-1:A")

    def test_write_versions_creates_exactly_two_linked_records(self) -> None:
        api = FakeApi()
        api.add("rec-source", {"脚本名称": "源脚本", "脚本ID": "SCRIPT-1", "脚本检查状态": "通过", "目标时长（秒）": 20})
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = []
            for index in range(1, 3):
                path = root / f"Segment-{index:02d}.png"
                Image.new("RGB", (18, 32), "white").save(path)
                paths.append(path)
            manifest = {"run_id": "run-1", "source_script_record_id": "rec-source", "versions": {version: {"variant_delta": f"{version} delta", "boards": [{"segment_id": f"Segment-{index:02d}", "path": str(paths[index - 1])} for index in range(1, 3)]} for version in ("A", "B")}}
            result = write_versions(api=api, uploader=FakeUploader(api), schema=schema(), source_script_record_id="rec-source", manifest=manifest)
        self.assertEqual(set(result["versions"]), {"A", "B"})
        self.assertEqual(len(api.records_by_table["scripts"]), 3)
        for record_id, record in api.records_by_table["scripts"].items():
            if record_id == "rec-source":
                continue
            self.assertEqual(record["fields"]["来源脚本"], ["rec-source"])
            self.assertIn(record["fields"]["脚本版本"], ("A", "B"))
            self.assertEqual(record["fields"]["分镜状态"], "待审核")
            self.assertEqual(len(record["fields"]["最终分镜图"]), 2)


if __name__ == "__main__":
    unittest.main()
