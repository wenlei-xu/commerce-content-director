"""Drive the already-open Chrome TikTok page through the local CDP websocket.

The Chrome process used by the desktop app accepts CDP websocket connections
without an Origin header. This keeps the user's existing login session in the
browser; no cookies are read or printed.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import websocket


class CDP:
    def __init__(self, url: str = "ws://127.0.0.1:9222/devtools/browser") -> None:
        # Loading a 100-card Creative Center result set can legitimately take
        # longer than the default websocket timeout while the page lazy-loads.
        self.ws = websocket.create_connection(url, timeout=180, suppress_origin=True)
        self.next_id = 0

    def command(self, method: str, params: dict | None = None, session_id: str | None = None) -> dict:
        self.next_id += 1
        message = {"id": self.next_id, "method": method, "params": params or {}}
        if session_id:
            message["sessionId"] = session_id
        self.ws.send(json.dumps(message))
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") == self.next_id:
                if "error" in response:
                    raise RuntimeError(f"CDP {method} failed: {response['error']}")
                return response.get("result", {})

    def close(self) -> None:
        self.ws.close()

    def page_session(self, url_contains: str = "ads.tiktok.com/business/creativecenter") -> str:
        targets = self.command("Target.getTargets").get("targetInfos", [])
        page = next((t for t in targets if t.get("type") == "page" and url_contains in t.get("url", "")), None)
        if not page:
            raise RuntimeError("no open TikTok Creative Center page found")
        return self.command("Target.attachToTarget", {"targetId": page["targetId"], "flatten": True})["sessionId"]

    def create_page_session(self, url: str) -> tuple[str, str]:
        target_id = self.command("Target.createTarget", {"url": url, "background": True})["targetId"]
        session_id = self.command("Target.attachToTarget", {"targetId": target_id, "flatten": True})["sessionId"]
        return target_id, session_id

    def close_target(self, target_id: str) -> None:
        self.command("Target.closeTarget", {"targetId": target_id})

    def navigate(self, session_id: str, url: str) -> None:
        self.command("Page.navigate", {"url": url}, session_id)

    def evaluate(self, session_id: str, expression: str):
        result = self.command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
                "userGesture": True,
            },
            session_id,
        )
        remote = result.get("result", {})
        if remote.get("subtype") == "error" or "exceptionDetails" in result:
            raise RuntimeError(result.get("exceptionDetails", remote))
        return remote.get("value")


CARD_SCRIPT = r"""
(async () => {
  const target = 100;
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const selector = '[class*="TopadsVideoCard_card__"]';
  let last = 0;
  for (let round = 0; round < 100; round++) {
    const count = document.querySelectorAll(selector).length;
    if (count >= target) break;
    window.scrollTo(0, document.body.scrollHeight);
    await sleep(1000);
    const now = document.querySelectorAll(selector).length;
    if (now === last && round > 8) await sleep(1500);
    last = now;
  }
  return document.querySelectorAll(selector).length;
})()
"""


METADATA_SCRIPT = r"""
(() => {
  const seen = new Set();
  const rows = [...document.querySelectorAll('[class*="TopadsVideoCard_card__"]')].map((card, index) => {
  const href = card.querySelector('a')?.href || '';
  const ad_id = (href.match(/topads\/(\d+)/) || [, ''])[1];
  const title = card.querySelector('[class*="videoDesc"]')?.innerText.trim() || '';
  const values = [...card.querySelectorAll('[class*="itemValue"]')].map(x => x.innerText.trim());
  const compactNumber = raw => {
    const match = String(raw || '').replace(/,/g, '').match(/(-?\d+(?:\.\d+)?)\s*([KMB万亿])?/i);
    if (!match) return null;
    const multiplier = ({k: 1e3, m: 1e6, b: 1e9, '万': 1e4, '亿': 1e8}[String(match[2] || '').toLowerCase()] || 1);
    return Number(match[1]) * multiplier;
  };
  const likes = compactNumber(values[0]);
  const ctr_rank = Number((values[1]?.match(/(\d+(?:\.\d+)?)%/) || [, ''])[1]) || null;
  const box = card.querySelector('[class*="TopadsVideoCard_cardVideo"]') || card;
  const bg = box.getAttribute('style') || '';
  const cover_url = (bg.match(/url\(["']?([^"')]+)["']?\)/) || [, ''])[1];
  const tags = [...title.matchAll(/#([A-Za-z][A-Za-z0-9_-]*)/g)].map(m => m[1]);
  return {index, ad_id, title, href, likes, ctr_rank, budget: values[2] || '', cover_url, brand: tags[0] || ''};
  }).filter(row => row.ad_id && !seen.has(row.ad_id) && seen.add(row.ad_id));
  return rows.slice(0, 100);
})()
"""


MEDIA_BATCH_SCRIPT = r"""
(async (start, end) => {
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const cards = [...document.querySelectorAll('[class*="TopadsVideoCard_card__"]')].slice(0, 120);
  const output = [];
  for (let index = start; index < Math.min(end, cards.length); index++) {
    const card = cards[index];
    const box = card.querySelector('[class*="TopadsVideoCard_cardVideo"]') || card;
    card.scrollIntoView({block: 'center'});
    for (const type of ['mouseenter', 'mouseover']) {
      box.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true, view: window}));
    }
    let video_url = '';
    let duration = 0;
    const deadline = Date.now() + 3000;
    while (Date.now() < deadline) {
      await sleep(250);
      const video = card.querySelector('video');
      video_url = video?.currentSrc || video?.src || '';
      duration = video?.duration || 0;
      if (video_url && video_url.includes('tiktokcdn.com')) break;
    }
    const href = card.querySelector('a')?.href || '';
    const ad_id = (href.match(/topads\/(\d+)/) || [, ''])[1];
    output.push({index, ad_id, video_url, duration});
  }
  return output;
})(START, END)
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=".tmp_tiktok_100/list.json")
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    cdp = CDP()
    try:
        session = cdp.page_session()
        count = cdp.evaluate(session, CARD_SCRIPT)
        metadata = cdp.evaluate(session, METADATA_SCRIPT) or []
        by_id = {row.get("ad_id"): row for row in metadata if row.get("ad_id")}
        for start in range(0, min(int(count or 0), 120), 10):
            script = MEDIA_BATCH_SCRIPT.replace("START", str(start)).replace("END", str(start + 10))
            for row in cdp.evaluate(session, script) or []:
                if row.get("ad_id") in by_id:
                    by_id[row["ad_id"]].update(row)
        rows = list(by_id.values())[:100]
        output.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"card_count": count, "rows": len(rows), "output": str(output)}, ensure_ascii=False))
    finally:
        cdp.close()


if __name__ == "__main__":
    main()
