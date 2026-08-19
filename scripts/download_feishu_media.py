#!/usr/bin/env python3
"""Download a Feishu Drive media asset using this skill's own credentials.

The credential source is intentionally fixed to:
    skills/commerce-content-director/.env

This helper does not search the workspace, Hermes, or process-specific env files.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SKILL_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = SKILL_DIR / ".env"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024


def load_env(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE dotenv entries without importing other env files."""
    values: dict[str, str] = {}
    if not path.is_file():
        raise RuntimeError(f"skill env file not found: {path}")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise RuntimeError(f"invalid dotenv entry at {path}:{line_number}")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "a").isalnum() or key[0].isdigit():
            raise RuntimeError(f"invalid dotenv key at {path}:{line_number}")
        raw_value = raw_value.strip()
        try:
            parsed = shlex.split(raw_value, posix=True)
        except ValueError as exc:
            raise RuntimeError(f"invalid dotenv value at {path}:{line_number}") from exc
        values[key] = parsed[0] if parsed else ""
    return values


def require_env(values: dict[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise RuntimeError(f"missing {key} in {ENV_FILE}")
    return value


def api_url(domain: str, path: str) -> str:
    base = domain.strip().rstrip("/")
    if base.lower() == "feishu":
        base = "https://open.feishu.cn"
    elif base.lower() == "lark":
        base = "https://open.larksuite.com"
    elif not base.startswith(("http://", "https://")):
        base = f"https://{base}"
    return f"{base}{path}"


def request_json(url: str, *, method: str = "GET", headers: dict[str, str] | None = None, body: bytes | None = None) -> dict:
    request = Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            payload = response.read()
    except HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace")
        raise RuntimeError(f"Feishu request failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Feishu request failed: {exc.reason}") from exc

    try:
        result = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError("Feishu returned invalid JSON") from exc
    if result.get("code", 0) != 0:
        raise RuntimeError(f"Feishu API error {result.get('code')}: {result.get('msg', 'unknown error')}")
    return result


def tenant_access_token(app_id: str, app_secret: str, domain: str) -> str:
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    result = request_json(
        api_url(domain, "/open-apis/auth/v3/tenant_access_token/internal"),
        method="POST",
        headers={"Content-Type": "application/json"},
        body=body,
    )
    token = str(result.get("tenant_access_token", "")).strip()
    if not token:
        raise RuntimeError("Feishu auth response did not contain tenant_access_token")
    return token


def download_media(domain: str, access_token: str, file_token: str, destination: Path) -> tuple[int, str]:
    request = Request(
        api_url(domain, f"/open-apis/drive/v1/medias/{file_token}/download"),
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=60) as response:
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError(f"media exceeds {MAX_DOWNLOAD_BYTES} bytes")

            written = 0
            with destination.open("wb") as output:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_DOWNLOAD_BYTES:
                        raise RuntimeError(f"media exceeds {MAX_DOWNLOAD_BYTES} bytes")
                    output.write(chunk)
    except HTTPError as exc:
        detail = exc.read(512).decode("utf-8", errors="replace")
        raise RuntimeError(f"media download failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"media download failed: {exc.reason}") from exc
    except Exception:
        if destination.exists():
            destination.unlink()
        raise
    return written, content_type


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download a Feishu Drive media asset")
    parser.add_argument("--file-token", required=True, help="Feishu media/file token")
    parser.add_argument("--out", required=True, type=Path, help="Output file path")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    destination = args.out.expanduser().resolve()
    if destination.exists() and not args.force:
        print(f"output already exists; use --force to overwrite: {destination}", file=sys.stderr)
        return 2

    try:
        values = load_env(ENV_FILE)
        app_id = require_env(values, "FEISHU_APP_ID")
        app_secret = require_env(values, "FEISHU_APP_SECRET")
        domain = require_env(values, "FEISHU_DOMAIN")
        access_token = tenant_access_token(app_id, app_secret, domain)
        destination.parent.mkdir(parents=True, exist_ok=True)
        size, content_type = download_media(domain, access_token, args.file_token, destination)
    except (RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps({"output": os.fspath(destination), "bytes": size, "content_type": content_type}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
