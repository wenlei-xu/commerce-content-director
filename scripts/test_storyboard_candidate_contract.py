#!/usr/bin/env python3
"""Regression tests for Feishu storyboard candidate selection and finalization."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from PIL import Image

from storyboard_candidates import (
    finalize_candidates,
    publish_candidate,
    select_candidate,
)


def schema() -> dict[str, Any]:
    return {
        "app_token": "app-test",
        "tables": {
            "scripts": {
                "table_id": "scripts",
                "script_status_field": "脚本状态",
                "validation_status_field": "脚本检查状态",
                "duration_field": "目标时长（秒）",
                "fields": {
                    "storyboard_attachments": "最终分镜图",
                    "storyboard_status": "分镜状态",
                    "storyboard_review_notes": "分镜审核意见",
                    "video_prompt": "视频提示词",
                },
            },
            "storyboard_candidates": {
                "table_id": "candidates",
                "fields": {
                    "name": "候选名称",
                    "candidate_id": "候选ID",
                    "script_link": "脚本",
                    "segment_id": "Segment ID",
                    "segment_index": "Segment 序号",
                    "target_time_range": "目标时间范围",
                    "board_attachment": "候选四宫格",
                    "status": "候选状态",
                    "selected": "是否采用",
                    "attempt": "生成轮次",
                    "run_id": "Run ID",
                    "job_id": "Flow2API Job ID",
                    "idempotency_key": "幂等键",
                    "model_id": "模型ID",
                    "sha256": "附件SHA256",
                    "review_notes": "审核意见",
                },
            },
        },
    }


class FakeApi:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, dict[str, Any]]] = {
            "scripts": {},
            "candidates": {},
        }
        self.sequence = 0

    def add(self, table: str, record_id: str, fields: dict[str, Any]) -> None:
        self.tables[table][record_id] = {
            "record_id": record_id,
            "fields": copy.deepcopy(fields),
        }

    def call(self, method: str, path: str, **_kwargs: Any) -> dict[str, Any]:
        if method != "GET":
            raise AssertionError((method, path))
        pieces = path.split("/")
        table = pieces[-3]
        record_id = pieces[-1]
        return {"record": copy.deepcopy(self.tables[table][record_id])}

    def records(self, _app: str, table: str) -> list[dict[str, Any]]:
        return copy.deepcopy(list(self.tables[table].values()))

    def create_record(
        self, _app: str, table: str, fields: dict[str, Any]
    ) -> dict[str, Any]:
        self.sequence += 1
        record_id = f"new-{self.sequence}"
        self.add(table, record_id, fields)
        return {"record": copy.deepcopy(self.tables[table][record_id])}

    def update_record(
        self,
        _app: str,
        table: str,
        record_id: str,
        fields: dict[str, Any],
    ) -> None:
        self.tables[table][record_id]["fields"].update(copy.deepcopy(fields))


class FakeUploader:
    def __init__(self, api: FakeApi) -> None:
        self.api = api

    def upload_and_attach(
        self,
        *,
        table_id: str,
        record_id: str,
        field: str,
        files: list[Path],
        **_kwargs: Any,
    ) -> list[str]:
        tokens = [f"token-{path.name}" for path in files]
        self.api.tables[table_id][record_id]["fields"][field] = [
            {"file_token": token} for token in tokens
        ]
        return tokens

    def attach_tokens(
        self,
        *,
        table_id: str,
        record_id: str,
        field: str,
        file_tokens: list[str],
        **_kwargs: Any,
    ) -> None:
        self.api.tables[table_id][record_id]["fields"][field] = [
            {"file_token": token} for token in file_tokens
        ]


def executable_script() -> dict[str, Any]:
    return {
        "脚本状态": "已锁定",
        "脚本检查状态": "通过",
        "目标时长（秒）": 30,
        "最终分镜图": [],
        "分镜状态": "生成中",
        "分镜审核意见": "",
        "视频提示词": "approved prompt",
    }


def candidate(
    candidate_id: str,
    segment_index: int,
    token: str,
    *,
    selected: bool,
) -> dict[str, Any]:
    return {
        "候选名称": candidate_id,
        "候选ID": candidate_id,
        "脚本": [{"record_id": "script-1"}],
        "Segment ID": f"Segment-{segment_index:02d}",
        "Segment 序号": segment_index,
        "目标时间范围": f"{(segment_index - 1) * 10}-{segment_index * 10}s",
        "候选四宫格": [{"file_token": token}],
        "候选状态": "已采用" if selected else "待选择",
        "是否采用": selected,
        "生成轮次": 1,
    }


class StoryboardCandidateContractTests(unittest.TestCase):
    def test_checked_in_schema_declares_candidate_table_v13(self) -> None:
        checked_in = json.loads(
            (Path(__file__).resolve().parents[1] / "config" / "base-schema.json")
            .read_text(encoding="utf-8")
        )
        table = checked_in["tables"]["storyboard_candidates"]

        self.assertGreaterEqual(checked_in["schema_version"], 13)
        self.assertTrue(table["table_id"].startswith("tbl"))
        self.assertEqual(table["fields"]["board_attachment"], "候选四宫格")
        self.assertEqual(table["fields"]["selected"], "是否采用")

    def test_select_replaces_only_the_same_segment(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        api.add("candidates", "s1-a", candidate("s1-a", 1, "t1a", selected=False))
        api.add("candidates", "s1-b", candidate("s1-b", 1, "t1b", selected=True))
        api.add("candidates", "s2-a", candidate("s2-a", 2, "t2a", selected=True))

        result = select_candidate(
            api=api,
            schema=schema(),
            candidate_record_id="s1-a",
        )

        self.assertEqual(result["segment_id"], "Segment-01")
        self.assertTrue(api.tables["candidates"]["s1-a"]["fields"]["是否采用"])
        self.assertFalse(api.tables["candidates"]["s1-b"]["fields"]["是否采用"])
        self.assertTrue(api.tables["candidates"]["s2-a"]["fields"]["是否采用"])

    def test_finalize_orders_one_complete_board_per_segment(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        api.add("candidates", "s1-a", candidate("s1-a", 1, "token-1", selected=True))
        api.add("candidates", "s1-b", candidate("s1-b", 1, "reject-1", selected=False))
        api.add("candidates", "s2-a", candidate("s2-a", 2, "token-2", selected=True))
        api.add("candidates", "s3-a", candidate("s3-a", 3, "token-3", selected=True))
        uploader = FakeUploader(api)

        result = finalize_candidates(
            api=api,
            uploader=uploader,
            schema=schema(),
            script_record_id="script-1",
            approve=True,
        )

        self.assertEqual(result["expected_board_count"], 3)
        self.assertEqual(
            result["observed_attachment_tokens"],
            ["token-1", "token-2", "token-3"],
        )
        self.assertEqual(result["observed_status"], "已通过")
        self.assertEqual(
            api.tables["candidates"]["s1-b"]["fields"]["候选状态"],
            "已淘汰",
        )

    def test_finalize_rejects_ambiguous_segment_selection(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        api.add("candidates", "s1-a", candidate("s1-a", 1, "t1a", selected=True))
        api.add("candidates", "s1-b", candidate("s1-b", 1, "t1b", selected=True))
        api.add("candidates", "s2-a", candidate("s2-a", 2, "t2", selected=True))
        api.add("candidates", "s3-a", candidate("s3-a", 3, "t3", selected=True))

        with self.assertRaisesRegex(RuntimeError, "duplicates"):
            finalize_candidates(
                api=api,
                uploader=FakeUploader(api),
                schema=schema(),
                script_record_id="script-1",
                approve=False,
            )

    def test_checkbox_is_selection_authority_not_stale_status(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        stale = candidate("s1-old", 1, "old", selected=False)
        stale["候选状态"] = "已采用"
        api.add("candidates", "s1-old", stale)
        api.add("candidates", "s1-new", candidate("s1-new", 1, "new", selected=True))
        api.add("candidates", "s2", candidate("s2", 2, "token-2", selected=True))
        api.add("candidates", "s3", candidate("s3", 3, "token-3", selected=True))

        result = finalize_candidates(
            api=api,
            uploader=FakeUploader(api),
            schema=schema(),
            script_record_id="script-1",
            approve=False,
        )

        self.assertEqual(
            result["observed_attachment_tokens"],
            ["new", "token-2", "token-3"],
        )

    def test_finalize_rejects_a_missing_segment_selection(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        api.add("candidates", "s1", candidate("s1", 1, "token-1", selected=True))
        api.add("candidates", "s2", candidate("s2", 2, "token-2", selected=True))

        with self.assertRaisesRegex(RuntimeError, r"missing=\[3\]"):
            finalize_candidates(
                api=api,
                uploader=FakeUploader(api),
                schema=schema(),
                script_record_id="script-1",
                approve=False,
            )

    def test_publish_validates_and_persists_a_complete_board(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        uploader = FakeUploader(api)
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            board = root / "board.png"
            profile = root / "profile.json"
            Image.new("RGB", (1080, 1920), "white").save(board)
            profile.write_text(
                json.dumps(
                    {"storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"}}
                ),
                encoding="utf-8",
            )

            result = publish_candidate(
                api=api,
                uploader=uploader,
                schema=schema(),
                script_record_id="script-1",
                segment_index=2,
                attempt=3,
                run_id="run-1",
                job_id="job-3",
                idempotency_key="run-1:Segment-02:storyboard:3",
                model_id="image-model",
                board=board,
                profile=profile,
            )

        record = api.tables["candidates"][result["candidate_record_id"]]
        self.assertEqual(record["fields"]["Segment ID"], "Segment-02")
        self.assertEqual(record["fields"]["候选状态"], "待选择")
        self.assertEqual(
            record["fields"]["候选四宫格"],
            [{"file_token": "token-board.png"}],
        )

    def test_publish_rejects_a_non_deterministic_idempotency_key(self) -> None:
        api = FakeApi()
        api.add("scripts", "script-1", executable_script())
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            board = root / "board.png"
            profile = root / "profile.json"
            Image.new("RGB", (1080, 1920), "white").save(board)
            profile.write_text(
                json.dumps(
                    {"storyboard": {"columns": 2, "rows": 2, "panel_ratio": "9:16"}}
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "idempotency key mismatch"):
                publish_candidate(
                    api=api,
                    uploader=FakeUploader(api),
                    schema=schema(),
                    script_record_id="script-1",
                    segment_index=2,
                    attempt=3,
                    run_id="run-1",
                    job_id="job-3",
                    idempotency_key="wrong",
                    model_id="image-model",
                    board=board,
                    profile=profile,
                )


if __name__ == "__main__":
    unittest.main()
