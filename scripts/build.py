"""Сборка сайта: data/*.csv + content/*.yml + site/templates -> dist/.
Цены берутся только из data/prices.csv."""
import csv, json, os, re, shutil, sys
from collections import defaultdict
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent.parent
SEVEN = [("dv_text", "Действующее вещество"), ("form", "Форма препарата"), ("drug_type", "Тип применения"),
         ("penetration", "Способ проникновения"), ("hazard_human", "Класс опасности для человека"),
         ("hazard_bee", "Класс опасности для пчёл"), ("phytotox", "Фитотоксичность")]


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def money(v):
    return f"{int(float(v)):,}".replace(",", " ") + " ₽"


def tel(v):
    return "+" + "".join(ch for ch in v if ch.isdigit())


def md(v):
    """**жирный** из SEO-текстов -> <strong>, остальное экранируется."""
    return Markup(re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(escape(v))))


def word_preparat(n):
    if n % 10 == 1 and n % 100 != 11:
        return "препарат"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return "препарата"
    return "препаратов"


def build(root=ROOT, out=None):
    root = Path(root)
    data, tpl, content = root / "data", root / "site" / "templates", root / "content"
    out = Path(out) if out else root / "dist"
    warnings = []
    s = yaml.safe_load((data / "settings.yml").read_text(encoding="utf-8"))
    prices = {r["slug"]: r["price"] for r in read_csv(data / "prices.csv")}
    cats = read_csv(data / "dict" / "categories.csv")
    cat_by = {c["slug"]: c for c in cats}
    mk = {r["slug"]: r for r in read_csv(data / "dict" / "manufacturers.csv")}
    crops = {r["slug"]: r for r in read_csv(data / "dict" / "crops.csv")}
    pests = {r["slug"]: r for r in read_csv(data / "dict" / "pests.csv")}
    subs = {r["slug"]: r for r in read_csv(data / "dict" / "substances.csv")}

    def links(name, key):
        d = defaultdict(list)
        for r in read_csv(data / "links" / name):
            d[r["slug"]].append(r[key])
        return d
    l_sub, l_crop, l_pest = links("product_substance.csv", "substance"), links("product_crop.csv", "crop"), links("product_pest.csv", "pest")
    l_cross = defaultdict(list)
    for r in sorted(read_csv(data / "links" / "cross_sell.csv"), key=lambda r: int(r["order"])):
        l_cross[r["slug"]].append(r["related"])

    products = [p for p in read_csv(data / "products.csv") if p["status"] == "published"]
    by_slug = {}
    for p in products:
        if p["slug"] not in prices:
            sys.exit(f"Нет цены для {p['slug']} в prices.csv")
        p["price_num"] = int(float(prices[p["slug"]]))
        p["price_text"] = money(p["price_num"])
        p["url"] = f"/catalog/{p['category']}/{p['slug']}/"
        p["substances"], p["crops"], p["pests"] = l_sub[p["slug"]], l_crop[p["slug"]], l_pest[p["slug"]]
        p["maker_badge"] = mk[p["manufacturer"]]["badge"]
        p["category_one"] = cat_by[p["category"]]["name_one"]
        # Нет фото — заглушка по виду упаковки (решение Оли 28.10.2026, Ф2)
        img = "/static/img/products/"
        if p["photo"]:
            p["img480"], p["img1000"] = f"{img}{p['photo']}-480.webp", f"{img}{p['photo']}-1000.webp"
        else:
            p["img480"] = p["img1000"] = f"{img}placeholder-{'liquid' if p['unit'] == 'л' else 'solid'}.svg"
        miss = [label for key, label in SEVEN if not p.get(key)]
        if miss:
            warnings.append(f"{p['slug']}: не заполнены характеристики: {', '.join(miss)}")
        by_slug[p["slug"]] = p

    env = Environment(loader=FileSystemLoader(tpl), undefined=StrictUndefined, autoescape=True)
    env.filters["tel"] = tel
    env.filters["md"] = md
    if out.exists():
        shutil.rmtree(out)
    pages = []

    def write(rel, html):
        f = out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
        pages.append(rel)
    noindex = os.environ.get("NOINDEX") == "1"  # закрытый тестовый сайт
    common = dict(s=s, cats=cats, noindex=noindex)

    # Список категории
    for cat in cats:
        items = sorted([p for p in products if p["category"] == cat["slug"]], key=lambda p: p["name"])
        if not items:
            continue
        seo_file = content / "seo" / f"{cat['slug']}.yml"
        seo = yaml.safe_load(seo_file.read_text(encoding="utf-8")) if seo_file.exists() else {}

        def group(key, title, field, names):
            cnt = defaultdict(int)
            for p in items:
                for v in (p[field] if isinstance(p[field], list) else [p[field]]):
                    if v:
                        cnt[v] += 1
            its = [dict(value=v, label=names.get(v, {"name": v})["name"], count=n) for v, n in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))]
            return dict(key=key, title=title, items=its) if its else None
        action_names = {"izbiratelnyy": {"name": "Избирательный"}, "sploshnoy": {"name": "Сплошного действия"}}
        groups = [g for g in [group("dv", "Действующее вещество", "substances", subs), group("crop", "Культура", "crops", crops),
                              group("pest", "Вредный объект", "pests", pests),
                              group("maker", "Производитель", "manufacturer", {k: {"name": v["name"]} for k, v in mk.items()}),
                              group("action", "Характер действия", "action_character", action_names)] if g]
        ser = defaultdict(int)
        for p in items:
            if p["series"]:
                ser[p["series"]] += 1
        series_pills = [dict(name=n, value=n) for n, c in sorted(ser.items()) if c >= 2]  # ПИ06: серия при ≥2 препаратах
        dvc = defaultdict(int)
        for p in items:
            for v in p["substances"]:
                dvc[v] += 1
        dv_pills = [dict(name=subs[v]["name"], value=v) for v, c in sorted(dvc.items(), key=lambda kv: -kv[1])[:5]]
        task_pills = [dict(name="Сплошного действия", value="sploshnoy")] if any(p["action_character"] == "sploshnoy" for p in items) else []
        prices_l = [p["price_num"] for p in items]
        html = env.get_template("listing.html").render(
            **common, title=seo.get("meta", {}).get("title") or f"{cat['name']} — купить в Челябинске | Восток АгроХим",
            description=seo.get("meta", {}).get("description") or seo.get("lead", ""), canonical=f"/catalog/{cat['slug']}/", category=cat, items=items,
            count_word=word_preparat(len(items)), lead=seo.get("lead", ""), seo=seo.get("seo"), groups=groups,
            series_pills=series_pills, dv_pills=dv_pills, task_pills=task_pills,
            price_min=min(prices_l), price_max=max(prices_l), other_cats=[c for c in cats if c["slug"] != cat["slug"]])
        write(f"catalog/{cat['slug']}/index.html", html)

    # Карточки
    for p in products:
        cfile = content / "products" / f"{p['slug']}.yml"
        c = yaml.safe_load(cfile.read_text(encoding="utf-8")) if cfile.exists() else {}
        for k, dflt in (("regulation", []), ("regulation_notes", {}), ("resistant_weeds_note", ""), ("procedures", []),
                        ("procedures_tail", []), ("first_aid", []), ("mechanism", [])):
            c.setdefault(k, dflt)
        specs = [(label, p[key]) for key, label in SEVEN if p.get(key)]
        cross = []
        for rs in l_cross[p["slug"]]:
            if rs in by_slug:
                q = by_slug[rs]
                cross.append(dict(name=q["name"], url=q["url"], photo=q["photo"], img480=q["img480"], category_one=q["category_one"], dv_text=q["dv_text"]))
        ld = {"@context": "https://schema.org", "@type": "Product", "name": p["name"], "description": p["description"],
              "brand": {"@type": "Brand", "name": mk[p["manufacturer"]]["name"]},
              "offers": {"@type": "Offer", "price": str(p["price_num"]), "priceCurrency": "RUB",
                         "url": f"{s['site_url']}{p['url']}"}}
        if p["photo"]:
            ld["image"] = f"{s['site_url']}{p['img1000']}"
        html = env.get_template("product.html").render(
            **common, title=f"{p['name']} — купить в Челябинске | Восток АгроХим", description=p["description"],
            canonical=p["url"], p=p, category=cat_by[p["category"]], maker=mk[p["manufacturer"]], specs=specs, c=c,
            crops=[crops[x] for x in p["crops"]], pests=[pests[x] for x in p["pests"]], cross=cross,
            jsonld=json.dumps(ld, ensure_ascii=False))
        write(f"catalog/{p['category']}/{p['slug']}/index.html", html)

    # Главная
    hp = {}
    hf = content / "pages" / "home.yml"
    if hf.exists():
        hp = yaml.safe_load(hf.read_text(encoding="utf-8"))
    write("index.html", env.get_template("home.html").render(
        **common, title="Восток АгроХим — средства защиты растений в Челябинске", description=hp.get("description", ""),
        canonical="/", h=hp, featured=[by_slug[x] for x in hp.get("featured", []) if x in by_slug]))

    shutil.copytree(root / "site" / "static", out / "static")
    # Тестовая копия закрыта от поисковиков; на боевом сайте robots.txt появится на этапе 5
    if noindex:
        (out / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    return out, warnings


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    o, w = build()
    for x in w:
        print("ВНИМАНИЕ:", x)
    print(f"Собрано страниц: {sum(1 for _ in o.rglob('*.html'))} в {o}")
