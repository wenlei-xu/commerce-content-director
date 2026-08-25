#!/usr/bin/env python3
"""Publish, select, and finalize Feishu storyboard-board candidates.

One candidate record owns one complete 2x2 board for one configured 10-second
target production Segment. Multiple candidates may exist for a Segment, but
exactly one accepted candidate per Segment is required before the script's
``最终分镜图`` field can be finalized.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from feishu_attachment_uploader import FeishuAttachmentUploader
from migrate_schema_v6 import Feishu
from validate_generation_storyboards import load_profile, validate_image


SKILL = Path(__file__).resolve().parent.parent
RAW_SEGMENT_SECONDS = 10
PENDING_STATUS = "待选择"
STAGING_STATUS = "提交中"
ACCEPTED_STATUS = "已采用"
REJECTED_STATUS = "已淘汰"


def load_schema() -> dict[str, Any]:
    return json.loads(
        (SKILL / "config" / "base-schema.json").read_text(encoding="utf-8")
    )


def plain_text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(filter(None, (plain_text(item) for item in value)))
    if isinstance(value, dict):
        return plain_text(
            value.get("text")
            or value.get("name")
            or value.get("value")
            or ""
        )
    return "" if value is None else str(value)


def linked_record_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            record_id = item.get("record_id")
            if record_id:
                result.append(str(record_id))
            result.extend(str(entry) for entry in item.get("record_ids", []) if entry)
        elif item:
            result.append(str(item))
    return result


def attachment_tokens(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            token = item.get("file_token") or item.get("token")
            if token:
                result.append(str(token))
    return result


def checkbox_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "是"}
    return False


def numeric(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    try:
        number = int(float(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be an integer") from error
    return number


def record_from_data(data: dict[str, Any]) -> dict[str, Any]:
    record = data.get("record")
    return record if isinstance(record, dict) else data


def record_id_from_data(data: dict[str, Any]) -> str:
    record = record_from_data(data)
    record_id = record.get("record_id") or record.get("id")
    if not record_id:
        raise RuntimeError(f"Feishu record response contains no record ID: {data}")
    return str(record_id)


def get_record(
    api: Feishu, app: str, table: str, record_id: str
) -> dict[str, Any]:
    data = api.call(
        "GET", f"/bitable/v1/apps/{app}/tables/{table}/records/{record_id}"
    )
    return record_from_data(data)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def deterministic_candidate_id(
    script_record_id: str, segment_index: int, attempt: int
) -> str:
    return f"{script_record_id}:Segment-{segment_index:02d}:attempt-{attempt:02d}"


def target_segment_id(segment_index: int) -> str:
    return f"Segment-{segment_index:02d}"


def target_time_range(segment_index: int) -> str:
    start = (segment_index - 1) * RAW_SEGMENT_SECONDS
    end = segment_index * RAW_SEGMENT_SECONDS
    return f"{start}-{end}s"


def schema_tables(schema: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        return schema["tables"]["scripts"], schema["tables"]["storyboard_candidates"]
    except KeyError as error:
        raise RuntimeError(
            "base-schema.json is missing the storyboard_candidates table mapping"
        ) from error


def candidate_fields(schema: dict[str, Any]) -> dict[str, str]:
    _scripts, candidates = schema_tables(schema)
    return candidates["fields"]


def all_candidates_for_script(
    api: Feishu,
    app: str,
    candidate_table: dict[str, Any],
    script_record_id: str,
) -> list[dict[str, Any]]:
    fields = candidate_table["fields"]
    link_field = fields["script_link"]
    return [
        record
        for record in api.records(app, candidate_table["table_id"])
        if script_record_id
        in linked_record_ids(record.get("fields", {}).get(link_field))
    ]


def require_executable_script(
    script: dict[str, Any], scripts_table: dict[str, Any]
) -> int:
    fields = script.get("fields", {})
    if plain_text(fields.get(scripts_table["script_status_field"])) != "已锁定":
        raise RuntimeError("storyboard candidates require 脚本状态=已锁定")
    if plain_text(fields.get(scripts_table["validation_status_field"])) != "通过":
        raise RuntimeError("storyboard candidates require 脚本检查状态=通过")
    duration = numeric(fields.get(scripts_table["duration_field"]), "目标时长（秒）")
    if duration <= 0 or duration % RAW_SEGMENT_SECONDS:
        raise RuntimeError("目标时长（秒） must be positive and divisible by 10")
    return duration


def selected_candidate(record: dict[str, Any], fields: dict[str, str]) -> bool:
    values = record.get("fields", {})
    return checkbox_true(values.get(fields["selected"]))


def publish_candidate(
    *,
    api: Feishu,
    uploader: FeishuAttachmentUploader,
    schema: dict[str, Any],
    script_record_id: str,
    segment_index: int,
    attempt: int,
    run_id: str,
    job_id: str,
    idempotency_key: str,
    model_id: str,
    board: Path,
    profile: Path,
) -> dict[str, Any]:
    scripts_table, candidate_table = schema_tables(schema)
    app = schema["app_token"]
    script = get_record(api, app, scripts_table["table_id"], script_record_id)
    duration = require_executable_script(script, scripts_table)
    expected_segments = duration // RAW_SEGMENT_SECONDS
    if segment_index < 1 or segment_index > expected_segments:
        raise RuntimeError(
            f"Segment index {segment_index} is outside 1..{expected_segments}"
        )
    if attempt < 1:
        raise RuntimeError("attempt must be positive")
    expected_idempotency_key = (
        f"{run_id}:{target_segment_id(segment_index)}:storyboard:{attempt}"
    )
    if idempotency_key != expected_idempotency_key:
        raise RuntimeError(
            "idempotency key mismatch: "
            f"expected {expected_idempotency_key}, got {idempotency_key}"
        )
    if not run_id or not job_id or not model_id:
        raise RuntimeError("run ID, Flow2API Job ID and model ID are required")
    if not board.is_file():
        raise FileNotFoundError(board)
    columns, rows, panel_ratio = load_profile(profile)
    validate_image(board, columns, rows, panel_ratio)

    fields = candidate_table["fields"]
    candidate_id = deterministic_candidate_id(
        script_record_id, segment_index, attempt
    )
    existing = [
        record
        for record in all_candidates_for_script(
            api, app, candidate_table, script_record_id
        )
        if plain_text(record.get("fields", {}).get(fields["candidate_id"]))
        == candidate_id
    ]
    if len(existing) > 1:
        raise RuntimeError(f"duplicate storyboard candidate ID: {candidate_id}")

    digest = sha256(board)
    if existing:
        record_id = str(existing[0]["record_id"])
        existing_fields = existing[0].get("fields", {})
        existing_digest = plain_text(existing_fields.get(fields["sha256"]))
        tokens = attachment_tokens(existing_fields.get(fields["board_attachment"]))
        if tokens and existing_digest == digest:
            if plain_text(existing_fields.get(fields["status"])) != PENDING_STATUS:
                api.update_record(
                    app,
                    candidate_table["table_id"],
                    record_id,
                    {fields["status"]: PENDING_STATUS},
                )
                fresh = get_record(
                    api, app, candidate_table["table_id"], record_id
                )
                if plain_text(
                    fresh.get("fields", {}).get(fields["status"])
                ) != PENDING_STATUS:
                    raise RuntimeError(
                        "candidate status resume verification failed"
                    )
            return {
                "candidate_record_id": record_id,
                "candidate_id": candidate_id,
                "segment_id": target_segment_id(segment_index),
                "attempt": attempt,
                "file_tokens": tokens,
                "idempotent": True,
            }
        if existing_digest and existing_digest != digest:
            raise RuntimeError(
                f"candidate {candidate_id} already exists with a different board hash"
            )
    else:
        create_fields = {
            fields["name"]: f"{target_segment_id(segment_index)} / 候选 {attempt:02d}",
            fields["candidate_id"]: candidate_id,
            fields["script_link"]: [script_record_id],
            fields["segment_id"]: target_segment_id(segment_index),
            fields["segment_index"]: segment_index,
            fields["target_time_range"]: target_time_range(segment_index),
            fields["status"]: STAGING_STATUS,
            fields["selected"]: False,
            fields["attempt"]: attempt,
            fields["run_id"]: run_id,
            fields["job_id"]: job_id,
            fields["idempotency_key"]: idempotency_key,
            fields["model_id"]: model_id,
            fields["sha256"]: digest,
        }
        created = api.create_record(
            app, candidate_table["table_id"], create_fields
        )
        record_id = record_id_from_data(created)

    tokens = uploader.upload_and_attach(
        app_token=app,
        table_id=candidate_table["table_id"],
        record_id=record_id,
        field=fields["board_attachment"],
        files=[board],
    )
    api.update_record(
        app,
        candidate_table["table_id"],
        record_id,
        {fields["status"]: PENDING_STATUS, fields["sha256"]: digest},
    )
    fresh = get_record(api, app, candidate_table["table_id"], record_id)
    fresh_fields = fresh.get("fields", {})
    observed = attachment_tokens(fresh_fields.get(fields["board_attachment"]))
    if observed != tokens:
        raise RuntimeError(
            f"candidate attachment fresh-read mismatch: expected {tokens}, got {observed}"
        )
    if plain_text(fresh_fields.get(fields["status"])) != PENDING_STATUS:
        raise RuntimeError("candidate status fresh-read verification failed")
    return {
        "candidate_record_id": record_id,
        "candidate_id": candidate_id,
        "segment_id": target_segment_id(segment_index),
        "attempt": attempt,
        "file_tokens": tokens,
        "sha256": digest,
        "idempotent": False,
    }


def select_candidate(
    *,
    api: Feishu,
    schema: dict[str, Any],
    candidate_record_id: str,
) -> dict[str, Any]:
    _scripts_table, candidate_table = schema_tables(schema)
    app = schema["app_token"]
    fields = candidate_table["fields"]
    chosen = get_record(api, app, candidate_table["table_id"], candidate_record_id)
    values = chosen.get("fields", {})
    script_ids = linked_record_ids(values.get(fields["script_link"]))
    if len(script_ids) != 1:
        raise RuntimeError("candidate must link to exactly one script")
    segment_id = plain_text(values.get(fields["segment_id"]))
    if not segment_id:
        raise RuntimeError("candidate is missing Segment ID")
    if len(attachment_tokens(values.get(fields["board_attachment"]))) != 1:
        raise RuntimeError("candidate must have exactly one complete 2x2 board")

    candidates = all_candidates_for_script(
        api, app, candidate_table, script_ids[0]
    )
    for record in candidates:
        record_fields = record.get("fields", {})
        if plain_text(record_fields.get(fields["segment_id"])) != segment_id:
            continue
        record_id = str(record["record_id"])
        if record_id == candidate_record_id:
            updates = {fields["selected"]: True, fields["status"]: ACCEPTED_STATUS}
        elif selected_candidate(record, fields):
            updates = {fields["selected"]: False, fields["status"]: PENDING_STATUS}
        else:
            continue
        api.update_record(app, candidate_table["table_id"], record_id, updates)

    fresh = all_candidates_for_script(api, app, candidate_table, script_ids[0])
    selected = [
        record
        for record in fresh
        if plain_text(record.get("fields", {}).get(fields["segment_id"]))
        == segment_id
        and selected_candidate(record, fields)
    ]
    if [record["record_id"] for record in selected] != [candidate_record_id]:
        raise RuntimeError("candidate selection fresh-read verification failed")
    return {
        "script_record_id": script_ids[0],
        "segment_id": segment_id,
        "selected_candidate_record_id": candidate_record_id,
    }


def finalize_candidates(
    *,
    api: Feishu,
    uploader: FeishuAttachmentUploader,
    schema: dict[str, Any],
    script_record_id: str,
    approve: bool,
    video_prompt: str | None = None,
) -> dict[str, Any]:
    scripts_table, candidate_table = schema_tables(schema)
    app = schema["app_token"]
    script = get_record(api, app, scripts_table["table_id"], script_record_id)
    duration = require_executable_script(script, scripts_table)
    expected_count = duration // RAW_SEGMENT_SECONDS
    fields = candidate_table["fields"]
    candidates = all_candidates_for_script(
        api, app, candidate_table, script_record_id
    )
    selected = [record for record in candidates if selected_candidate(record, fields)]
    by_index: dict[int, list[dict[str, Any]]] = {}
    for record in selected:
        index = numeric(
            record.get("fields", {}).get(fields["segment_index"]),
            "Segment 序号",
        )
        by_index.setdefault(index, []).append(record)

    missing = [index for index in range(1, expected_count + 1) if index not in by_index]
    duplicates = {
        index: [str(item["record_id"]) for item in records]
        for index, records in by_index.items()
        if len(records) != 1
    }
    unexpected = sorted(index for index in by_index if index < 1 or index > expected_count)
    if missing or duplicates or unexpected:
        raise RuntimeError(
            "storyboard selection incomplete or ambiguous: "
            f"missing={missing}, duplicates={duplicates}, unexpected={unexpected}"
        )

    ordered = [by_index[index][0] for index in range(1, expected_count + 1)]
    tokens: list[str] = []
    candidate_ids: list[str] = []
    for index, record in enumerate(ordered, start=1):
        record_fields = record.get("fields", {})
        expected_segment = target_segment_id(index)
        observed_segment = plain_text(record_fields.get(fields["segment_id"]))
        if observed_segment != expected_segment:
            raise RuntimeError(
                f"Segment identity mismatch at {index}: {observed_segment}"
            )
        board_tokens = attachment_tokens(
            record_fields.get(fields["board_attachment"])
        )
        if len(board_tokens) != 1:
            raise RuntimeError(
                f"{expected_segment} selected candidate must have exactly one board"
            )
        tokens.extend(board_tokens)
        candidate_ids.append(plain_text(record_fields.get(fields["candidate_id"])))

    script_fields = script.get("fields", {})
    script_field_names = scripts_table["fields"]
    current_tokens = attachment_tokens(
        script_fields.get(script_field_names["storyboard_attachments"])
    )
    current_status = plain_text(
        script_fields.get(script_field_names["storyboard_status"])
    )
    if current_status == "已通过" and current_tokens != tokens:
        raise RuntimeError("refusing to overwrite an already accepted storyboard")

    prompt = video_prompt or plain_text(
        script_fields.get(script_field_names["video_prompt"])
    )
    if approve and not prompt:
        raise RuntimeError("approval requires a non-empty 视频提示词")

    if current_tokens != tokens:
        uploader.attach_tokens(
            app_token=app,
            table_id=scripts_table["table_id"],
            record_id=script_record_id,
            field=script_field_names["storyboard_attachments"],
            file_tokens=tokens,
        )

    notes = "\n".join(
        f"{target_segment_id(index)}={candidate_id}"
        for index, candidate_id in enumerate(candidate_ids, start=1)
    )
    updates: dict[str, Any] = {
        script_field_names["storyboard_status"]: "已通过" if approve else "待审核",
        script_field_names["storyboard_review_notes"]: notes,
    }
    if video_prompt is not None:
        updates[script_field_names["video_prompt"]] = video_prompt
    api.update_record(app, scripts_table["table_id"], script_record_id, updates)

    selected_record_ids = {str(record["record_id"]) for record in ordered}
    for record in candidates:
        record_id = str(record["record_id"])
        update = (
            {fields["selected"]: True, fields["status"]: ACCEPTED_STATUS}
            if record_id in selected_record_ids
            else {fields["selected"]: False, fields["status"]: REJECTED_STATUS}
        )
        api.update_record(app, candidate_table["table_id"], record_id, update)

    fresh_script = get_record(api, app, scripts_table["table_id"], script_record_id)
    fresh_fields = fresh_script.get("fields", {})
    observed_tokens = attachment_tokens(
        fresh_fields.get(script_field_names["storyboard_attachments"])
    )
    expected_status = "已通过" if approve else "待审核"
    observed_status = plain_text(
        fresh_fields.get(script_field_names["storyboard_status"])
    )
    if observed_tokens != tokens or observed_status != expected_status:
        raise RuntimeError(
            "script storyboard fresh-read verification failed: "
            f"tokens={observed_tokens}, status={observed_status}"
        )
    return {
        "script_record_id": script_record_id,
        "target_duration_seconds": duration,
        "expected_board_count": expected_count,
        "selected_candidate_ids": candidate_ids,
        "observed_attachment_tokens": observed_tokens,
        "observed_status": observed_status,
    }


def write_output(path: Path | None, value: dict[str, Any]) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    print(json.dumps(value, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    publish = subparsers.add_parser("publish", help="publish one complete board candidate")
    publish.add_argument("--script-record-id", required=True)
    publish.add_argument("--segment-index", required=True, type=int)
    publish.add_argument("--attempt", required=True, type=int)
    publish.add_argument("--run-id", required=True)
    publish.add_argument("--job-id", required=True)
    publish.add_argument("--idempotency-key", required=True)
    publish.add_argument("--model-id", required=True)
    publish.add_argument("--board", required=True, type=Path)
    publish.add_argument("--profile", required=True, type=Path)
    publish.add_argument("--out", type=Path)

    select = subparsers.add_parser("select", help="select one candidate for its Segment")
    select.add_argument("--candidate-record-id", required=True)
    select.add_argument("--out", type=Path)

    finalize = subparsers.add_parser(
        "finalize", help="write one selected board per Segment back to the script"
    )
    finalize.add_argument("--script-record-id", required=True)
    finalize.add_argument("--approve", action="store_true")
    finalize.add_argument("--video-prompt-file", type=Path)
    finalize.add_argument("--out", type=Path)

    args = parser.parse_args()
    schema = load_schema()
    api = Feishu()
    uploader = FeishuAttachmentUploader.from_env()
    if args.command == "publish":
        result = publish_candidate(
            api=api,
            uploader=uploader,
            schema=schema,
            script_record_id=args.script_record_id,
            segment_index=args.segment_index,
            attempt=args.attempt,
            run_id=args.run_id,
            job_id=args.job_id,
            idempotency_key=args.idempotency_key,
            model_id=args.model_id,
            board=args.board.resolve(),
            profile=args.profile.resolve(),
        )
    elif args.command == "select":
        result = select_candidate(
            api=api,
            schema=schema,
            candidate_record_id=args.candidate_record_id,
        )
    else:
        video_prompt = None
        if args.video_prompt_file:
            video_prompt = args.video_prompt_file.read_text(encoding="utf-8").strip()
        result = finalize_candidates(
            api=api,
            uploader=uploader,
            schema=schema,
            script_record_id=args.script_record_id,
            approve=args.approve,
            video_prompt=video_prompt,
        )
    write_output(args.out, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
