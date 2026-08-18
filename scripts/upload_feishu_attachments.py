"""CLI for uploading local media to a Feishu Base attachment field.

The reusable implementation lives in ``feishu_attachment_uploader.py``. This
thin CLI is kept as the documented entry point and remains compatible with
the ingestion scripts that import ``upload_multipart`` from this file.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from feishu_attachment_uploader import (
    API_ROOT,
    SINGLE_UPLOAD_LIMIT,
    FeishuAttachmentUploader,
    read_env,
    require_ok,
    upload_multipart,
)

__all__ = [
    "API_ROOT",
    "SINGLE_UPLOAD_LIMIT",
    "FeishuAttachmentUploader",
    "read_env",
    "require_ok",
    "upload_multipart",
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload local files and attach their tokens to a Feishu Base record."
    )
    parser.add_argument("--record-id", required=True)
    parser.add_argument("--field", required=True)
    parser.add_argument(
        "--env",
        default=None,
        help="dotenv file; defaults to FEISHU_ENV_FILE, .hermes/.env, or .env",
    )
    parser.add_argument(
        "--app-token",
        default=os.environ.get("FEISHU_APP_TOKEN"),
        help="target Base app token (or FEISHU_APP_TOKEN)",
    )
    parser.add_argument(
        "--table-id",
        default=os.environ.get("FEISHU_TABLE_ID"),
        help="target table ID (or FEISHU_TABLE_ID)",
    )
    parser.add_argument(
        "--parent-type",
        choices=("bitable_image", "bitable_file"),
        help="Override the Feishu media upload parent type for every file.",
    )
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    if not args.app_token or not args.table_id:
        parser.error("--app-token and --table-id are required (or set FEISHU_APP_TOKEN/FEISHU_TABLE_ID)")

    paths = [Path(value).expanduser().resolve() for value in args.files]
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    uploader = FeishuAttachmentUploader.from_env(args.env)
    tokens = uploader.upload_and_attach(
        app_token=args.app_token,
        table_id=args.table_id,
        record_id=args.record_id,
        field=args.field,
        files=paths,
        parent_type=args.parent_type,
    )
    print(json.dumps({"record_id": args.record_id, "field": args.field, "files": [path.name for path in paths]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
