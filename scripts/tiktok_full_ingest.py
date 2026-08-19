"""Capture TikTok detail pages and write them to the designated Feishu Base."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import mimetypes
import re
import tempfile
import time
from pathlib import Path

import requests

from tiktok_cdp_scraper import CDP


API_ROOT = "https://open.feishu.cn/open-apis"
TARGET_APP = "QQ1ib0FTHahCUhstRH8cVx9in7S"
MAIN_TABLE = "tblUsj7XFrRTbUpK"
METRICS = ["CTR", "CVR", "Clicks", "Conversion", "Remain"]


DETAIL_SCRIPT = r"""
(async () => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  window.scrollTo(0, document.body.scrollHeight);
  await sleep(1200);
  const text = document.body?.innerText || '';
  const lines = text.split(/\n+/).map(x => x.trim()).filter(Boolean);
  const exact = label => { const i = lines.findIndex(x => x === label); return i >= 0 ? lines[i + 1] || '' : ''; };
  const block = (start, end) => { const a=lines.indexOf(start), b=lines.indexOf(end); return a>=0 ? lines.slice(a+1,b>a?b:Math.min(a+8,lines.length)).join('\n') : ''; };
  const viewAll = [...document.querySelectorAll('button,[role="button"],div,span')].find(x => /^View all/.test(x.innerText?.trim()||''));
  if (viewAll) { viewAll.click(); await sleep(400); }
  const refreshed = document.body?.innerText || text;
  const refreshedLines = refreshed.split(/\n+/).map(x => x.trim()).filter(Boolean);
  const refreshedExact = label => { const i=refreshedLines.findIndex(x=>x===label); return i>=0?refreshedLines[i+1]||'':''; };
  const productLinks = [...document.querySelectorAll('a[href]')]
    .map(a=>({text:a.innerText.trim(),href:a.href}))
    .filter(x=>x.text || /shop|product|item|goods/i.test(x.href))
    .filter(x=>!x.href.includes('ads.tiktok.com/business/creativecenter'));
  const productImages = [...document.images].map(x=>({alt:x.alt||'',src:x.currentSrc||x.src}))
    .filter(x=>x.src && !x.src.includes('ttwstatic.com'));
  const highlight = (refreshed.match(/occur at ([^\n]+?) seconds/i)||[, ''])[1];
  return {
    values:{region:refreshedExact('Region'),industry:refreshedExact('Industry'),objective:refreshedExact('Objective'),brand:refreshedExact('Brand name'),landing_page:refreshedExact('Landing Page'),likes:refreshedExact('Likes'),comments:refreshedExact('Comments'),shares:refreshedExact('Shares'),ctr:refreshedExact('CTR'),budget:refreshedExact('Budget')},
    caption:block('Ad caption','Ad performance'),highlight,product_links:productLinks,product_images:productImages,
    body_text:refreshed.slice(0,12000),canvas:[...document.querySelectorAll('canvas')].map(x=>({w:x.width,h:x.height}))
  };
})()
"""


def chart_script(metric: str) -> str:
    return f"""
(async () => {{
  const label = {json.dumps(metric)};
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const nodes = [...document.querySelectorAll('div,span,button,[role="button"]')].filter(x => x.innerText?.trim() === label);
  const tab = nodes.find(x => x.className?.toString().includes('tab')) || nodes.find(x => x.getBoundingClientRect().width > 40);
  if (tab) (tab.closest('button,[role="button"]') || tab).click();
  await sleep(850);
  const canvas = [...document.querySelectorAll('canvas')].find(x => x.width > 500);
  const body = document.body?.innerText || '';
  return {{metric:label,data_url:canvas?.toDataURL('image/png')||'',summary:body.slice(Math.max(0,body.indexOf(label)),Math.min(body.length,body.indexOf(label)+1200))}};
}})()
"""


def load_uploader():
    path = Path(__file__).with_name("upload_feishu_attachments.py")
    spec = importlib.util.spec_from_file_location("feishu_uploader", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Feishu uploader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def api(response: requests.Response, label: str) -> dict:
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
        return first.get("text") if isinstance(first, dict) else first
    return value


def number(value):
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    match = re.search(r"(-?[\d]+(?:\.\d+)?)\s*([KMB万亿])?", text, re.IGNORECASE)
    if not match:
        return None
    multiplier = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000,
        "万": 10_000,
        "亿": 100_000_000,
    }.get((match.group(2) or "").lower(), 1)
    return float(match.group(1)) * multiplier


def download(url: str, path: Path, headers: dict[str, str]) -> None:
    response = requests.get(url, headers=headers, timeout=180)
    response.raise_for_status()
    path.write_bytes(response.content)


def upload(path: Path, headers: dict[str, str], uploader) -> str:
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    parent_type = "bitable_image" if content_type.startswith("image/") else "bitable_file"
    if path.stat().st_size > uploader.SINGLE_UPLOAD_LIMIT:
        return uploader.upload_multipart(path, headers, parent_type, TARGET_APP)
    response = None
    for attempt in range(4):
        try:
            with path.open("rb") as handle:
                response = requests.post(
                    f"{API_ROOT}/drive/v1/medias/upload_all",
                    headers=headers,
                    data={"file_name":path.name,"parent_type":parent_type,"parent_node":TARGET_APP,"size":str(path.stat().st_size)},
                    files={"file":(path.name,handle,content_type)},
                    timeout=180,
                )
            if response.status_code not in (408, 429) and response.status_code < 500:
                break
        except requests.RequestException:
            if attempt == 3:
                raise
        if attempt < 3:
            time.sleep(2 ** attempt)
    return api(response, f"upload {path.name}")["file_token"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", required=True)
    parser.add_argument("--env", default=str(Path(__file__).resolve().parents[1] / ".env"))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--new-worker-tab",
        action="store_true",
        help="Create a dedicated worker tab. By default, reuse the already-open TikTok tab to avoid repeated browser permission prompts.",
    )
    args = parser.parse_args()
    rows = json.loads(Path(args.list).read_text(encoding="utf-8"))[args.start:args.start + args.limit]
    config = read_env(Path(args.env).resolve())
    token_body = requests.post(f"{API_ROOT}/auth/v3/tenant_access_token/internal",json={"app_id":config["FEISHU_APP_ID"],"app_secret":config["FEISHU_APP_SECRET"]},timeout=30).json()
    headers = {"Authorization":f"Bearer {token_body['tenant_access_token']}"}
    uploader = load_uploader()

    existing_data = api(requests.post(f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/search",headers={**headers,"Content-Type":"application/json"},json={"field_names":["广告ID","视频","封面"]},timeout=60),"read target")
    existing = {str(scalar(x.get("fields",{}).get("广告ID"))):x for x in existing_data.get("items",[]) if scalar(x.get("fields",{}).get("广告ID"))}
    cdp = CDP()
    target_id = None
    original_url = None
    first_url = rows[0]["href"].rstrip("/") + "/pc/en?countryCode=TH&from=001110&period=180"
    try:
        if args.new_worker_tab:
            target_id, session = cdp.create_page_session(first_url)
        else:
            # Reuse the user's already-authorized Creative Center tab. This avoids
            # creating a fresh browser target for every run, which is the source
            # of the repeated "Allow" prompt in the desktop browser.
            session = cdp.page_session()
            original_url = cdp.evaluate(session, "location.href")
            cdp.navigate(session, first_url)
    except RuntimeError:
        # If no Creative Center tab is open, create one once as a fallback.
        target_id, session = cdp.create_page_session(first_url)
    completed = []
    try:
        with tempfile.TemporaryDirectory(prefix="tk_detail_") as temp_dir:
            temp = Path(temp_dir)
            for row in rows:
                ad_id = row["ad_id"]
                url = row["href"].rstrip("/") + "/pc/en?countryCode=TH&from=001110&period=180"
                cdp.navigate(session, url)
                deadline = time.time() + 20
                while time.time() < deadline:
                    try:
                        if cdp.evaluate(session,"document.readyState==='complete' && document.body?.innerText.includes('About this ad')"):
                            break
                    except Exception:
                        pass
                    time.sleep(0.5)
                detail = cdp.evaluate(session, DETAIL_SCRIPT) or {}
                chart_tokens = {}
                for metric in METRICS:
                    chart = cdp.evaluate(session, chart_script(metric)) or {}
                    data_url = chart.get("data_url", "")
                    if data_url.startswith("data:image"):
                        path = temp / f"{ad_id}_{metric}.png"
                        path.write_bytes(base64.b64decode(data_url.split(",",1)[1]))
                        chart_tokens[metric] = upload(path, headers, uploader)
                values = detail.get("values", {})
                main_fields = {
                    "广告标题":row.get("title") or ad_id,"广告ID":ad_id,"广告文案":detail.get("caption") or row.get("title") or "",
                    "品牌":values.get("brand") if values.get("brand") not in (None,"-") else row.get("brand", ""),
                    "行业":values.get("industry", ""),"广告目标":values.get("objective", ""),"地区":values.get("region", ""),"周期":"180天",
                    "CTR排行":number(values.get("ctr")),"Likes":number(values.get("likes")),"评论":number(values.get("comments")),"分享":number(values.get("shares")),"预算":values.get("budget", ""),
                    "视频时长":row.get("duration"),"高光时间":detail.get("highlight", ""),"商品信息":json.dumps(detail.get("product_links",[]),ensure_ascii=False),
                    "原始详情JSON":json.dumps(detail,ensure_ascii=False)[:18000],"抓取时间":int(time.time()*1000),"分析状态":"待分析",
                    "Creative Center链接":{"text":"TikTok Creative Center","link":row["href"]},
                }
                if values.get("landing_page") not in (None,"-") and str(values.get("landing_page")).startswith("http"):
                    main_fields["落地页"]={"text":values["landing_page"],"link":values["landing_page"]}
                for metric, token in chart_tokens.items():
                    main_fields[f"图表_{metric}"]=[{"file_token":token}]
                if ad_id in existing:
                    record_id=existing[ad_id]["record_id"]
                    api(requests.put(f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/{record_id}",headers={**headers,"Content-Type":"application/json"},json={"fields":main_fields},timeout=60),f"update {ad_id}")
                else:
                    created=api(requests.post(f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records",headers={**headers,"Content-Type":"application/json"},json={"fields":main_fields},timeout=60),f"create {ad_id}")
                    record_id=created["record"]["record_id"]
                existing_fields = existing.get(ad_id, {}).get("fields", {})
                media_fields = {}
                if not existing_fields.get("视频") and row.get("video_url"):
                    video_path=temp/f"{ad_id}.mp4"
                    download(row["video_url"],video_path,headers={})
                    media_fields["视频"]=[{"file_token":upload(video_path,headers,uploader)}]
                if not existing_fields.get("封面") and row.get("cover_url"):
                    cover_path=temp/f"{ad_id}.jpg"
                    download(row["cover_url"],cover_path,headers={})
                    media_fields["封面"]=[{"file_token":upload(cover_path,headers,uploader)}]
                if media_fields:
                    api(requests.put(f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/{record_id}",headers={**headers,"Content-Type":"application/json"},json={"fields":media_fields},timeout=60),f"attach {ad_id}")
                completed.append({"ad_id":ad_id,"record_id":record_id,"charts":len(chart_tokens)})
                print(json.dumps({"ad_id":ad_id,"charts":len(chart_tokens)},ensure_ascii=True),flush=True)
    finally:
        if target_id:
            cdp.close_target(target_id)
        elif original_url and "ads.tiktok.com/business/creativecenter" in original_url:
            # Leave the user's tab where it was before the run.
            cdp.navigate(session, original_url)
        cdp.close()
    print(json.dumps({"completed":completed},ensure_ascii=True))


if __name__ == "__main__":
    main()
