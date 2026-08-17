"""Upload local media to one Feishu Base attachment field without exposing credentials."""

import argparse
import json
import mimetypes
from pathlib import Path

import requests


API_ROOT = "https://open.feishu.cn/open-apis"
DEFAULT_APP_TOKEN = "QQ1ib0FTHahCUhstRH8cVx9in7S"
DEFAULT_TABLE_ID = "tblGPsdyzMG0o6zP"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def require_ok(response: requests.Response, step: str) -> dict:
    response.raise_for_status()
    body = response.json()
    if body.get("code") != 0:
        raise RuntimeError(f"{step} failed: {body.get('msg', 'unknown error')}")
    return body.get("data", {})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--field", required=True)
    parser.add_argument("--env", default=".hermes/.env")
    parser.add_argument("--app-token", default=DEFAULT_APP_TOKEN)
    parser.add_argument("--table-id", default=DEFAULT_TABLE_ID)
    parser.add_argument(
        "--parent-type",
        choices=("bitable_image", "bitable_file"),
        help="Override the Feishu media upload parent type for every file.",
    )
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    paths = [Path(value).resolve() for value in args.files]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    config = read_env(Path(args.env).resolve())
    for name in ("FEISHU_APP_ID", "FEISHU_APP_SECRET"):
        if not config.get(name):
            raise RuntimeError(f"missing {name} in {args.env}")

    token_response = requests.post(
        f"{API_ROOT}/auth/v3/tenant_access_token/internal",
        json={"app_id": config["FEISHU_APP_ID"], "app_secret": config["FEISHU_APP_SECRET"]},
        timeout=30,
    )
    token_response.raise_for_status()
    token_body = token_response.json()
    if token_body.get("code") != 0 or not token_body.get("tenant_access_token"):
        raise RuntimeError(f"get tenant token failed: {token_body.get('msg', 'unknown error')}")
    headers = {"Authorization": f"Bearer {token_body['tenant_access_token']}"}

    attachments = []
    for path in paths:
        if path.stat().st_size > 20 * 1024 * 1024:
            raise ValueError(
                f"{path.name} exceeds Feishu's 20 MB single-upload limit; use Feishu UI or multipart upload."
            )
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parent_type = args.parent_type or (
            "bitable_image" if content_type.startswith("image/") else "bitable_file"
        )
        with path.open("rb") as handle:
            upload_response = requests.post(
                f"{API_ROOT}/drive/v1/medias/upload_all",
                headers=headers,
                data={
                    "file_name": path.name,
                    "parent_type": parent_type,
                    "parent_node": args.app_token,
                    "size": str(path.stat().st_size),
                },
                files={"file": (path.name, handle, content_type)},
                timeout=90,
            )
        attachments.append({"file_token": require_ok(upload_response, f"upload {path.name}")["file_token"]})

    update_response = requests.put(
        f"{API_ROOT}/bitable/v1/apps/{args.app_token}/tables/{args.table_id}/records/{args.record_id}",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps({"fields": {args.field: attachments}}),
        timeout=30,
    )
    require_ok(update_response, f"attach {args.field}")
    print(json.dumps({"record_id": args.record_id, "field": args.field, "files": [path.name for path in paths]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
