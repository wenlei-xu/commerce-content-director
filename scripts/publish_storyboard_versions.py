#!/usr/bin/env python3
"""Write exactly two complete A/B storyboard packages to the script table.

The source script is the only parent.  This writer never creates a
per-Segment candidate record and never exposes a Segment-level approval state.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from feishu_attachment_uploader import FeishuAttachmentUploader
from migrate_schema_v6 import Feishu


VERSIONS = ("A", "B")
RAW_SEGMENT_SECONDS = 10


def text(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(item for item in (text(entry) for entry in value) if item)
    if isinstance(value, dict):
        return text(value.get("text") or value.get("name") or value.get("value") or "")
    return "" if value is None else str(value)


def linked_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, dict):
            record_id = item.get("record_id")
            if record_id:
                result.append(str(record_id))
            result.extend(str(record_id) for record_id in item.get("record_ids", []) if record_id)
        elif item:
            result.append(str(item))
    return result


def attachment_tokens(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item.get("file_token") or item.get("token")) for item in value if isinstance(item, dict) and (item.get("file_token") or item.get("token"))]


def record_from_data(data: dict[str, Any]) -> dict[str, Any]:
    record = data.get("record")
    return record if isinstance(record, dict) else data


def record_id(data: dict[str, Any]) -> str:
    record = record_from_data(data)
    value = record.get("record_id") or record.get("id")
    if not value:
        raise RuntimeError(f"Feishu response contains no record ID: {data}")
    return str(value)


def get_record(api: Feishu, app: str, table: str, record_id_value: str) -> dict[str, Any]:
    return record_from_data(api.call("GET", f"/bitable/v1/apps/{app}/tables/{table}/records/{record_id_value}"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("storyboard writeback manifest must be an object")
    versions = value.get("versions")
    if not isinstance(versions, dict) or set(versions) != set(VERSIONS):
        raise ValueError("manifest.versions must contain exactly A and B")
    for version in VERSIONS:
        package = versions[version]
        if not isinstance(package, dict) or not isinstance(package.get("boards"), list):
            raise ValueError(f"manifest.versions.{version}.boards must be a list")
        if not package["boards"]:
            raise ValueError(f"manifest.versions.{version}.boards must not be empty")
        for board in package["boards"]:
            if not isinstance(board, dict) or not isinstance(board.get("segment_id"), str) or not isinstance(board.get("path"), str):
                raise ValueError(f"manifest.versions.{version}.boards entries require segment_id and path")
    return value


def validate_package(package: dict[str, Any], target_duration: int) -> list[tuple[str, Path, str]]:
    expected = target_duration // RAW_SEGMENT_SECONDS
    boards = package["boards"]
    if len(boards) != expected:
        raise ValueError(f"storyboard version requires {expected} boards, got {len(boards)}")
    result: list[tuple[str, Path, str]] = []
    for index, board in enumerate(boards, start=1):
        expected_segment = f"Segment-{index:02d}"
        if board["segment_id"] != expected_segment:
            raise ValueError(f"boards must be ordered and named {expected_segment}")
        path = Path(board["path"]).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = sha256(path)
        declared = board.get("sha256")
        if declared is not None and declared != digest:
            raise ValueError(f"{expected_segment} sha256 does not match {path}")
        result.append((expected_segment, path, digest))
    return result


def find_version_record(api: Feishu, app: str, table: str, fields: dict[str, str], source_id: str, version: str, source_script_id: str) -> dict[str, Any] | None:
    matches = []
    for record in api.records(app, table):
        values = record.get("fields", {})
        if source_id in linked_ids(values.get(fields["parent_script_link"])) and text(values.get(fields["script_version"])) == version:
            matches.append(record)
    # Repair the records produced by the old writer, which set A/B but left
    # 来源脚本 empty.  The deterministic script ID is only a recovery key;
    # the relation is always written and verified below.
    if not matches:
        legacy_id = f"{source_script_id}:{version}"
        for record in api.records(app, table):
            values = record.get("fields", {})
            if text(values.get(fields["script_id"])) == legacy_id and text(values.get(fields["script_version"])) == version:
                matches.append(record)
    if len(matches) > 1:
        raise RuntimeError(f"multiple script records found for source {source_id} version {version}")
    return matches[0] if matches else None


def build_version_fields(
    source: dict[str, Any],
    fields: dict[str, str],
    source_id: str,
    version: str,
    *,
    status: str = "生成中",
    review_notes: str = "",
) -> dict[str, Any]:
    source_fields = copy.deepcopy(source.get("fields", {}))
    attachment_field = fields["storyboard_attachments"]
    for key in (attachment_field, fields["storyboard_status"], fields.get("storyboard_review_notes", "")):
        if key:
            source_fields.pop(key, None)
    source_name = text(source_fields.get(fields["name"])) or source_id
    source_script_id = text(source_fields.get(fields["script_id"])) or source_id
    source_fields[fields["name"]] = f"{source_name}｜版本 {version}"
    source_fields[fields["script_id"]] = f"{source_script_id}:{version}"
    source_fields[fields["parent_script_link"]] = [source_id]
    if fields.get("parent_script_record_id"):
        source_fields[fields["parent_script_record_id"]] = source_id
    source_fields[fields["script_version"]] = version
    source_fields[fields["storyboard_status"]] = status
    if fields.get("storyboard_review_notes"):
        source_fields[fields["storyboard_review_notes"]] = review_notes
    source_fields[attachment_field] = []
    return source_fields


def write_versions(
    *,
    api: Feishu,
    uploader: FeishuAttachmentUploader,
    schema: dict[str, Any],
    source_script_record_id: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    app = schema["app_token"]
    table = schema["tables"]["scripts"]
    fields = table["fields"]
    source = get_record(api, app, table["table_id"], source_script_record_id)
    source_values = source.get("fields", {})
    if text(source_values.get(table["validation_status_field"])) != "通过":
        raise RuntimeError("source script must have 脚本检查状态=通过")
    if text(source_values.get(fields["script_version"])) in VERSIONS:
        raise RuntimeError("source_script_record_id must point to the unversioned source script, not an A/B version")
    duration_value = source_values.get(table["duration_field"])
    try:
        target_duration = int(float(duration_value))
    except (TypeError, ValueError) as error:
        raise RuntimeError("source script has an invalid target duration") from error
    if target_duration <= 0 or target_duration % RAW_SEGMENT_SECONDS:
        raise RuntimeError("source script target duration must be positive and divisible by 10")
    if manifest.get("source_script_record_id") and str(manifest["source_script_record_id"]) != source_script_record_id:
        raise ValueError("manifest source_script_record_id does not match the CLI source record")
    run_id = text(manifest.get("run_id"))
    if not run_id:
        raise ValueError("manifest.run_id is required")

    results: dict[str, Any] = {"source_script_record_id": source_script_record_id, "run_id": run_id, "versions": {}}
    for version in VERSIONS:
        package = manifest["versions"][version]
        boards = validate_package(package, target_duration)
        delta = text(package.get("variant_delta"))
        if not delta:
            raise ValueError(f"manifest.versions.{version}.variant_delta is required")
        notes = "run_id=" + run_id + "; variant_delta=" + delta + "; " + "; ".join(f"{segment}={digest}" for segment, _path, digest in boards)
        source_script_id = text(source_values.get(fields["script_id"])) or source_script_record_id
        existing = find_version_record(api, app, table["table_id"], fields, source_script_record_id, version, source_script_id)
        if existing:
            version_id = str(existing["record_id"])
            existing_status = text(existing.get("fields", {}).get(fields["storyboard_status"]))
            if existing_status == "已通过":
                raise RuntimeError(f"refusing to overwrite approved storyboard version {version_id}")
            api.update_record(app, table["table_id"], version_id, build_version_fields(source, fields, source_script_record_id, version, review_notes=notes))
        else:
            created = api.create_record(app, table["table_id"], build_version_fields(source, fields, source_script_record_id, version, review_notes=notes))
            version_id = record_id(created)
        tokens = uploader.upload_and_attach(app_token=app, table_id=table["table_id"], record_id=version_id, field=fields["storyboard_attachments"], files=[path for _segment, path, _digest in boards])
        api.update_record(app, table["table_id"], version_id, {fields["storyboard_status"]: "待审核", fields["storyboard_review_notes"]: notes})
        fresh = get_record(api, app, table["table_id"], version_id)
        fresh_values = fresh.get("fields", {})
        observed_parent = linked_ids(fresh_values.get(fields["parent_script_link"]))
        observed_tokens = attachment_tokens(fresh_values.get(fields["storyboard_attachments"]))
        if observed_parent != [source_script_record_id] or text(fresh_values.get(fields["script_version"])) != version or observed_tokens != tokens or text(fresh_values.get(fields["storyboard_status"])) != "待审核":
            raise RuntimeError(f"A/B version fresh-read verification failed for {version}")
        results["versions"][version] = {"record_id": version_id, "source_script_record_id": source_script_record_id, "attachment_tokens": observed_tokens, "board_hashes": [digest for _segment, _path, digest in boards], "status": "待审核"}
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--source-script-record-id", required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    schema = json.loads((Path(__file__).resolve().parents[1] / "config" / "base-schema.json").read_text(encoding="utf-8"))
    result = write_versions(api=Feishu(), uploader=FeishuAttachmentUploader.from_env(), schema=schema, source_script_record_id=args.source_script_record_id, manifest=load_manifest(args.manifest))
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
