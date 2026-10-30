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
RESERVED = {"all", "promyshlennye", "sornyaki", "vrediteli", "bolezni"}  # site-structure-v1.md §1


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


def plural(n, forms):
    """forms: (1, 2–4, 5+) — («препарат», «препарата», «препаратов»)."""
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return forms[1]
    return forms[2]


def word_preparat(n):
    return plural(n, ("препарат", "препарата", "препаратов"))


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

    # DRAFTS=1 — сборка с черновиками, только для просмотра у себя; на тестовый и боевой сайт не выкладывается
    shown = {"published", "draft"} if os.environ.get("DRAFTS") == "1" else {"published"}
    products = [p for p in read_csv(data / "products.csv") if p["status"] in shown]
    if "draft" in shown:
        warnings.append("сборка с черновиками (DRAFTS=1) — не выкладывать")
    by_slug = {}
    for p in products:
        if p["slug"] in RESERVED:
            sys.exit(f"Адрес препарата {p['slug']} совпадает с зарезервированным словом")
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

    action_names = {"izbiratelnyy": {"name": "Избирательный"}, "sploshnoy": {"name": "Сплошного действия"}}
    facets = {"cat": ("Категория", "category", cat_by), "dv": ("Действующее вещество", "substances", subs),
              "crop": ("Культура", "crops", crops), "pest": ("Вредный объект", "pests", pests),
              "maker": ("Производитель", "manufacturer", {k: {"name": v["name"]} for k, v in mk.items()}),
              "action": ("Характер действия", "action_character", action_names)}

    def facet(items, key):
        title, field, names = facets[key]
        cnt = defaultdict(int)
        for p in items:
            for v in (p[field] if isinstance(p[field], list) else [p[field]]):
                if v:
                    cnt[v] += 1
        its = [dict(value=v, label=names.get(v, {"name": v})["name"], count=n) for v, n in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))]
        return dict(key=key, title=title, items=its) if its else None

    def read_seo(f):
        return yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else {}

    def listing(rel, items, h1, crumb, keys, quick, title, description, lead, seo, auto=None, other_title="Другие категории каталога", other_cats=cats):
        """Листинг по макету гербицидов: категория или страница входа (культура, объект, ДВ)."""
        prices_l = [p["price_num"] for p in items]
        write(rel, env.get_template("listing.html").render(
            **common, title=title, description=description, canonical="/" + rel.removesuffix("index.html"), h1=h1, crumb=crumb,
            items=items, count_word=word_preparat(len(items)), lead=lead, seo=seo, auto=auto, quick=[q for q in quick if q["items"]],
            groups=[g for g in (facet(items, k) for k in keys) if g], price_min=min(prices_l), price_max=max(prices_l),
            other_title=other_title, other_cats=other_cats))

    # Список категории
    for cat in cats:
        items = sorted([p for p in products if p["category"] == cat["slug"]], key=lambda p: p["name"])
        if not items:
            continue
        seo = read_seo(content / "seo" / f"{cat['slug']}.yml")
        ser = defaultdict(int)
        for p in items:
            if p["series"]:
                ser[p["series"]] += 1
        dvc = defaultdict(int)
        for p in items:
            for v in p["substances"]:
                dvc[v] += 1
        quick = [dict(label="Серии", group="series", items=[dict(name=n, value=n) for n, c in sorted(ser.items()) if c >= 2]),  # ПИ06: серия при ≥2 препаратах
                 dict(label="Задачи защиты", group="action",
                      items=[dict(name="Сплошного действия", value="sploshnoy")] if any(p["action_character"] == "sploshnoy" for p in items) else []),
                 dict(label="Действующее вещество", group="dv",
                      items=[dict(name="ДВ: " + subs[v]["name"], value=v) for v, c in sorted(dvc.items(), key=lambda kv: -kv[1])[:5]])]
        listing(f"catalog/{cat['slug']}/index.html", items, cat["name"], cat["name"], ["dv", "crop", "pest", "maker", "action"], quick,
                title=seo.get("meta", {}).get("title") or f"{cat['name']} — купить в Челябинске | Восток АгроХим",
                description=seo.get("meta", {}).get("description") or seo.get("lead", ""), lead=seo.get("lead", ""), seo=seo.get("seo"),
                other_cats=[c for c in cats if c["slug"] != cat["slug"]])

    # Страницы входов: культура, вредный объект, ДВ (ДМ02). Страница есть, только если на ней есть опубликованный препарат.
    def short(p):
        return p["name"].split(",")[0].strip()

    def crop_keys(slug):  # культура вместе с родителем и подвидами, как в проверке SEO-текстов
        return {slug, crops[slug]["parent"]} - {""} | {k for k, v in crops.items() if v["parent"] == slug}

    entries = [("kultura", crops, lambda p, slug: bool(crop_keys(slug) & set(p["crops"])), "для", "crop"),
               ("vrednyy-obekt", pests, lambda p, slug: slug in p["pests"], "против", "pest"),
               ("dv", subs, lambda p, slug: slug in p["substances"], "на основе", "dv")]
    built = {k: {} for k, *_ in entries}  # собранные страницы входов: slug -> число препаратов
    for kind, dct, has, prep, own in entries:
        for slug, row in dct.items():
            if slug in RESERVED:
                sys.exit(f"Адрес {slug} ({kind}) совпадает с зарезервированным словом")
            items = sorted([p for p in products if has(p, slug)], key=lambda p: p["name"])
            if not items:
                continue
            gen = row.get("name_gen") or row["name"].lower()
            if not row.get("name_gen"):
                warnings.append(f"{kind}/{slug}: нет родительного падежа (name_gen) в словаре")
            present = [c for c in cats if any(p["category"] == c["slug"] for p in items)]
            names = [c["name"] if i == 0 else c["name"].lower() for i, c in enumerate(present)]
            lead = f"{', '.join(names[:-1])} и {names[-1]}" if len(names) > 1 else names[0]
            lead += f" {prep} {gen}."
            seo = read_seo(content / "seo" / kind / f"{slug}.yml").get("seo")
            auto = None
            if seo and any(sec.get("products") == "auto" for sec in seo["sections"]):
                if kind == "dv":  # состав каждого препарата — из products.csv
                    auto = dict(kind="dv", items=[dict(name=short(p), url=p["url"], dv_text=p["dv_text"]) for p in sorted(items, key=short)])
                else:  # не больше 3 названий на категорию, остальные — «и другие» (полный список в сетке выше)
                    auto = dict(kind="groups", items=[dict(name=c["name"], more=len(ps) > 3, items=[dict(name=short(p), url=p["url"]) for p in sorted(ps, key=short)[:3]])
                                                      for c in present for ps in [[p for p in items if p["category"] == c["slug"]]]])
            built[kind][slug] = len(items)
            h1 = f"Препараты {prep} {gen}"
            listing(f"catalog/{kind}/{slug}/index.html", items, h1, h1, ["cat"] + [k for k in ("dv", "crop", "pest") if k != own] + ["maker", "action"],
                    [dict(label="Категория", group="cat", items=[dict(name=c["name"], value=c["slug"]) for c in present] if len(present) > 1 else [])],
                    title=f"{h1} — купить в Челябинске | Восток АгроХим",
                    description=f"{lead} Отгрузка под заявку, доставка по РФ и самовывоз в Челябинске.", lead=lead, seo=seo, auto=auto,
                    other_title="Категории каталога")

    # Обзорные страницы входов и узлы вредных объектов (ДМ02, ДМ26): плитки только собранных страниц
    def tile(kind, slug, name, subs_=()):
        n = built[kind][slug]
        return dict(name=name, url=f"/catalog/{kind}/{slug}/", count=f"{n} {word_preparat(n)}", subs=list(subs_))

    def overview(rel, h1, lead, groups, words, crumbs=(), n=None):
        groups = [g for g in groups if g["tiles"]]
        if not groups:
            return False
        n = n or sum(len(g["tiles"]) for g in groups)  # у культур считаются и подвиды
        write(rel, env.get_template("overview.html").render(
            **common, title=f"{h1} — купить в Челябинске | Восток АгроХим",
            description=f"{lead} Отгрузка под заявку, доставка по РФ и самовывоз в Челябинске.",
            canonical="/" + rel.removesuffix("index.html"), h1=h1, lead=lead, crumbs=list(crumbs), groups=groups,
            count=f"{n} {plural(n, words)}", other_cats=[c for c in cats if any(p["category"] == c["slug"] for p in products)]))
        return True

    # Культуры: по группам словаря, подвиды — под родителем («Пшеница» → озимая, яровая)
    cgroups = {}
    for slug, row in crops.items():
        if slug in built["kultura"] and not row["parent"]:
            sub = [dict(name=r["name"].removeprefix(row["name"]).strip().lower() if r["name"].startswith(row["name"] + " ") else r["name"],
                        url=f"/catalog/kultura/{k}/") for k, r in crops.items() if r["parent"] == slug and k in built["kultura"]]
            cgroups.setdefault(row["group"] or "Другие культуры", []).append(tile("kultura", slug, row["name"], sub))
    overview("catalog/kultura/index.html", "Препараты по культурам",
             "Выберите культуру — на её странице собраны все препараты каталога для неё.",
             [dict(title=k, tiles=v) for k, v in cgroups.items()], ("культура", "культуры", "культур"), n=len(built["kultura"]))

    # Вредные объекты: узлы по подтипу и общий обзор из трёх разделов
    hubs = [("sornyaki", "sornyak", "Сорняки", "сорняков", "Выберите сорняк — на его странице собраны препараты каталога против него.", ("сорняк", "сорняка", "сорняков")),
            ("vrediteli", "vreditel", "Вредители", "вредителей", "Выберите вредителя — на его странице собраны препараты каталога против него.", ("вредитель", "вредителя", "вредителей")),
            ("bolezni", "bolezn", "Болезни", "болезней", "Выберите болезнь — на её странице собраны препараты каталога против неё.", ("болезнь", "болезни", "болезней"))]
    sections = []
    for hub, typ, title, gen, lead, words in hubs:
        tiles = [tile("vrednyy-obekt", k, r["name"]) for k, r in pests.items() if r["type"] == typ and k in built["vrednyy-obekt"]]
        ok = overview(f"catalog/vrednyy-obekt/{hub}/index.html", f"Препараты против {gen}", lead, [dict(title="", tiles=tiles)], words,
                      [dict(name="Вредные объекты", url="/catalog/vrednyy-obekt/")])
        sections.append(dict(title=title, tiles=tiles, more=dict(name=f"Все {title.lower()} →", url=f"/catalog/vrednyy-obekt/{hub}/") if ok else None))
    overview("catalog/vrednyy-obekt/index.html", "Препараты против вредителей, сорняков и болезней",
             "Выберите сорняк, вредителя или болезнь — на странице объекта собраны препараты каталога против него.",
             sections, ("вредный объект", "вредных объекта", "вредных объектов"))

    # ДВ: по химическим классам (ПИ09), ПАВ и прочие не-пестициды — в конце
    dgroups = defaultdict(list)
    for slug, row in subs.items():
        if slug in built["dv"]:
            dgroups[(row["kind"] != "pestitsid", row["chem_class"] or "Другие вещества")].append(tile("dv", slug, row["name"]))
    overview("catalog/dv/index.html", "Препараты по действующим веществам",
             "Вещества сгруппированы по химическим классам. На странице вещества — все препараты каталога на его основе.",
             [dict(title=k[1], tiles=sorted(v, key=lambda x: x["name"].lower())) for k, v in sorted(dgroups.items())],
             ("действующее вещество", "действующих вещества", "действующих веществ"))

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
    # Плитка задачи ведёт на узел объектов; пока узла нет — на категорию, иначе в корень каталога
    done = {"/" + r.removesuffix("index.html") for r in pages}
    fallback = {"/catalog/vrednyy-obekt/sornyaki/": "/catalog/gerbitsidy/", "/catalog/vrednyy-obekt/vrediteli/": "/catalog/insektitsidy/",
                "/catalog/vrednyy-obekt/bolezni/": "/catalog/fungitsidy/"}
    for t in hp.get("tasks", []):
        if t["href"] in fallback and t["href"] not in done:
            t["href"] = fallback[t["href"]] if fallback[t["href"]] in done else "/catalog/"
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
