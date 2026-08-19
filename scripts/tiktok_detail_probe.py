import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tiktok_cdp_scraper import CDP


DETAIL_SCRIPT = r"""
(() => {
  const text = document.body?.innerText || '';
  const lines = text.split(/\n+/).map(x => x.trim()).filter(Boolean);
  const exact = label => {
    const index = lines.findIndex(x => x === label);
    return index >= 0 ? lines[index + 1] || '' : '';
  };
  const candidates = label => [...document.querySelectorAll('button,[role="button"],div,span')]
    .filter(x => x.innerText?.trim() === label)
    .map(x => ({tag:x.tagName, cls:x.className, rect:x.getBoundingClientRect().toJSON(), html:x.outerHTML.slice(0,300)}))
    .filter(x => x.rect.width > 0 && x.rect.height > 0)
    .slice(0,10);
  const chartCanvases = [...document.querySelectorAll('canvas')].map(x => ({w:x.width,h:x.height}));
  return {
    title: document.title,
    values: {
      region: exact('Region'), industry: exact('Industry'), objective: exact('Objective'),
      brand: exact('Brand name'), landing_page: exact('Landing Page'),
      likes: exact('Likes'), comments: exact('Comments'), shares: exact('Shares'),
      ctr: exact('CTR'), budget: exact('Budget')
    },
    highlight: (text.match(/occur at ([^\n]+?) seconds/i) || [, ''])[1],
    chart_canvases: chartCanvases,
    tabs: Object.fromEntries(['CTR','CVR','Clicks','Conversion','Remain'].map(x => [x,candidates(x)])),
    links: [...document.querySelectorAll('a[href]')].map(a => ({text:a.innerText.trim(),href:a.href})).filter(x => x.text || /shop|product|item/i.test(x.href)).slice(0,100),
    images: [...document.images].map(x => ({alt:x.alt||'',src:x.currentSrc||x.src})).filter(x => x.src).slice(0,100),
    body_text: text.slice(0,30000)
  };
})()
"""


def main():
    rows = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    row = rows[0]
    url = row['href'].rstrip('/') + '/pc/en?countryCode=TH&from=001110&period=180'
    cdp = CDP()
    target_id, session = cdp.create_page_session(url)
    try:
        end = time.time() + 20
        while time.time() < end:
            try:
                ready = cdp.evaluate(session, "document.readyState === 'complete' && document.body?.innerText.includes('Interactive time analysis')")
                if ready:
                    break
            except Exception:
                pass
            time.sleep(0.5)
        cdp.evaluate(session, "(async()=>{window.scrollTo(0,document.body.scrollHeight);await new Promise(r=>setTimeout(r,1800));return [...document.querySelectorAll('canvas')].map(x=>({w:x.width,h:x.height}))})()")
        value = cdp.evaluate(session, DETAIL_SCRIPT)
        print(json.dumps({'ad_id':row['ad_id'],'target_id':target_id,'detail':{**value,'body_text':None}},ensure_ascii=True))
    finally:
        cdp.close_target(target_id)
        cdp.close()


if __name__ == '__main__':
    main()
