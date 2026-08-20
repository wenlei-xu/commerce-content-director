"""Run the TikTok detail ingest through one long-lived Chrome DevTools MCP connection.

Chrome 144+ asks for permission per DevTools connection.  This runner starts one
connection, reuses one selected tab, and processes the complete range before
disconnecting, so the permission prompt is not repeated for every batch/page.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import threading
import time
from pathlib import Path

import requests

from tiktok_full_ingest import (
    API_ROOT,
    DETAIL_SCRIPT,
    MAIN_TABLE,
    METRICS,
    TARGET_APP,
    api,
    chart_script,
    download,
    load_uploader,
    number,
    read_env,
    scalar,
    upload,
)


NODE = r"E:\JavaStudy\nodejs\node.exe"
MCP_ENTRY = r"E:\JavaStudy\nvm\v18.18.2\node_cache\_npx\15c61037b1978c83\node_modules\chrome-devtools-mcp\build\src\bin\chrome-devtools-mcp.js"
CHROME_ACTIVE_PORT = Path(r"C:\Users\33583\AppData\Local\Google\Chrome\User Data\DevToolsActivePort")


def chrome_ws_endpoint() -> str:
    lines = [line.strip() for line in CHROME_ACTIVE_PORT.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError(f"Invalid Chrome DevToolsActivePort: {CHROME_ACTIVE_PORT}")
    return f"ws://127.0.0.1:{lines[0]}{lines[1]}"


def click_allow_prompt() -> None:
    """Click Chrome's Allow button only if the remote-debugging prompt is visible."""
    try:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        point = wintypes.POINT(1538, 624)
        hwnd = user32.WindowFromPoint(point)
        title = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, title, 512)
        if "远程调试" not in title.value:
            return

        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x = 1538 - rect.left
        y = 624 - rect.top
        lparam = (y << 16) | (x & 0xFFFF)
        user32.SetForegroundWindow(hwnd)
        user32.PostMessageW(hwnd, 0x0201, 1, lparam)  # WM_LBUTTONDOWN
        user32.PostMessageW(hwnd, 0x0202, 0, lparam)  # WM_LBUTTONUP
    except Exception:
        pass


def allow_prompt_worker() -> None:
    for _ in range(30):
        click_allow_prompt()
        time.sleep(0.5)


class McpClient:
    def __init__(self) -> None:
        self.proc = subprocess.Popen(
            [NODE, MCP_ENTRY, "--ws-endpoint", chrome_ws_endpoint(), "--no-usage-statistics"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.next_id = 0

    def close(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def _send(self, message: dict) -> None:
        if not self.proc.stdin:
            raise RuntimeError("MCP stdin is closed")
        body = json.dumps(message, ensure_ascii=False).encode("utf-8")
        self.proc.stdin.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body + b"\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        request_id = self.next_id
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})
        if not self.proc.stdout:
            raise RuntimeError("MCP stdout is closed")
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("Chrome DevTools MCP exited unexpectedly")
            # The bundled server emits newline-delimited JSON when attached
            # to pipes, while a PTY may expose Content-Length framing.
            stripped = line.strip()
            if stripped.startswith(b"{"):
                message = json.loads(stripped.decode("utf-8"))
                if message.get("id") == request_id:
                    return message
                continue
            if not line.lower().startswith(b"content-length:"):
                continue
            length = int(line.split(b":", 1)[1].strip())
            # Consume the empty header separator.
            separator = self.proc.stdout.readline()
            if separator not in (b"\r\n", b"\n"):
                raise RuntimeError(f"Invalid MCP framing: {separator!r}")
            payload = self.proc.stdout.read(length)
            message = json.loads(payload.decode("utf-8"))
            if message.get("id") == request_id:
                return message

    def notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def call(self, name: str, arguments: dict | None = None) -> dict:
        result = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        if result.get("result", {}).get("isError"):
            raise RuntimeError(json.dumps(result, ensure_ascii=False))
        return result.get("result", {})

    def eval_json(self, function: str) -> object:
        result = self.call("evaluate_script", {"function": function})
        text = "\n".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")
        match = re.search(r"```json\s*(.*?)\s*```", text, re.S)
        if match:
            return json.loads(match.group(1))
        return json.loads(text)


def async_expression(expression: str) -> str:
    return f"async () => await {expression}"


def wait_for_detail_function() -> str:
    return """async () => {
      const deadline = Date.now() + 25000;
      while (Date.now() < deadline) {
        if (document.readyState === 'complete' && (document.body?.innerText || '').includes('About this ad')) return true;
        await new Promise(r => setTimeout(r, 500));
      }
      return false;
    }"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", required=True)
    parser.add_argument("--env", default=str(Path(__file__).resolve().parents[1] / ".env"))
    parser.add_argument("--start", type=int, default=5)
    parser.add_argument("--limit", type=int, default=95)
    args = parser.parse_args()

    all_rows = json.loads(Path(args.list).read_text(encoding="utf-8"))
    rows = all_rows[args.start : args.start + args.limit]
    if not rows:
        print(json.dumps({"completed": [], "message": "no rows"}, ensure_ascii=False))
        return

    config = read_env(Path(args.env).resolve())
    token_body = requests.post(
        f"{API_ROOT}/auth/v3/tenant_access_token/internal",
        json={"app_id": config["FEISHU_APP_ID"], "app_secret": config["FEISHU_APP_SECRET"]},
        timeout=30,
    ).json()
    headers = {"Authorization": f"Bearer {token_body['tenant_access_token']}"}
    uploader = load_uploader()

    existing_data = api(
        requests.post(
            f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/search",
            headers={**headers, "Content-Type": "application/json"},
            json={"field_names": ["广告ID", "视频", "封面"]},
            timeout=60,
        ),
        "read target",
    )
    existing = {
        str(scalar(item.get("fields", {}).get("广告ID"))): item
        for item in existing_data.get("items", [])
        if scalar(item.get("fields", {}).get("广告ID"))
    }

    mcp = McpClient()
    completed: list[dict] = []
    original_url = None
    try:
        mcp.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "tiktok-ingest", "version": "1.0"}})
        mcp.notify("notifications/initialized")

        # The first browser call may open Chrome's one-time consent dialog.
        threading.Thread(target=allow_prompt_worker, daemon=True).start()
        mcp.call("list_pages")
        original_url = mcp.eval_json("() => location.href")
        if not isinstance(original_url, str):
            original_url = None

        with __import__("tempfile").TemporaryDirectory(prefix="tk_detail_mcp_") as temp_dir:
            temp = Path(temp_dir)
            for row in rows:
                ad_id = row["ad_id"]
                url = row["href"].rstrip("/") + "/pc/en?countryCode=TH&from=001110&period=180"
                try:
                    mcp.call("navigate_page", {"type": "url", "url": url, "timeout": 30000})
                    mcp.eval_json(wait_for_detail_function())
                    detail = mcp.eval_json(async_expression(DETAIL_SCRIPT)) or {}

                    chart_tokens: dict[str, str] = {}
                    for metric in METRICS:
                        chart = mcp.eval_json(async_expression(chart_script(metric))) or {}
                        data_url = chart.get("data_url", "") if isinstance(chart, dict) else ""
                        if isinstance(data_url, str) and data_url.startswith("data:image"):
                            path = temp / f"{ad_id}_{metric}.png"
                            path.write_bytes(base64.b64decode(data_url.split(",", 1)[1]))
                            chart_tokens[metric] = upload(path, headers, uploader)

                    values = detail.get("values", {})
                    main_fields = {
                        "广告标题": row.get("title") or ad_id,
                        "广告ID": ad_id,
                        "广告文案": detail.get("caption") or row.get("title") or "",
                        "品牌": values.get("brand") if values.get("brand") not in (None, "-") else row.get("brand", ""),
                        "行业": values.get("industry", ""),
                        "广告目标": values.get("objective", ""),
                        "地区": values.get("region", ""),
                        "周期": "180天",
                        "CTR排行": number(values.get("ctr")),
                        "Likes": number(values.get("likes")),
                        "评论": number(values.get("comments")),
                        "分享": number(values.get("shares")),
                        "预算": values.get("budget", ""),
                        "视频时长": row.get("duration"),
                        "高光时间": detail.get("highlight", ""),
                        "商品信息": json.dumps(detail.get("product_links", []), ensure_ascii=False),
                        "原始详情JSON": json.dumps(detail, ensure_ascii=False)[:18000],
                        "抓取时间": int(time.time() * 1000),
                        "分析状态": "待分析",
                        "Creative Center链接": {"text": "TikTok Creative Center", "link": row["href"]},
                    }
                    if values.get("landing_page") not in (None, "-") and str(values.get("landing_page")).startswith("http"):
                        main_fields["落地页"] = {"text": values["landing_page"], "link": values["landing_page"]}
                    for metric, token in chart_tokens.items():
                        main_fields[f"图表_{metric}"] = [{"file_token": token}]

                    if ad_id in existing:
                        record_id = existing[ad_id]["record_id"]
                        api(
                            requests.put(
                                f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/{record_id}",
                                headers={**headers, "Content-Type": "application/json"},
                                json={"fields": main_fields},
                                timeout=60,
                            ),
                            f"update {ad_id}",
                        )
                    else:
                        created = api(
                            requests.post(
                                f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records",
                                headers={**headers, "Content-Type": "application/json"},
                                json={"fields": main_fields},
                                timeout=60,
                            ),
                            f"create {ad_id}",
                        )
                        record_id = created["record"]["record_id"]

                    if ad_id not in existing:
                        video_path = temp / f"{ad_id}.mp4"
                        cover_path = temp / f"{ad_id}.jpg"
                        download(row["video_url"], video_path, headers={})
                        download(row["cover_url"], cover_path, headers={})
                        video_token = upload(video_path, headers, uploader)
                        cover_token = upload(cover_path, headers, uploader)
                        api(
                            requests.put(
                                f"{API_ROOT}/bitable/v1/apps/{TARGET_APP}/tables/{MAIN_TABLE}/records/{record_id}",
                                headers={**headers, "Content-Type": "application/json"},
                                json={"fields": {"视频": [{"file_token": video_token}], "封面": [{"file_token": cover_token}]}},
                                timeout=60,
                            ),
                            f"attach {ad_id}",
                        )

                    item = {"ad_id": ad_id, "record_id": record_id, "charts": len(chart_tokens)}
                    completed.append(item)
                    print(json.dumps(item, ensure_ascii=False), flush=True)
                except Exception as exc:
                    print(json.dumps({"ad_id": ad_id, "error": str(exc)}, ensure_ascii=False), flush=True)
    finally:
        if original_url and "ads.tiktok.com/business/creativecenter" in original_url:
            try:
                mcp.call("navigate_page", {"type": "url", "url": original_url, "timeout": 30000})
            except Exception:
                pass
        mcp.close()

    print(json.dumps({"completed": completed, "completed_count": len(completed)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
