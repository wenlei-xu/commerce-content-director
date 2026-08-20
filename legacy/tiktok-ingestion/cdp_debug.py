import sys
import json
sys.path.insert(0, str(__file__).rsplit('\\', 1)[0])
from tiktok_cdp_scraper import CDP

c = CDP()
try:
    s = c.page_session()
    print('count', c.evaluate(s, "document.querySelectorAll('[class*=" + '"' + "TopadsVideoCard_card__" + '"' + "]').length"))
    print('title', c.evaluate(s, "document.title"))
    expr = """[...document.querySelectorAll('[class*="TopadsVideoCard_card__"]')].slice(0,2).map(x => ({cls:x.className, href:x.querySelector('a')?.href || '', text:x.innerText.slice(0,100)}))"""
    value = c.evaluate(s, expr)
    print('sample', json.dumps([{'cls':x['cls'],'href':x['href']} for x in value], ensure_ascii=True))
    ids = c.evaluate(s, "[...document.querySelectorAll('[class*=\\\"TopadsVideoCard_card__\\\"]')].slice(0,117).map((x,i)=>({i,href:x.querySelector('a')?.href||''}))")
    print('missing_href', json.dumps([x for x in ids if not x['href']], ensure_ascii=True))
    print('unique_ids', c.evaluate(s, "(()=>{const a=[...document.querySelectorAll('[class*=\\\"TopadsVideoCard_card__\\\"]')].slice(0,117).map(x=>(x.querySelector('a')?.href||'').match(/topads\\/(\\d+)/)?.[1]).filter(Boolean);return {total:a.length,unique:new Set(a).size,dups:a.filter((x,i)=>a.indexOf(x)!==i).slice(0,20)}})()"))
finally:
    c.close()
