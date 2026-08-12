"""Smoke-test с Playwright: обходит /security-check/ JS-challenge через реальный headless-Chromium."""
import argparse, json, re, sys, time
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright
from parser_v2 import parse_card

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

def fetch_html_pw(url, timeout_ms=45000):
    """Реальный браузер: goto → wait до появления state → return HTML + cookies."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled'],
        )
        context = browser.new_context(
            user_agent=UA,
            locale='ru-RU',
            timezone_id='Asia/Yekaterinburg',
            viewport={'width': 1440, 'height': 900},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            "Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU','ru','en']});"
        )
        page = context.new_page()
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
            try:
                page.wait_for_function(
                    'window.__INITIAL_STATE__ && window.__INITIAL_STATE__.page',
                    timeout=timeout_ms
                )
            except Exception:
                pass
            html = page.content()
            final_url = page.url
            cookies = context.cookies()
        finally:
            browser.close()
    return html, final_url, cookies


def cookie_header(cookies):
    return '; '.join(f"{c['name']}={c['value']}" for c in cookies if c.get('domain','').endswith('satom.ru') or c.get('domain','').endswith('vostok-agrohim.ru'))


def download_photo(url, out_dir, sku_slug, size_label, cookie_hdr):
    fname = url.split('/')[-1].split('?')[0]
    path = out_dir / f'{sku_slug}__{size_label}__{fname}'
    if path.exists(): return path, 'cached'
    hdrs = {
        'User-Agent': UA,
        'Referer': 'https://vostok-agrohim.ru/',
        'Accept': 'image/webp,image/*,*/*;q=0.8',
    }
    if cookie_hdr:
        hdrs['Cookie'] = cookie_hdr
    r = requests.get(url, headers=hdrs, timeout=30)
    if r.status_code == 403:
        r = requests.get(url, headers={**hdrs, 'Referer': 'https://satom.ru/'}, timeout=30)
    r.raise_for_status()
    path.write_bytes(r.content)
    return path, 'downloaded'


def sku_slug(name):
    trans = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'yo','ж':'zh','з':'z','и':'i',
             'й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t',
             'у':'u','ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y',
             'ь':'','э':'e','ю':'yu','я':'ya'}
    s = ''.join(trans.get(c.lower(), c.lower()) if c.lower() in trans else c for c in name)
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--out', default='phase-4-content/parsed_v2')
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'photos').mkdir(exist_ok=True)
    (out_dir / 'raw_html').mkdir(exist_ok=True)

    print(f'Fetching (Playwright): {args.url}')
    try:
        html, final_url, cookies = fetch_html_pw(args.url)
    except Exception as e:
        print(f'FATAL fetch failed: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'Got {len(html):,} bytes, final URL: {final_url}')
    print(f'Cookies: {len(cookies)}')

    if 'window.__INITIAL_STATE__' not in html:
        print('ANTI-BOT: state НЕ загрузился даже через Playwright. Первые 800 симв:', file=sys.stderr)
        print(html[:800], file=sys.stderr)
        sys.exit(2)

    if '/security-check/' in final_url:
        print(f'ANTI-BOT: застряли на security-check: {final_url}', file=sys.stderr)
        print(html[:800], file=sys.stderr)
        sys.exit(2)

    try:
        data = parse_card(html, args.url)
    except Exception as e:
        print(f'PARSE failed: {e}', file=sys.stderr)
        sys.exit(3)

    slug = sku_slug(data.get('name') or 'unknown')
    (out_dir / 'raw_html' / f'{slug}.html').write_text(html, encoding='utf-8')

    ck = cookie_header(cookies)
    data['photos_downloaded'] = []
    for i, ph in enumerate(data.get('photos', [])):
        for size in ('big', 'source'):
            u = ph.get(size)
            if not u: continue
            try:
                p, status = download_photo(u, out_dir / 'photos', f'{slug}_{i+1}', size, ck)
                data['photos_downloaded'].append({'photo_idx': i, 'size': size, 'url': u,
                                                   'path': str(p), 'status': status,
                                                   'bytes': p.stat().st_size})
            except Exception as e:
                data['_flags'].append(f'photo_download_failed: {size}#{i}: {str(e)[:80]}')

    (out_dir / f'{slug}.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'\n✓ SMOKE PASSED')
    print(f'  Имя:          {data.get("name")}')
    print(f'  Цена:         {(data.get("price") or {}).get("raw")}')
    print(f'  Attrs pairs:  {sum(len(g.get("pairs", [])) for g in data["attrs"].values())}')
    print(f'  Photos:       {len(data["photos"])} (downloaded: {len(data["photos_downloaded"])})')
    print(f'  Description:  {(data.get("description") or {}).get("length_chars", 0)} chars')
    print(f'  Related:      {len(data["related_goods"])}')
    print(f'  SEO tags:     {len(data["seo_tags"])}')
    print(f'  Flags:        {data["_flags"] or "—"}')
    print(f'  → JSON:       {out_dir / f"{slug}.json"}')

if __name__ == '__main__':
    main()
