"""Portable Feishu media upload client for Base attachment fields.

This module deliberately does not depend on a browser, Feishu UI, or a
workspace-specific Base. Callers can authenticate with either an app ID and
secret or an already-issued tenant access token, upload a local file or bytes,
and then attach the returned file tokens to any Base record.
"""

from __future__ import annotations

import io
import json
import mimetypes
import os
from pathlib import Path
from typing import Iterable, Mapping

import requests


API_ROOT = "https://open.feishu.cn/open-apis"
SINGLE_UPLOAD_LIMIT = 20 * 1024 * 1024
DEFAULT_TIMEOUT = 90


def read_env(path: Path) -> dict[str, str]:
    """Read a small dotenv-style file without printing or exposing secrets."""
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _env_file_values(env_path: str | Path | None) -> dict[str, str]:
    if env_path:
        path = Path(env_path).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        return read_env(path)

    for key in ("FEISHU_ENV_FILE", "HERMES_ENV_FILE"):
        candidate = os.environ.get(key)
        if candidate:
            path = Path(candidate).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            return read_env(path)

    skill_env = Path(__file__).resolve().parents[1] / ".env"
    for candidate in (skill_env, Path.cwd() / ".hermes" / ".env", Path.cwd() / ".env"):
        if candidate.is_file():
            return read_env(candidate)
    return {}


def _content_type(filename: str, explicit: str | None = None) -> str:
    return explicit or mimetypes.guess_type(filename)[0] or "application/octet-stream"


class FeishuAttachmentUploader:
    """Upload media and attach it to a Feishu Base record."""

    def __init__(
        self,
        *,
        app_id: str | None = None,
        app_secret: str | None = None,
        tenant_access_token: str | None = None,
        api_root: str = API_ROOT,
        session: requests.Session | None = None,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = tenant_access_token
        self.api_root = api_root.rstrip("/")
        self.session = session or requests.Session()
        self._headers: dict[str, str] | None = None

    @classmethod
    def from_env(cls, env_path: str | Path | None = None) -> "FeishuAttachmentUploader":
        values = _env_file_values(env_path)

        def value(name: str) -> str | None:
            return os.environ.get(name) or values.get(name)

        return cls(
            app_id=value("FEISHU_APP_ID"),
            app_secret=value("FEISHU_APP_SECRET"),
            tenant_access_token=value("FEISHU_TENANT_ACCESS_TOKEN"),
            api_root=value("FEISHU_API_ROOT") or API_ROOT,
        )

    def _headers_for_request(self) -> dict[str, str]:
        if self._headers is not None:
            return self._headers
        if self.tenant_access_token:
            token = self.tenant_access_token
        else:
            if not self.app_id or not self.app_secret:
                raise RuntimeError(
                    "Feishu auth requires FEISHU_TENANT_ACCESS_TOKEN or "
                    "FEISHU_APP_ID plus FEISHU_APP_SECRET"
                )
            response = self.session.post(
                f"{self.api_root}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
                timeout=30,
            )
            body = self._require_ok(response, "get tenant access token")
            token = body.get("tenant_access_token")
            if not token and isinstance(body.get("data"), dict):
                token = body["data"].get("tenant_access_token")
            if not token:
                raise RuntimeError("get tenant access token failed: missing token")
        self._headers = {"Authorization": f"Bearer {token}"}
        return self._headers

    @staticmethod
    def _require_ok(response: requests.Response, step: str) -> dict:
        response.raise_for_status()
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(f"{step} failed: Feishu returned non-JSON data") from exc
        if body.get("code") != 0:
            raise RuntimeError(f"{step} failed: {body.get('msg', 'unknown error')}")
        # Feishu auth responses expose tenant_access_token at the top level,
        # while most other endpoints wrap their payload in ``data``.
        data = body.get("data")
        return body if data is None else data

    def _upload_all(
        self,
        *,
        filename: str,
        content: bytes,
        parent_type: str,
        parent_node: str,
        content_type: str,
    ) -> str:
        response = self.session.post(
            f"{self.api_root}/drive/v1/medias/upload_all",
            headers=self._headers_for_request(),
            data={
                "file_name": filename,
                "parent_type": parent_type,
                "parent_node": parent_node,
                "size": str(len(content)),
            },
            files={"file": (filename, io.BytesIO(content), content_type)},
            timeout=DEFAULT_TIMEOUT,
        )
        return self._require_ok(response, f"upload {filename}")["file_token"]

    def _upload_file_path(
        self,
        path: Path,
        *,
        parent_type: str,
        parent_node: str,
        content_type: str,
    ) -> str:
        with path.open("rb") as handle:
            response = self.session.post(
                f"{self.api_root}/drive/v1/medias/upload_all",
                headers=self._headers_for_request(),
                data={
                    "file_name": path.name,
                    "parent_type": parent_type,
                    "parent_node": parent_node,
                    "size": str(path.stat().st_size),
                },
                files={"file": (path.name, handle, content_type)},
                timeout=DEFAULT_TIMEOUT,
            )
        return self._require_ok(response, f"upload {path.name}")["file_token"]

    def _upload_multipart_bytes(
        self,
        *,
        filename: str,
        content: bytes,
        parent_type: str,
        parent_node: str,
        content_type: str,
    ) -> str:
        headers = self._headers_for_request()
        prepare_response = self.session.post(
            f"{self.api_root}/drive/v1/medias/upload_prepare",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={
                "file_name": filename,
                "parent_type": parent_type,
                "parent_node": parent_node,
                "size": len(content),
            },
            timeout=30,
        )
        prepare = self._require_ok(prepare_response, f"prepare {filename}")
        upload_id = prepare["upload_id"]
        block_size = int(prepare["block_size"])
        block_num = int(prepare["block_num"])

        for seq in range(block_num):
            start = seq * block_size
            chunk = content[start : start + block_size]
            if not chunk:
                raise RuntimeError(f"empty block {seq} for {filename}")
            response = self.session.post(
                f"{self.api_root}/drive/v1/medias/upload_part",
                headers=headers,
                data={"upload_id": upload_id, "seq": str(seq), "size": str(len(chunk))},
                files={"file": (filename, io.BytesIO(chunk), content_type)},
                timeout=DEFAULT_TIMEOUT,
            )
            self._require_ok(response, f"upload block {seq} of {filename}")

        response = self.session.post(
            f"{self.api_root}/drive/v1/medias/upload_finish",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={"upload_id": upload_id, "block_num": block_num},
            timeout=60,
        )
        return self._require_ok(response, f"finish {filename}")["file_token"]

    def _upload_multipart_path(
        self,
        path: Path,
        *,
        parent_type: str,
        parent_node: str,
        content_type: str,
    ) -> str:
        headers = self._headers_for_request()
        prepare_response = self.session.post(
            f"{self.api_root}/drive/v1/medias/upload_prepare",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={
                "file_name": path.name,
                "parent_type": parent_type,
                "parent_node": parent_node,
                "size": path.stat().st_size,
            },
            timeout=30,
        )
        prepare = self._require_ok(prepare_response, f"prepare {path.name}")
        upload_id = prepare["upload_id"]
        block_size = int(prepare["block_size"])
        block_num = int(prepare["block_num"])

        with path.open("rb") as handle:
            for seq in range(block_num):
                chunk = handle.read(block_size)
                if not chunk:
                    raise RuntimeError(f"empty block {seq} for {path.name}")
                response = self.session.post(
                    f"{self.api_root}/drive/v1/medias/upload_part",
                    headers=headers,
                    data={"upload_id": upload_id, "seq": str(seq), "size": str(len(chunk))},
                    files={"file": (path.name, io.BytesIO(chunk), content_type)},
                    timeout=DEFAULT_TIMEOUT,
                )
                self._require_ok(response, f"upload block {seq} of {path.name}")

        response = self.session.post(
            f"{self.api_root}/drive/v1/medias/upload_finish",
            headers={**headers, "Content-Type": "application/json; charset=utf-8"},
            json={"upload_id": upload_id, "block_num": block_num},
            timeout=60,
        )
        return self._require_ok(response, f"finish {path.name}")["file_token"]

    def upload_bytes(
        self,
        filename: str,
        content: bytes,
        *,
        parent_node: str,
        parent_type: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Upload bytes and return a Feishu ``file_token``."""
        detected_type = _content_type(filename, content_type)
        detected_parent = parent_type or (
            "bitable_image" if detected_type.startswith("image/") else "bitable_file"
        )
        if len(content) > SINGLE_UPLOAD_LIMIT:
            return self._upload_multipart_bytes(
                filename=filename,
                content=content,
                parent_type=detected_parent,
                parent_node=parent_node,
                content_type=detected_type,
            )
        return self._upload_all(
            filename=filename,
            content=content,
            parent_type=detected_parent,
            parent_node=parent_node,
            content_type=detected_type,
        )

    def upload_file(
        self,
        path: str | Path,
        *,
        parent_node: str,
        parent_type: str | None = None,
    ) -> str:
        """Upload a local file and return a Feishu ``file_token``."""
        file_path = Path(path).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        detected_type = _content_type(file_path.name)
        detected_parent = parent_type or (
            "bitable_image" if detected_type.startswith("image/") else "bitable_file"
        )
        if file_path.stat().st_size > SINGLE_UPLOAD_LIMIT:
            return self._upload_multipart_path(
                file_path,
                parent_type=detected_parent,
                parent_node=parent_node,
                content_type=detected_type,
            )
        return self._upload_file_path(
            file_path,
            parent_type=detected_parent,
            parent_node=parent_node,
            content_type=detected_type,
        )

    def attach_tokens(
        self,
        *,
        app_token: str,
        table_id: str,
        record_id: str,
        field: str,
        file_tokens: Iterable[str],
    ) -> None:
        tokens = list(file_tokens)
        response = self.session.put(
            f"{self.api_root}/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            headers={**self._headers_for_request(), "Content-Type": "application/json"},
            data=json.dumps({"fields": {field: [{"file_token": token} for token in tokens]}}),
            timeout=30,
        )
        self._require_ok(response, f"attach {field}")

    def upload_and_attach(
        self,
        *,
        app_token: str,
        table_id: str,
        record_id: str,
        field: str,
        files: Iterable[str | Path],
        parent_type: str | None = None,
    ) -> list[str]:
        """Upload files and replace the target attachment field."""
        tokens = [
            self.upload_file(path, parent_node=app_token, parent_type=parent_type)
            for path in files
        ]
        self.attach_tokens(
            app_token=app_token,
            table_id=table_id,
            record_id=record_id,
            field=field,
            file_tokens=tokens,
        )
        return tokens


def require_ok(response: requests.Response, step: str) -> dict:
    """Compatibility helper for existing skill scripts."""
    return FeishuAttachmentUploader._require_ok(response, step)


def upload_multipart(
    path: Path,
    headers: Mapping[str, str],
    parent_type: str,
    parent_node: str,
) -> str:
    """Compatibility wrapper used by existing ingestion scripts."""
    authorization = headers.get("Authorization", "")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise RuntimeError("missing Authorization bearer token for multipart upload")
    uploader = FeishuAttachmentUploader(tenant_access_token=token)
    return uploader.upload_file(path, parent_node=parent_node, parent_type=parent_type)
