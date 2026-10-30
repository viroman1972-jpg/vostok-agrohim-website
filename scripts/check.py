"""Автопроверки собранного сайта. Код возврата 1, если есть нарушения.
Использование: check.py [папка] [--staging | --release]   |   check.py --selftest
--staging: дополнительно проверить, что тестовая копия закрыта от индексации.
--release: боевой сайт — картинки только с правом использования (журнал ДЗ09, статус «разрешено» или «своё»).
Кроме собранных страниц проверяются исходные SEO-тексты content/seo (правило 4: названия препаратов — по таблице связей)."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STOP_PHRASES = [  # (шаблон, причина)
    (r"прямые\s+дистрибьютор", "«Прямые дистрибьюторы» запрещено (риск по 38-ФЗ)"),
    (r"гарантия\s+производителя\s+на\s+всю", "формулировка гарантии запрещена (ДЗ10)"),
    (r"продолжая\s+использовать", "в баннере cookie нельзя «продолжая использовать — соглашаетесь» (ДЗ08)"),
    (r"щ[её]лково", "Щёлково Агрохим не упоминается (НР05)"),
    (r"/opt\b|/oferta/|/dacha", "отменённые страницы /opt, /oferta/, /dacha (НР01, НР13, НР14)"),
    (r"telegram[-\s]?бот", "Telegram-бот отменён (НР12)"),
    (r"в\s+наличии|под\s+заказ", "индикатор наличия запрещён (ПИ11)"),
    (r"google-analytics|googletagmanager|gtag\(", "GA4 не используется (О8)"),
    (r"docs\.google\.com/forms|script\.google\.com", "Google Sheet/Forms для заявок запрещены (НР17)"),
]
EXTERNAL = re.compile(r"""(?:<(?:script|img|iframe|source)\b[^>]*\bsrc|<link\b[^>]*\bhref|<form\b[^>]*\baction)\s*=\s*["'](https?:)?//""", re.I)
CSS_URL = re.compile(r"url\(\s*['\"]?(https?:)?//", re.I)

# Страницы, которые ещё не собраны (по site-structure-v1.md). Ссылки на них допустимы до своего этапа.
# Страницы культур, объектов и ДВ уже собираются — допустимы только ссылки на их ещё не собранные обзорные страницы.
PLANNED_EXACT = {"/catalog/kultura/", "/catalog/vrednyy-obekt/", "/catalog/dv/", "/catalog/vrednyy-obekt/sornyaki/",
                 "/catalog/vrednyy-obekt/vrediteli/", "/catalog/vrednyy-obekt/bolezni/"}
PLANNED = ("/catalog/seriya/", "/contacts/", "/about/",
           "/comments/", "/sitemap/", "/privacy-policy/", "/send.php", "/catalog/insektitsidy/", "/catalog/fungitsidy/",
           "/catalog/protraviteli/", "/catalog/stimulyatory-rosta/", "/catalog/adyuvanty/", "/catalog/desikanty/")
HREF = re.compile(r"""<a\b[^>]*\bhref\s*=\s*["'](/[^"'#?]*)""", re.I)
PRICE_VIS = re.compile(r'class="price">\s*([\d\s ]+)\s*₽')
IMG_REF = re.compile(r"""(?:src|data-front|data-back)\s*=\s*["']/static/(img/[^"']+?)(?:-\d+)?\.(?:webp|svg|jpe?g|png)["']""", re.I)
JOURNAL = ROOT / "assets" / "image-sources.csv"
STATUSES = {"разрешено", "своё", "ожидает", "уточнить"}  # первые два допустимы на боевом сайте (ДЗ09)
RELEASE_OK = {"разрешено", "своё"}
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
# Названия, которых не должно быть в SEO-текстах: исключённые из каталога и встречавшиеся в волнах, но не продаваемые
SEO_OFF = {"Ректор": "исключён (У02)", "Альфацин": "исключён (У03)", "Лазурит Ультра": "исключён (У04)",
           "Лигногумат": "исключён (У05)", "Тиара": "исключена (У06)", "Лемур": "исключён до новой регистрации (У08)",
           "Шаман": "исключён до новой регистрации (У08)", "Табу Супер": "нет в каталоге", "Бицепс": "нет в каталоге",
           "Дублон": "нет в каталоге"}


def link_exists(root, href):
    p = root / href.lstrip("/")
    return p.is_file() or (p / "index.html").is_file()


def check_file(path, text, root=None):
    errs = []
    # цена на странице = цена в разметке Offer
    for m in LD.finditer(text):
        try:
            ld = json.loads(m.group(1))
        except ValueError:
            errs.append(f"{path}: разметка ld+json не читается"); continue
        if ld.get("@type") == "Product":
            shown = PRICE_VIS.search(text)
            offer = str(ld.get("offers", {}).get("price", ""))
            if not shown or re.sub(r"\D", "", shown.group(1)) != offer:
                errs.append(f"{path}: цена на странице не равна цене в разметке ({shown.group(1).strip() if shown else 'нет'} и {offer})")
    if root is not None:
        for href in sorted(set(HREF.findall(text))):
            if not link_exists(root, href) and not href.startswith(PLANNED) and href not in PLANNED_EXACT | {"/catalog/"}:
                errs.append(f"{path}: битая ссылка {href}")
    low = text.lower()
    for pat, why in STOP_PHRASES:
        if re.search(pat, low):
            errs.append(f"{path}: {why}")
    text_ext = re.sub(r'<link rel="canonical"[^>]*>', "", text)  # canonical — не загрузка чужого ресурса
    if EXTERNAL.search(text_ext) or CSS_URL.search(text_ext):
        errs.append(f"{path}: запрос к чужому серверу (шрифты, скрипты и картинки только свои)")
    for m in re.finditer(r"<input\b[^>]*type\s*=\s*[\"']checkbox[\"'][^>]*>", text, re.I):
        tag = m.group(0)
        if re.search(r"\bchecked\b", tag, re.I):
            errs.append(f"{path}: галочка согласия отмечена заранее (ДЗ07)")
        if "consent" in tag.lower() and not re.search(r"\brequired\b", tag, re.I):
            errs.append(f"{path}: галочка согласия не обязательна (ДЗ07)")
    for m in re.finditer(r"<img\b[^>]*>", text, re.I):
        if not re.search(r"\balt\s*=\s*[\"'][^\"']+[\"']", m.group(0), re.I):
            errs.append(f"{path}: картинка без alt (ДЗ09)")
    if "<form" in low and "обработк" not in low:
        errs.append(f"{path}: у формы нет указания цели обработки данных (ДЗ07)")
    return errs


def read_journal(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["file"]: r for r in csv.DictReader(fh)}


def check_images(path, text, journal, release):
    errs = []
    for key in sorted(set(IMG_REF.findall(text))):
        r = journal.get(key)
        if r is None:
            errs.append(f"{path}: картинка {key} не записана в журнал источников (ДЗ09)")
        elif r["status"] not in STATUSES:
            errs.append(f"{path}: у картинки {key} неизвестный статус «{r['status']}» в журнале")
        elif release and r["status"] not in RELEASE_OK:
            errs.append(f"{path}: картинка {key} без права использования на боевом сайте (статус «{r['status']}», ДЗ09)")
    return errs


def check_dir(d, staging=False, release=False, journal=JOURNAL):
    errs, n = [], 0
    jr = read_journal(journal)
    for f in sorted(Path(d).rglob("*.html")):
        n += 1
        text = f.read_text(encoding="utf-8")
        errs += check_file(f.relative_to(d), text, Path(d))
        errs += check_images(f.relative_to(d), text, jr, release)
        if staging and 'name="robots" content="noindex' not in text:
            errs.append(f"{f.relative_to(d)}: тестовая копия не закрыта от индексации (нет noindex)")
    if n == 0:
        errs.append(f"{d}: нет ни одной html-страницы")
    if staging and "Disallow: /\n" not in ((Path(d) / "robots.txt").read_text(encoding="utf-8") if (Path(d) / "robots.txt").is_file() else ""):
        errs.append(f"{d}: тестовая копия без robots.txt с запретом индексации")
    return errs, n


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def name_forms(name):
    """Шаблон названия с падежными окончаниями первого слова: Балерина → Балерину, Хакер → Хакером, Колосаль → Колосаля."""
    first, sep, rest = name.partition(" ")
    if first[-1] in "ая":
        w = re.escape(first[:-1]) + "(?:а|я|ы|и|е|у|ю|ой|ей)"
    elif first[-1] == "ь":
        w = re.escape(first[:-1]) + "(?:ь|я|ю|ем|е)"
    elif re.match(r"[бвгджзклмнпрстфхцчшщ]", first[-1]):
        w = re.escape(first) + "(?:а|у|ом|е)?"
    else:
        w = re.escape(first)
    return w + re.escape(sep + rest)


def check_seo(root=ROOT):
    """Правило 4: препарат в тексте страницы культуры, объекта или ДВ — только если он есть в таблице связей этой страницы.
    Культура учитывает родителя и подвиды (у яровой пшеницы — связи «пшеницы»)."""
    errs = []
    data, seo = Path(root) / "data", Path(root) / "content" / "seo"
    slug_by_name = {p["name"].split(",")[0].strip(): p["slug"] for p in read_csv(data / "products.csv")}
    names = sorted(set(slug_by_name) | set(SEO_OFF), key=len, reverse=True)  # длинные первыми: «Балерина Форте», не «Балерина»
    pats = [(n, re.compile(r"(?<![А-Яа-яЁё])" + name_forms(n) + r"(?![А-Яа-яЁё])")) for n in names]
    crops = {r["slug"]: r for r in read_csv(data / "dict" / "crops.csv")}
    kinds = {"kultura": ("crops.csv", "product_crop.csv", "crop"), "vrednyy-obekt": ("pests.csv", "product_pest.csv", "pest"),
             "dv": ("substances.csv", "product_substance.csv", "substance")}
    for kind, (dict_file, link_file, col) in kinds.items():
        known = {r["slug"] for r in read_csv(data / "dict" / dict_file)}
        links = read_csv(data / "links" / link_file)
        for f in sorted((seo / kind).glob("*.yml")):
            rel = f.relative_to(root)
            if f.stem not in known:
                errs.append(f"{rel}: страницы {f.stem} нет в словаре {dict_file}"); continue
            keys = {f.stem}
            if kind == "kultura":
                keys |= {k for k, v in crops.items() if v["parent"] == f.stem}
                if crops[f.stem]["parent"]:
                    keys.add(crops[f.stem]["parent"])
            linked = {r["slug"] for r in links if r[col] in keys}
            text, found = f.read_text(encoding="utf-8"), set()
            for n, p in pats:  # найденное вырезается, чтобы «Балерина Форте» не засчиталась ещё и как «Балерина»
                text, k = p.subn("§", text)
                if k:
                    found.add(n)
            for n in sorted(found):
                if n in SEO_OFF:
                    errs.append(f"{rel}: {n} — {SEO_OFF[n]}")
                elif slug_by_name[n] not in linked:
                    errs.append(f"{rel}: {n} — нет связи с этой страницей в {link_file} (правило 4)")
    return errs


def selftest():
    bad, _ = check_dir(ROOT / "tests" / "bad", staging=True, journal=ROOT / "tests" / "image-sources.csv")
    bad += check_dir(ROOT / "tests" / "bad", release=True, journal=ROOT / "tests" / "image-sources.csv")[0]
    seo = check_seo(ROOT / "tests" / "seo")
    bad += seo
    expected = ["не записана в журнал", "неизвестный статус", "без права использования", "Прямые дистрибьюторы", "гарантии", "cookie", "Щёлково", "наличия", "чужому серверу", "заранее", "не обязательна", "без alt", "GA4", "цена на странице", "битая ссылка /catalog/gerbitsidy/", "битая ссылка /catalog/kultura/",
                "нет noindex", "без robots.txt", "Миура — нет связи", "Тиара — исключена","Бицепс — нет в каталоге", "нет в словаре"]
    missing = [e for e in expected if not any(e in x for x in bad)]
    if any("Балерина" in x for x in seo):  # связь через родительскую культуру — не нарушение
        missing.append("ложное срабатывание на Балерину (связь через «пшеницу»)")
    if missing:
        print("SELFTEST ПРОВАЛЕН, проверки не поймали:", ", ".join(missing)); return 1
    print(f"selftest ок: на плохом примере поймано {len(bad)} нарушений"); return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # консоль Windows (cp1251) не печатает ✗
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = Path(args[0]) if args else ROOT / "dist"
    errs, n = check_dir(d, staging="--staging" in sys.argv, release="--release" in sys.argv)
    errs += check_seo()
    for e in errs: print("✗", e)
    print(f"Проверено страниц: {n}, нарушений: {len(errs)}")
    sys.exit(1 if errs else 0)
