#!/usr/bin/env python3
"""Prepare cached, Flow2API-compatible image inputs from approved Feishu media.

The input JSON contains an ``assets`` list. Each item needs ``role``, ``field``,
``file_token``, and ``filename``. The script keeps original downloads and a
complete, uncropped transport rendition in the skill-local cache, plus a plain
Base64 sidecar for the Flow2API MCP ``input_images`` payload.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from download_feishu_media import (
    ENV_FILE,
    download_media,
    load_env,
    require_env,
    tenant_access_token,
)


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIR = SKILL_DIR / ".cache" / "flow-inputs"
RENDER_POLICY = "flow-input-v1-max-edge-1024-jpeg-q88-no-crop"
MAX_EDGE = 1024
JPEG_QUALITY = 88


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cache_key(asset: dict[str, str]) -> str:
    source = "\x1f".join((asset["file_token"], asset["filename"], RENDER_POLICY))
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def load_plan(path: Path) -> list[dict[str, str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid asset plan: {path}") from exc

    items = value.get("assets")
    if not isinstance(items, list) or not items:
        raise RuntimeError("asset plan needs a non-empty assets list")

    required = ("role", "field", "file_token", "filename")
    seen: set[str] = set()
    normalized: list[dict[str, str]] = []
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            raise RuntimeError(f"assets[{index}] must be an object")
        asset = {key: str(raw.get(key, "")).strip() for key in required}
        if any(not asset[key] for key in required):
            raise RuntimeError(f"assets[{index}] is missing role, field, file_token, or filename")
        if asset["file_token"] in seen:
            raise RuntimeError(f"duplicate file_token in asset plan: {asset['file_token']}")
        seen.add(asset["file_token"])
        normalized.append(asset)
    return normalized


def load_cache_manifest(path: Path, asset: dict[str, str]) -> dict[str, Any] | None:
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    expected = {"file_token": asset["file_token"], "filename": asset["filename"], "render_policy": RENDER_POLICY}
    if any(manifest.get(key) != value for key, value in expected.items()):
        return None
    for relative in ("source_path", "flow_image_path", "base64_path"):
        if not isinstance(manifest.get(relative), str) or not (path / manifest[relative]).is_file():
            return None
    return manifest


def render_flow_image(source: Path, destination: Path) -> tuple[str, tuple[int, int]]:
    try:
        with Image.open(source) as image:
            image.load()
            width, height = image.size
            if width < 1 or height < 1:
                raise RuntimeError("image has invalid dimensions")
            image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
            if image.mode in {"RGBA", "LA"} or (image.mode == "P" and "transparency" in image.info):
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")
            image.save(destination, "JPEG", quality=JPEG_QUALITY, optimize=True)
            return "image/jpeg", (width, height)
    except (OSError, UnidentifiedImageError) as exc:
        raise RuntimeError(f"downloaded asset is not a valid image: {source.name}") from exc


def prepare_one(
    asset: dict[str, str],
    cache_dir: Path,
    domain: str,
    access_token: str,
) -> dict[str, Any]:
    destination = cache_dir / cache_key(asset)
    manifest = load_cache_manifest(destination, asset)
    if manifest is not None:
        return {
            "role": asset["role"],
            "field": asset["field"],
            "file_token": asset["file_token"],
            "filename": asset["filename"],
            "cache_status": "hit",
            "cache_dir": os.fspath(destination),
            "source_sha256": manifest["source_sha256"],
            "mime_type": manifest["mime_type"],
            "base64_path": os.fspath(destination / manifest["base64_path"]),
            "flow_image_path": os.fspath(destination / manifest["flow_image_path"]),
            "source_dimensions": manifest["source_dimensions"],
        }

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix="flow-input-", dir=destination.parent))
    try:
        source_name = "source" + Path(asset["filename"]).suffix.lower()
        source_path = temporary / source_name
        download_media(domain, access_token, asset["file_token"], source_path)
        source_sha256 = sha256_file(source_path)
        flow_image_path = temporary / "flow-input.jpg"
        mime_type, dimensions = render_flow_image(source_path, flow_image_path)
        base64_path = temporary / "flow-input.b64"
        base64_path.write_text(base64.b64encode(flow_image_path.read_bytes()).decode("ascii"), encoding="ascii")
        manifest = {
            "file_token": asset["file_token"],
            "filename": asset["filename"],
            "field": asset["field"],
            "role": asset["role"],
            "render_policy": RENDER_POLICY,
            "source_path": source_name,
            "flow_image_path": "flow-input.jpg",
            "base64_path": "flow-input.b64",
            "source_sha256": source_sha256,
            "flow_image_sha256": sha256_file(flow_image_path),
            "mime_type": mime_type,
            "source_dimensions": {"width": dimensions[0], "height": dimensions[1]},
            "prepared_at": datetime.now(UTC).isoformat(),
        }
        (temporary / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        if destination.exists():
            shutil.rmtree(temporary)
        else:
            temporary.replace(destination)
        return {
            "role": asset["role"],
            "field": asset["field"],
            "file_token": asset["file_token"],
            "filename": asset["filename"],
            "cache_status": "miss",
            "cache_dir": os.fspath(destination),
            "source_sha256": manifest["source_sha256"],
            "mime_type": manifest["mime_type"],
            "base64_path": os.fspath(destination / manifest["base64_path"]),
            "flow_image_path": os.fspath(destination / manifest["flow_image_path"]),
            "source_dimensions": manifest["source_dimensions"],
        }
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare cached Flow2API image inputs from Feishu assets")
    parser.add_argument("--asset-plan", required=True, type=Path, help="JSON file with an assets list")
    parser.add_argument("--out", required=True, type=Path, help="write scrubbed cache manifest JSON here")
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR, help="local cache directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        assets = load_plan(args.asset_plan.expanduser().resolve())
        values = load_env(ENV_FILE)
        domain = require_env(values, "FEISHU_DOMAIN")
        access_token = tenant_access_token(
            require_env(values, "FEISHU_APP_ID"),
            require_env(values, "FEISHU_APP_SECRET"),
            domain,
        )
        result = {
            "render_policy": RENDER_POLICY,
            "cache_dir": os.fspath(args.cache_dir.expanduser().resolve()),
            "assets": [prepare_one(asset, args.cache_dir.expanduser().resolve(), domain, access_token) for asset in assets],
        }
        output = args.out.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"output": os.fspath(output), "assets": [{"role": item["role"], "cache_status": item["cache_status"]} for item in result["assets"]]}, ensure_ascii=False))
    except (RuntimeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
