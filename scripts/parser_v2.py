"""Парсер карточек satom.ru через window.__INITIAL_STATE__."""
import re, json
from html.parser import HTMLParser

def extract_state(html):
    marker = 'window.__INITIAL_STATE__='
    start = html.find(marker)
    if start < 0:
        raise ValueError('window.__INITIAL_STATE__ не найден (возможно anti-bot страница)')
    js = start + len(marker)
    depth = 0; in_str = False; esc = False; i = js
    while i < len(html):
        c = html[i]
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': in_str = not in_str
        elif not in_str:
            if c == '{': depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0: break
        i += 1
    raw = html[js:i+1]
    raw = re.sub(r':\s*undefined\s*([,}\]])', r':null\1', raw)
    return json.loads(raw)

VOID_TAGS = {'br','img','hr','input','meta','link'}
BLOCK_TAGS = {'p','div','tr','li','h1','h2','h3','h4','h5','h6','table','ul','ol','br'}

class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS: self.parts.append('\n')
        if tag == 'td': self.parts.append(' | ')
    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS: self.parts.append('\n')
    def handle_data(self, data): self.parts.append(data)

def html_to_text(html):
    p = _StripHTML()
    p.feed(html or '')
    return re.sub(r'\n{3,}', '\n\n', ''.join(p.parts)).strip()

def render_html(node):
    if node is None: return ''
    if isinstance(node, str): return node
    if isinstance(node, (int, float)): return str(node)
    if isinstance(node, list): return ''.join(render_html(x) for x in node)
    if isinstance(node, dict):
        if 'content' in node and 'children' not in node:
            return node['content'] or ''
        tag = node.get('tag'); children = node.get('children')
        if tag and tag[0].isupper(): return render_html(children)
        if not tag: return render_html(children)
        attrs = ''
        for a in ('cls','href','src','alt','title'):
            v = node.get(a)
            if v:
                name = 'class' if a == 'cls' else a
                attrs += f' {name}="{v}"'
        if tag.lower() in VOID_TAGS: return f'<{tag}{attrs}/>'
        return f'<{tag}{attrs}>{render_html(children)}</{tag}>'
    return ''

def render_text(node):
    return html_to_text(render_html(node))

def norm_url(u):
    if not u: return u
    if u.startswith('//'): return 'https:' + u
    return u

def extract_attrs(attrs_obj):
    out = {}
    if not isinstance(attrs_obj, dict): return out
    for group_key, group in attrs_obj.items():
        if not isinstance(group, dict): continue
        pairs = []
        for it in (group.get('items') or []):
            title = it.get('title')
            if isinstance(title, dict): title = render_text(title).strip()
            elif isinstance(title, str): title = title.strip()
            value = it.get('value')
            if isinstance(value, dict): value = render_text(value).strip()
            elif isinstance(value, str): value = value.strip()
            if title: pairs.append({'key': title, 'value': value})
        out[group_key] = {'title': group.get('title') or group_key, 'pairs': pairs}
    return out

def extract_crumbs(crumbs):
    if not crumbs: return []
    return [{'name': c.get('text'), 'url': c.get('url')} for c in crumbs if c.get('url') or c.get('text')]

def extract_seo_links(seo):
    if not seo: return []
    full = seo.get('full') or seo.get('items') or []
    return [{'name': l.get('text'), 'url': l.get('href')} for l in full]

def extract_goods_list(g):
    if not g: return []
    items = g.get('items') or g.get('goods') or []
    return [{'name': it.get('name') or it.get('title'), 'url': it.get('url') or it.get('link'),
             'id': it.get('id'), 'price': it.get('price') or it.get('priceValue')}
            for it in items if isinstance(it, dict)]

def extract_price(prod):
    pjm = prod.get('priceJsonMarkup')
    if isinstance(pjm, dict):
        txt = render_text(pjm).strip()
        m = re.match(r'([\d\s\xa0,\.]+)\s*(₽|руб)?\s*/?\s*(\S+)?', txt)
        if m:
            amount = m.group(1).replace('\xa0','').replace(' ','').replace(',','.')
            try: return {'amount': float(amount), 'currency': 'RUR', 'unit': m.group(3), 'raw': txt}
            except ValueError: pass
        return {'raw': txt}
    return None

def parse_card(html, source_url):
    state = extract_state(html)
    page = state.get('page', {})
    prod = page.get('product', {})
    head = page.get('headData', {}) or {}
    flags = []

    dm = prod.get('descMarkup')
    desc_html = render_html(dm) if dm else None
    desc_text = render_text(dm) if dm else None

    ai_markers = ['средних и крупных сельскохозяйственных','эргономичн','оптимизировать затраты',
                  'при затяжной весне','область применения и сценарии',
                  'ключевые преимущества препарата','характеристики и эксплуатация']
    if desc_text:
        first = desc_text[:2500].lower()
        if sum(1 for m in ai_markers if m in first) >= 2:
            flags.append('probable_ai_preamble')

    meta = {'title': head.get('title')}
    for m in head.get('meta', []) or []:
        n = m.get('name') or m.get('property')
        c = m.get('content')
        if n and c: meta[n] = c

    micro = page.get('microdataJsonLD')
    if isinstance(micro, str):
        try: micro = json.loads(micro)
        except: micro = {'_raw': micro[:200]}

    data = {
        'source_url': source_url,
        'name': prod.get('title'),
        'satom_id': prod.get('id'),
        'satom_vid': prod.get('vId'),
        'articul': prod.get('articul') or None,
        'vendor': prod.get('vendor'),
        'min_order': prod.get('minOrder'),
        'presence': prod.get('presence'),
        'presence_text': prod.get('presenceText'),
        'quantity': prod.get('quantity'),
        'price': extract_price(prod),
        'photos': [
            {'id': p.get('id'),
             'thumbnail': norm_url(p.get('thumbnail') or p.get('thumb')),
             'middle': norm_url(p.get('middle')),
             'source': norm_url(p.get('source')),
             'big': norm_url(p.get('big')),
             'original': norm_url(p.get('original')),
             'alt': p.get('alt'),
             'width': p.get('originalWidth'),
             'height': p.get('originalHeight')}
            for p in (prod.get('pics') or [])
        ],
        'attrs': extract_attrs(prod.get('attrs') or {}),
        'description': {'html': desc_html, 'text': desc_text,
                        'length_chars': len(desc_text or '')} if desc_text else None,
        'meta': meta,
        'breadcrumbs': extract_crumbs(page.get('crumbs')),
        'category_path_ids': page.get('categoryPath') or [],
        'seo_tags': extract_seo_links(page.get('seoLinks')),
        'related_goods': extract_goods_list(page.get('relatedGoods')),
        'similar_goods': extract_goods_list(page.get('similarGoods')),
        'microdata_jsonld': micro,
        '_flags': flags,
    }
    if not data['name']: flags.append('missing_name')
    if not data['price']: flags.append('missing_price')
    if not data['photos']: flags.append('no_photos')
    if not data['description'] or data['description']['length_chars'] < 100:
        flags.append('short_or_no_description')
    if not data['related_goods']: flags.append('no_related_goods')
    if not data['seo_tags']: flags.append('no_seo_tags')
    return data
