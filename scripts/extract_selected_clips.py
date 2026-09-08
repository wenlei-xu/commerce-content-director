#!/usr/bin/env python3
"""Extract explicitly selected clips and archive them in 精选片段库.

The source supplied for this run is a mixed final video.  Exports are muted so
the selected-clip library keeps reusable visuals rather than freezing the
source voiceover into a future remix.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))

from feishu_api import Feishu, config, text  # noqa: E402
from feishu_attachment_uploader import FeishuAttachmentUploader  # noqa: E402


TABLE_KEY = "selected_clips"
PRODUCT = "菠萝狗狗玩具"
TAG_PREFIXES = ("用途｜", "动作｜", "卖点｜", "复用｜")

CLIPS: list[dict[str, Any]] = [
    {
        "label": "S01",
        "start": 0.0,
        "end": 3.5,
        "tags": ["用途｜钩子", "动作｜抢玩具", "复用｜品类可复用"],
        "description": "S01｜狗狗看到主人递来的菠萝，跳起叼住，随后落地开始玩。",
        "voiceover": "拆家或抢玩具式开场，先用狗狗的即时反应吸引注意。",
    },
    {
        "label": "S02",
        "start": 3.5,
        "end": 6.5,
        "tags": ["用途｜产品展示", "复用｜单SKU"],
        "description": "S02｜菠萝玩具单独立在地板上，正面展示外观和镂空纹理。",
        "voiceover": "自然带出这是菠萝漏食玩具，做轻量产品介绍。",
    },
    {
        "label": "S03",
        "start": 6.5,
        "end": 9.5,
        "tags": ["用途｜卖点证明", "动作｜啃咬", "卖点｜耐磨耐咬", "卖点｜辅助洁牙", "复用｜单SKU"],
        "description": "S03｜狗狗侧面近景，后槽牙反复啃咬菠萝表面的凸起纹理。",
        "voiceover": "突出耐磨耐咬，以及凸起纹理辅助磨牙的使用场景。",
    },
    {
        "label": "S04",
        "start": 9.5,
        "end": 12.5,
        "tags": ["用途｜卖点证明", "动作｜塞食", "卖点｜益智漏食", "复用｜单SKU"],
        "description": "S04｜手持玩具翻到底部，清楚展示底部漏食孔和装零食的入口。",
        "voiceover": "说明怎么打开、装零食，把漏食玩法讲清楚。",
    },
    {
        "label": "S05",
        "start": 12.5,
        "end": 19.5,
        "tags": ["用途｜玩法演示", "动作｜掏食", "卖点｜益智漏食", "复用｜品类可复用"],
        "description": "S05｜狗狗在地板上用鼻子和爪子推动菠萝，持续啃咬并找食。",
        "voiceover": "强调狗狗可以自己玩、慢慢消耗精力，适合主人出门前留下。",
    },
    {
        "label": "S07",
        "start": 21.416,
        "end": 23.958,
        "tags": ["用途｜卖点证明", "动作｜啃咬", "卖点｜耐磨耐咬", "复用｜单SKU"],
        "description": "S07｜狗狗近距离叼住菠萝持续啃咬，牙齿与玩具的受力状态清晰可见。",
        "voiceover": "强调柔软耐咬，适合日常啃咬和消耗。",
    },
    {
        "label": "S06",
        "start": 19.5,
        "end": 21.416,
        "tags": ["用途｜玩法演示", "动作｜叼回", "复用｜品类可复用"],
        "description": "S06｜狗狗从门口叼着菠萝向镜头走来，形成主动回到主人身边的互动画面。",
        "voiceover": "用于表现玩具的互动感、召回感和狗狗主动参与。",
    },
    {
        "label": "S08",
        "start": 23.958,
        "end": 27.458,
        "tags": ["用途｜卖点证明", "动作｜冲洗", "卖点｜方便清洁", "卖点｜一体结构", "复用｜单SKU"],
        "description": "S08｜水槽下用水流冲洗菠萝，水流穿过孔洞和纹理，玩具被冲得干净。",
        "voiceover": "强调一体结构和冲洗方便，清洁起来省事。",
    },
    {
        "label": "S09",
        "start": 27.458,
        "end": 29.0,
        "tags": ["用途｜收尾", "动作｜互动", "复用｜品类可复用"],
        "description": "S09｜狗狗安静坐在主人身边，主人轻抚狗狗，菠萝玩具放在前景作为温馨收尾。",
        "voiceover": "用于省心、陪伴和情绪收尾，不承担新的卖点解释。",
    },
]


def record_id(payload: dict[str, Any]) -> str:
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    value = payload.get("record_id") or payload.get("id") or record.get("record_id") or record.get("id")
    if not value:
        raise RuntimeError(f"创建记录后未返回 record_id: {payload}")
    return str(value)


def attachment_count(value: Any) -> int:
    if not isinstance(value, list):
        return 0
    return sum(1 for item in value if isinstance(item, dict) and (item.get("file_token") or item.get("token")))


def validate_clip_spec(clip: dict[str, Any]) -> None:
    required = {"label", "start", "end", "tags", "description", "voiceover"}
    missing = sorted(required - set(clip))
    if missing:
        raise ValueError(f"片段 {clip.get('label')} 缺少字段: {missing}")
    if not clip["tags"] or any(not str(tag).startswith(TAG_PREFIXES) for tag in clip["tags"]):
        raise ValueError(f"片段 {clip['label']} 存在未使用前缀的标签: {clip['tags']}")
    if sum(str(tag).startswith("复用｜") for tag in clip["tags"]) != 1:
        raise ValueError(f"片段 {clip['label']} 必须且只能有一个复用范围标签: {clip['tags']}")


def extract_clip(ffmpeg: Path, source: Path, output: Path, start: float, end: float) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-i",
        str(source),
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output),
    ]
    subprocess.run(command, check=True)


def ensure_tag_options(api: Feishu, app: str, table_id: str, field_name: str, tags: list[str]) -> None:
    fields = api.fields(app, table_id)
    field = next((item for item in fields if item.get("field_name") == field_name), None)
    if not field:
        raise RuntimeError(f"找不到字段: {field_name}")
    existing = (field.get("property") or {}).get("options") or []
    names = [str(item.get("name")) for item in existing if item.get("name")]
    changed = False
    for tag in tags:
        if tag not in names:
            names.append(tag)
            changed = True
    if not changed:
        return
    api.update_field(
        app,
        table_id,
        str(field["field_id"]),
        {
            "field_name": field_name,
            "type": 4,
            "ui_type": "MultiSelect",
            "property": {"options": [{"name": name, "color": index % 55} for index, name in enumerate(names)]},
        },
    )
    fresh = next(item for item in api.fields(app, table_id) if item.get("field_name") == field_name)
    fresh_names = [str(item.get("name")) for item in (fresh.get("property") or {}).get("options", [])]
    if any(tag not in fresh_names for tag in tags):
        raise RuntimeError(f"片段标签选项 fresh-read 校验失败: {fresh_names}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    source = args.source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    ffmpeg = SKILL / "vendor" / "bin" / "ffmpeg.exe"
    if not ffmpeg.is_file():
        raise FileNotFoundError(ffmpeg)

    schema = config()
    app = schema["app_token"]
    table_id = schema["tables"][TABLE_KEY]["table_id"]
    api = Feishu()
    uploader = FeishuAttachmentUploader.from_env(SKILL / ".env")

    for clip in CLIPS:
        validate_clip_spec(clip)
    all_tags = sorted({tag for clip in CLIPS for tag in clip["tags"]})
    ensure_tag_options(api, app, table_id, "片段标签", all_tags)

    existing = api.records(app, table_id)
    by_description = {
        text(item.get("fields", {}).get("画面描述")): item
        for item in existing
        if text(item.get("fields", {}).get("画面描述"))
    }
    report: list[dict[str, Any]] = []

    for clip in CLIPS:
        filename = f"{clip['label']}_{clip['start']:05.2f}-{clip['end']:05.2f}.mp4"
        output = args.output_dir.resolve() / filename
        extract_clip(ffmpeg, source, output, float(clip["start"]), float(clip["end"]))

        old = by_description.get(clip["description"])
        if old:
            rid = str(old["record_id"])
            api.update_record(
                app,
                table_id,
                rid,
                {
                    "产品 / SKU": PRODUCT,
                    "片段标签": clip["tags"],
                    "画面描述": clip["description"],
                    "适合的口播方向": clip["voiceover"],
                    "当前状态": "可用",
                },
            )
            fresh = api.call("GET", f"/bitable/v1/apps/{app}/tables/{table_id}/records/{rid}").get("record", {})
            fresh_fields = fresh.get("fields", {}) if isinstance(fresh, dict) else {}
            if attachment_count(fresh_fields.get("片段视频")) < 1:
                uploader.upload_and_attach(
                    app_token=app,
                    table_id=table_id,
                    record_id=rid,
                    field="片段视频",
                    files=[output],
                    parent_type="bitable_file",
                )
                fresh = api.call("GET", f"/bitable/v1/apps/{app}/tables/{table_id}/records/{rid}").get("record", {})
            report.append({"label": clip["label"], "record_id": rid, "status": "updated", "file": str(output)})
            continue

        created = api.call(
            "POST",
            f"/bitable/v1/apps/{app}/tables/{table_id}/records",
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={
                "fields": {
                    "产品 / SKU": PRODUCT,
                    "片段标签": clip["tags"],
                    "画面描述": clip["description"],
                    "适合的口播方向": clip["voiceover"],
                    "当前状态": "可用",
                }
            },
        )
        rid = record_id(created)
        uploader.upload_and_attach(
            app_token=app,
            table_id=table_id,
            record_id=rid,
            field="片段视频",
            files=[output],
            parent_type="bitable_file",
        )
        fresh = api.call("GET", f"/bitable/v1/apps/{app}/tables/{table_id}/records/{rid}").get("record", {})
        fresh_fields = fresh.get("fields", {}) if isinstance(fresh, dict) else {}
        if attachment_count(fresh_fields.get("片段视频")) < 1 or text(fresh_fields.get("当前状态")) != "可用":
            raise RuntimeError(f"{clip['label']} record fresh-read verification failed: {fresh}")
        by_description[clip["description"]] = fresh
        report.append({"label": clip["label"], "record_id": rid, "status": "created", "file": str(output)})

    print(json.dumps({"run_id": args.run_id, "table_id": table_id, "items": report}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
