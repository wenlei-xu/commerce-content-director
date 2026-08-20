"""Copy the scraped TikTok material records and attachments into the configured Base."""

import importlib.util
import json
import mimetypes
import tempfile
from pathlib import Path

import requests


API_ROOT = "https://open.feishu.cn/open-apis"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "config" / "base-schema.json"
INGESTION_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))["tables"]["tiktok_ingestion"]
SOURCE_APP = INGESTION_SCHEMA["source_app_token"]
SOURCE_TABLE = INGESTION_SCHEMA["source_table_id"]
TARGET_APP = INGESTION_SCHEMA["target_app_token"]
TARGET_TABLE = INGESTION_SCHEMA["target_table_id"]


def load_uploader():
    path = Path(__file__).with_name("upload_feishu_attachments.py")
    spec = importlib.util.spec_from_file_location("feishu_uploader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load attachment uploader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api_json(response: requests.Response, label: str) -> dict:
    response.raise_for_status()
    body = response.json()
    if body.get("code") != 0:
        raise RuntimeError(f"{label}: {body.get('msg', 'unknown error')}")
    return body.get("data", {})


def scalar(value):
    if isinstance(value, list):
        if not value:
            return None
        first = value[0]
        if isinstance(first, dict):
            return first.get("text") or first.get("value") or first.get("name")
        return first
    return value


def link_value(value):
    if isinstance(value, dict) and value.get("link"):
        return {"text": value.get("text") or value["link"], "link": value["link"]}
    return None


def upload_one(path: Path, headers: dict[str, str], parent_node: str, uploader) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parent_type = "bitable_image" if content_type.startswith("image/") else "bitable_file"
    if path.stat().st_size > uploader.SINGLE_UPLOAD_LIMIT:
        return uploader.upload_multipart(path, headers, parent_type, parent_node)
    with path.open("rb") as handle:
        response = requests.post(
            f"{API_ROOT}/drive/v1/medias/upload_all",
            headers=headers,
            data={
                "file_name": path.name,
                "parent_type": parent_type,
                "parent_node": parent_node,
                "size": str(path.stat().st_size),
            },
            files={"file": (path.name, handle, content_type)},
            timeout=120,
        )
    return api_json(response, f"upload {path.name}")["file_token"]


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--env", default=str(Path(__file__).resolve().parents[1] / ".env"))
    args = parser.parse_args()
    config = read_env(Path(args.env).resolve())
    token_response = requests.post(
        f"{API_ROOT}/auth/v3/tenant_access_token/internal",
        json={"app_id": config["FEISHU_APP_ID"], "app_secret": config["FEISHU_APP_SECRET"]},
        timeout=30,
    )
    token = token_response.json().get("tenant_access_token")
    if not token:
        raise RuntimeError("unable to obtain tenant token")
    headers = {"Authorization": f"Bearer {token}"}

    source_data = {
        "field_names": [
            "广告标题", "广告ID", "品牌", "行业", "广告目标", "地区", "周期", "CTR", "点赞",
            "评论", "分享", "视频时长", "落地页", "Creative Center链接", "视频", "封面", "图表",
            "抓取时间", "分析状态",
        ]
    }
    source = api_json(
        requests.post(
            f"{API_ROOT}/bitable/v1/apps/{SOURCE_APP}/tables/{SOURCE_TABLE}/records/search",
            headers={**headers, "Content-Type": "application/json"},
            json=source_data,
            timeout=60,
        ),
        "read source records",
    )
    uploader = load_uploader()
    migrated = 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="tk_migrate_") as temp_dir:
        temp = Path(temp_dir)
        for item in source.get("items", []):
            fields = item.get("fields", {})
            ad_id = str(scalar(fields.get("广告ID")) or "")
            if not ad_id:
                failures.append("missing_id")
                continue
            target_fields = {
                "广告标题": scalar(fields.get("广告标题")) or ad_id,
                "广告ID": ad_id,
                "广告文案": scalar(fields.get("广告标题")) or "",
                "品牌": scalar(fields.get("品牌")) or "",
                "行业": scalar(fields.get("行业")) or "",
                "广告目标": scalar(fields.get("广告目标")) or "",
                "地区": scalar(fields.get("地区")) or "",
                "周期": scalar(fields.get("周期")) or "",
                "CTR排行": fields.get("CTR"),
                "Likes": fields.get("点赞"),
                "评论": fields.get("评论"),
                "分享": fields.get("分享"),
                "预算": scalar(fields.get("预算")) or "",
                "视频时长": fields.get("视频时长"),
                "抓取时间": fields.get("抓取时间"),
                "分析状态": scalar(fields.get("分析状态")) or "待分析",
            }
            for source_name, target_name in (("落地页", "落地页"), ("Creative Center链接", "Creative Center链接")):
                link = link_value(fields.get(source_name))
                if link:
                    target_fields[target_name] = link
            target_fields = {key: value for key, value in target_fields.items() if value not in (None, "")}
            created = api_json(
                requests.post(
                    f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{TARGET_TABLE}/records",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"fields": target_fields},
                    timeout=60,
                ),
                f"create {ad_id}",
            )
            record_id = created["record"]["record_id"]
            attachments = {}
            for source_name, target_name in (("视频", "视频"), ("封面", "封面"), ("图表", "图表_CTR")):
                files = fields.get(source_name) or []
                if not files:
                    continue
                file_info = files[0]
                filename = file_info.get("name") or f"{ad_id}_{source_name}"
                local_path = temp / f"{ad_id}_{source_name}_{filename}"
                download = requests.get(
                    f"{API_ROOT}/drive/v1/medias/{file_info['file_token']}/download",
                    headers=headers,
                    timeout=180,
                )
                download.raise_for_status()
                local_path.write_bytes(download.content)
                attachments[target_name] = [{"file_token": upload_one(local_path, headers, TARGET_APP, uploader)}]
            if attachments:
                api_json(
                    requests.put(
                        f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{TARGET_TABLE}/records/{record_id}",
                        headers={**headers, "Content-Type": "application/json"},
                        json={"fields": attachments},
                        timeout=60,
                    ),
                    f"attach {ad_id}",
                )
            migrated += 1
    print(json.dumps({"migrated": migrated, "total": len(source.get("items", [])), "failures": failures}, ensure_ascii=False))


if __name__ == "__main__":
    main()
