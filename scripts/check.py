"""Автопроверки собранного сайта. Код возврата 1, если есть нарушения.
Использование: check.py [папка] [--staging | --release]   |   check.py --selftest
--staging: дополнительно проверить, что тестовая копия закрыта от индексации.
--release: боевой сайт — картинки только с правом использования (журнал ДЗ09, статус «разрешено» или «своё»).
Кроме собранных страниц проверяются исходные SEO-тексты content/seo (правило 4: названия препаратов — по таблице связей)."""
import csv, json, re, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

STOP_PHRASES = [  # (шаблон, причина)
    (r"прямые\s+дистрибьютор", "«Прямые дистрибьюторы» запрещено (риск по 38-ФЗ)"),
    (r"гарантия\s+производителя\s+на\s+всю", "формулировка гарантии запрещена (ДЗ10)"),
    (r"продолжая\s+использовать", "в баннере cookie нельзя «продолжая использовать — соглашаетесь» (ДЗ08)"),
    (r"щ[её]лково", "Щёлково Агрохим не упоминается (НР05)"),
    (r"/opt\b|/oferta/|/dacha", "отменённые страницы /opt, /oferta/, /dacha (НР01, НР13, НР14)"),
    (r"telegram[-\s]?бот", "Telegram-бот отменён (НР12)"),
    (r"/return-policy|/price/|/legal/", "отменённые страницы /return-policy/, /price/, /legal/ (НР20, П07, НР19)"),
    (r"лигногумат|деразал", "препарата нет в каталоге (У05, отзывы)"),
    (r"в\s+наличии|под\s+заказ", "индикатор наличия запрещён (ПИ11)"),
    (r"google-analytics|googletagmanager|gtag\(", "GA4 не используется (О8)"),
    (r"docs\.google\.com/forms|script\.google\.com", "Google Sheet/Forms для заявок запрещены (НР17)"),
]
EXTERNAL = re.compile(r"""(?:<(?:script|img|iframe|source)\b[^>]*\bsrc|<link\b[^>]*\bhref|<form\b[^>]*\baction)\s*=\s*["'](https?:)?//""", re.I)
CSS_URL = re.compile(r"url\(\s*['\"]?(https?:)?//", re.I)

# Страницы, которые ещё не собраны (по site-structure-v1.md). Ссылки на них допустимы до своего этапа.
# Страницы входов (культуры, объекты, ДВ, их обзорные и узлы) собираются — ссылка на несобранную считается битой.
PLANNED = ("/catalog/insektitsidy/", "/catalog/fungitsidy/",
           "/catalog/protraviteli/", "/catalog/stimulyatory-rosta/", "/catalog/adyuvanty/")
HREF = re.compile(r"""<a\b[^>]*\bhref\s*=\s*["'](/[^"'#?]*)""", re.I)
PRICE_VIS = re.compile(r'class="price">\s*([\d\s ]+)\s*₽')
IMG_REF = re.compile(r"""(?:src|data-front|data-back)\s*=\s*["']/static/(img/[^"']+?)(?:-\d+)?\.(?:webp|svg|jpe?g|png)["']""", re.I)
JOURNAL = ROOT / "assets" / "image-sources.csv"
STATUSES = {"разрешено", "своё", "ожидает", "уточнить"}  # первые два допустимы на боевом сайте (ДЗ09)
RELEASE_OK = {"разрешено", "своё"}
REQUIRED = ("catalog/all/index.html", "about/index.html", "contacts/index.html", "comments/index.html", "privacy-policy/index.html", "sitemap/index.html", "404.html")  # план §2.4
PRICE_FILE = "files/prays-list.pdf"  # П07
# Политика (чек-лист D, ДЗ08): без этих разделов страница не проходит
POLICY_MUST = ("Оператор персональных данных", "Цели обработки", "Правовые основания", "хранятся", "Ваши права", "Отозвать согласие", "cookie", "Яндекс.Метрика", "Редакция от")
# Отзывы (ДЗ04, ДЗ06, B.9): стоп-слова, непроверяемые обещания, упоминание физлиц. Имён авторов здесь нет намеренно — это персональные данные
COMMENTS_OFF = r"безопасн|безвредн|экологичн|100\s*%|гарантированн|физлиц|физическ\w+ лиц|частн\w+ лиц"
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
            if not link_exists(root, href) and not href.startswith(PLANNED):
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
    # Быстрые входы по ДВ (ДМ32): ссылка на страницу вещества, а не фильтр
    if re.search(r"<button\b[^>]*\bqpill\b[^>]*\bdata-group=[\"']dv[\"']", text, re.I):
        errs.append(f"{path}: быстрый вход по ДВ — фильтр вместо ссылки (ДМ32)")
    # Кнопка-фильтр (ДМ32) отмечает галочку боковой панели: без неё кнопка ничего не делает
    for m in re.finditer(r"<button\b[^>]*\bqpill\b[^>]*\bdata-group=\"(\w+)\"[^>]*\bdata-value=\"([^\"]*)\"", text, re.I):
        for v in m.group(2).split():
            if f'type="checkbox" data-group="{m.group(1)}" value="{v}"' not in text:
                errs.append(f"{path}: кнопка-фильтр {m.group(1)}={v} — нет галочки в боковой панели (ДМ32)")
    # Группы «Категория» и «Упаковка» — только при двух и более значениях (ДМ32)
    for group, title in (("cat", "Категория"), ("pack", "Упаковка")):
        if len(re.findall(rf'type="checkbox" data-group="{group}"', text)) == 1:
            errs.append(f"{path}: фильтр «{title}» с одним значением (ДМ32)")
    # Панель фильтров (ДМ23): под кнопкой «Ещё фильтры (N)» ровно эти группы, N — их число на странице
    extra = 0
    for m in re.finditer(r'<div class="fgroup( extra)?" data-group="(\w+)"( hidden)?>', text):
        want = m.group(2) in ("action", "term", "pack", "price")
        extra += bool(m.group(1) and m.group(3))
        if want != bool(m.group(1) and m.group(3)):
            errs.append(f"{path}: группа {m.group(2)} " + ("развёрнута, а должна быть под кнопкой «Ещё фильтры» (ДМ23)" if want else "под кнопкой «Ещё фильтры», а должна быть развёрнута (ДМ23)"))
    more = re.search(r'id="more-filters"[^>]*>Ещё фильтры \((\d+)\)', text)
    if extra and (not more or int(more.group(1)) != extra):
        errs.append(f"{path}: на кнопке «Ещё фильтры» не то число групп (ДМ23)")
    # Сценарные входы (ДМ31): кнопка открывает форму, а тип территории уходит в заявку
    for m in re.finditer(r"<button\b[^>]*\bdata-territory\b[^>]*>", text, re.I):
        if "data-open-lead" not in m.group(0):
            errs.append(f"{path}: вход по территории не открывает форму заявки (ДМ31)")
        if 'name="territory"' not in text:
            errs.append(f"{path}: вход по территории, но в форме нет поля territory (ДМ31)")
    if "<form" in low and "обработк" not in low:
        errs.append(f"{path}: у формы нет указания цели обработки данных (ДЗ07)")
    errs += check_lead(path, text)
    errs += check_related(path, text)
    return errs


def check_lead(path, text):
    """Форма заявки (ДМ35, ДЗ07, план §2.6): уходит в send.php, скрытые поля для письма, ловушка, телефон на случай сбоя и после успеха."""
    m = re.search(r'<form\b[^>]*\bid="lead-form"[^>]*>(.*?)</form>', text, re.S)
    if not m:
        return []
    errs, tag, body = [], m.group(0)[:m.group(0).index(">") + 1], m.group(1)
    if 'action="/send.php"' not in tag or 'method="post"' not in tag:
        errs.append(f"{path}: форма заявки не отправляется в /send.php методом POST")
    for f in ("product", "territory", "page"):
        if not re.search(rf'<input type="hidden" name="{f}"', body):
            errs.append(f"{path}: в форме заявки нет скрытого поля {f} (план §2.6)")
    if not re.search(r'class="hp"[^>]*>.*?name="website"', body, re.S):
        errs.append(f"{path}: в форме заявки нет поля-ловушки (ДМ35 п. 6)")
    if not re.search(r'id="lead-err"[^>]*>.*?href="tel:', body, re.S):
        errs.append(f"{path}: при сбое отправки форма не показывает телефон (план §2.6)")
    if not re.search(r'id="lead-done"[^>]*>.*?Если не ответим в течение рабочего дня, позвоните.*?href="tel:', text, re.S):
        errs.append(f"{path}: после заявки нет «Если не ответим в течение рабочего дня, позвоните» с телефоном (ДМ35 п. 5)")
    return errs


def check_send(d, has_form):
    """send.php (этап 4): есть, если на сайте форма; согласие проверяется на сервере; нет пароля и неподставленных значений."""
    f = Path(d) / "send.php"
    if not f.is_file():
        return [f"{d}: на сайте форма заявки, а send.php нет"] if has_form else []
    t, errs = f.read_text(encoding="utf-8"), []
    if "%%" in t:
        errs.append("send.php: не подставлены телефоны или адрес из settings.yml")
    if not re.search(r"if \(!\$consent\) \{\s*journal\([^;]*\);\s*answer\(422, 'consent'\)", t):
        errs.append("send.php: заявка без галочки согласия не отклоняется на сервере (ДЗ07)")
    for must, why in (("field('website')", "нет проверки поля-ловушки (ДМ35 п. 6)"), ("rate_ok(", "нет ограничения частоты (ДМ35 п. 6)"),
                      ("vostok-private/send-config.php", "настройки не вне папки сайта (план §2.5)"), ("answer(502, 'send')", "сбой отправки не сообщается посетителю (план §2.6)")):
        if must not in t:
            errs.append(f"send.php: {why}")
    if re.search(r"""['"]smtp_pass['"]\s*=>\s*['"][^'"]""", t) or re.search(r"(?i)password\s*=", t):
        errs.append("send.php: пароль почты в файле сайта — только в настройках на хостинге")
    if re.search(r"google|sheets|telegram|api\.", t, re.I):
        errs.append("send.php: заявка уходит в зарубежный сервис или Telegram (НР17)")
    return errs


def check_service(d, release):
    """Служебные страницы (план §2.4): все на месте, политика полная, отзывы по ДЗ06, карта сайта ведёт на все страницы, 404 настроена, прайс есть к запуску."""
    d, errs = Path(d), []
    for rel in REQUIRED:
        if not (d / rel).is_file():
            errs.append(f"{d}: нет обязательной страницы {rel}")
    f = d / "privacy-policy" / "index.html"
    if f.is_file():
        text = f.read_text(encoding="utf-8")
        for must in POLICY_MUST:
            if must.lower() not in text.lower():
                errs.append(f"privacy-policy: в политике нет раздела «{must}» (чек-лист D)")
    f = d / "comments" / "index.html"
    if f.is_file():
        body = re.search(r"<main.*?</main>", f.read_text(encoding="utf-8"), re.S)
        for m in re.finditer(COMMENTS_OFF, body.group(0).lower() if body else "", re.I):
            errs.append(f"comments: недопустимое в отзыве «{m.group(0)}» (ДЗ04, ДЗ06, B.9)")
    f = d / "sitemap" / "index.html"
    if f.is_file():
        linked = set(HREF.findall(re.search(r"<main.*?</main>", f.read_text(encoding="utf-8"), re.S).group(0)))
        for page in sorted(d.rglob("*.html")):
            rel = page.relative_to(d).as_posix()
            url = "/" + rel.removesuffix("index.html")
            if rel not in ("404.html", "sitemap/index.html") and url not in linked:
                errs.append(f"sitemap: нет ссылки на страницу {url} (ДМ19)")
    ht = d / ".htaccess"
    if not ht.is_file() or "ErrorDocument 404 /404.html" not in ht.read_text(encoding="utf-8"):
        errs.append(f"{d}: страница 404 не настроена в .htaccess")
    nf = d / "404.html"
    if nf.is_file() and 'name="robots" content="noindex' not in nf.read_text(encoding="utf-8"):
        errs.append("404.html: страница не закрыта от индексации")
    if release and not (d / PRICE_FILE).is_file():
        errs.append(f"{d}: нет файла прайса {PRICE_FILE} (П07)")
    f = d / "index.html"
    if f.is_file():
        text = f.read_text(encoding="utf-8")
        if 'class="sticky-cta"' in text:
            errs.append("index.html: нижняя кнопка на главной (ДМ37)")
        if 'class="hero-phones"' not in text:
            errs.append("index.html: нет телефонов в первом экране (ДМ37)")
    return errs


def check_search(d):
    """Поиск (ДМ38): значок, поле в меню и номер в шапке на всех страницах; в индексе только собранные страницы и нет цен; индекс совпадает со списком /catalog/all/, закрытым от индексации."""
    d, errs = Path(d), []
    for f in sorted(d.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(d)
        header = re.search(r"<header.*?</header>", text, re.S)
        header = header.group(0) if header else ""
        if 'id="search-open"' not in header or "data-search" not in header:
            errs.append(f"{rel}: в шапке нет значка или поля поиска (ДМ38)")
        if 'class="p1"' not in header:
            errs.append(f"{rel}: в шапке нет номера телефона (ДМ37, ДМ38)")
    f = d / "static" / "search-index.json"
    if not f.is_file():
        return errs + [f"{d}: нет индекса поиска static/search-index.json (ДМ38)"]
    raw = f.read_text(encoding="utf-8")
    if "₽" in raw or re.search(r'"price', raw):
        errs.append("search-index.json: в индексе поиска цена — цена попадает на страницу только при сборке (ДМ38)")
    index = json.loads(raw)
    for x in index["products"] + index["sections"]:
        if not link_exists(d, x["url"]):
            errs.append(f"search-index.json: индекс ведёт на несобранную страницу {x['url']} (ДМ38)")
    f = d / "catalog" / "all" / "index.html"
    if f.is_file():
        text = f.read_text(encoding="utf-8")
        if 'name="robots" content="noindex' not in text:
            errs.append("catalog/all: страница не закрыта от индексации (ДМ38)")
        cards = set(re.findall(r'<a class="card" href="([^"]+)"', text))
        if cards != {p["url"] for p in index["products"]}:
            errs.append("catalog/all: список карточек не совпадает с индексом поиска (ДМ38)")
    return errs


def check_related(path, text):
    """«Похожие подборки» (ДМ32): только на листинге категории, между SEO-текстом и «Другими категориями», ссылки не из быстрых входов; состав — по культурам карточек этой страницы."""
    errs = []
    parts = Path(path).parts
    is_cat = len(parts) == 3 and parts[0] == "catalog" and parts[2] == "index.html" and parts[1] not in ("kultura", "vrednyy-obekt", "dv", "seriya", "all")
    m = re.search(r'<div class="related">.*?</div>', text, re.S)
    links = re.findall(r'href="([^"]*)"', m.group(0)) if m else []
    if m:
        if not is_cat:
            errs.append(f"{path}: блок «Похожие подборки» только на листинге категории (ДМ32)")
        other, seo = text.find('<div class="other">'), text.find('<div class="seo">')
        if not m.start() < other or m.start() < seo:
            errs.append(f"{path}: блок «Похожие подборки» не на месте — нужен между SEO-текстом и «Другими категориями» (ДМ32)")
        quick = re.search(r'id="quick">(.*?)<div class="bar"', text, re.S)
        for href in set(links) & set(re.findall(r'href="([^"]*)"', quick.group(1)) if quick else []):
            errs.append(f"{path}: блок «Похожие подборки» повторяет быстрый вход {href} (ДМ32)")
    if is_cat:
        crops = {r["slug"]: r for r in read_csv(ROOT / "data" / "dict" / "crops.csv")}
        cnt = {}
        for card in re.findall(r'\bdata-crop="([^"]*)"', text):  # препарат считается один раз, подвид — в родителе
            for k in {crops[v]["parent"] or v for v in card.split()}:
                if crops[k]["group"] != "Спец. объекты":
                    cnt[k] = cnt.get(k, 0) + 1
        order = list(crops)
        want = sorted(cnt, key=lambda k: (-cnt[k], order.index(k)))[:8] if len(cnt) >= 5 else []
        if links != [f"/catalog/kultura/{k}/" for k in want]:
            errs.append(f"{path}: состав блока «Похожие подборки» не совпадает с отбором по культурам (ДМ32)")
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


def check_css(d):
    """Адаптив: длинное слово или ряд кнопок не должны расширять страницу (проверка без браузера — только правила стилей)."""
    f = Path(d) / "static" / "site.css"
    if not f.is_file():
        return []
    css, errs = f.read_text(encoding="utf-8"), []
    if re.search(r"\.shell\{[^}]*grid-template-columns:(?:\d+px\s+)?1fr", css):
        errs.append("site.css: колонка .shell растягивается содержимым — нужен minmax(0,1fr)")
    if not re.search(r"(?:^|\n)h1,h2\{[^}]*overflow-wrap:anywhere", css):
        errs.append("site.css: длинное слово в заголовке не переносится — нет overflow-wrap:anywhere")
    return errs


def check_dir(d, staging=False, release=False, journal=JOURNAL):
    errs, n, has_form = [], 0, False
    jr = read_journal(journal)
    for f in sorted(Path(d).rglob("*.html")):
        n += 1
        text = f.read_text(encoding="utf-8")
        has_form = has_form or 'id="lead-form"' in text
        errs += check_file(f.relative_to(d), text, Path(d))
        errs += check_images(f.relative_to(d), text, jr, release)
        if re.search(r'class="sep">·</span>(?!<wbr>)', text):
            errs.append(f"{f.relative_to(d)}: крошки не переносятся — после разделителя нужен <wbr>")
        if staging and 'name="robots" content="noindex' not in text:
            errs.append(f"{f.relative_to(d)}: тестовая копия не закрыта от индексации (нет noindex)")
    if n == 0:
        errs.append(f"{d}: нет ни одной html-страницы")
    errs += check_service(d, release) + check_css(d) + check_search(d) + check_send(d, has_form)
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


def check_prom(root=ROOT):
    """Промышленные гербициды (ДМ31): тег promyshlennoe-primenenie стоит ровно у препаратов со связью «земли несельхозпользования»
    (госреестр), только у гербицидов; препарат, названный в тексте подраздела, должен быть с тегом."""
    errs, tag, land = [], "promyshlennoe-primenenie", "zemli-neselhozpolzovaniya"
    data = Path(root) / "data"
    products = read_csv(data / "products.csv")
    linked = {r["slug"] for r in read_csv(data / "links" / "product_crop.csv") if r["crop"] == land}
    tagged = set()
    for p in products:
        if tag in p["tags"].split():
            tagged.add(p["slug"])
            if p["category"] != "gerbitsidy":
                errs.append(f"products.csv: {p['slug']} — тег {tag} не у гербицида (ДМ31)")
    for s in sorted(tagged - linked):
        errs.append(f"products.csv: {s} — тег {tag} без связи «{land}» в product_crop.csv")
    for s in sorted(linked - tagged):
        errs.append(f"products.csv: {s} — связь «{land}» без тега {tag}")
    f = Path(root) / "content" / "seo" / "gerbitsidy-promyshlennye.yml"
    if f.exists():
        text = f.read_text(encoding="utf-8")
        by_name = {p["name"].split(",")[0].strip(): p["slug"] for p in products}
        for n in sorted(by_name, key=len, reverse=True):
            text, k = re.subn(r"(?<![А-Яа-яЁё])" + name_forms(n) + r"(?![А-Яа-яЁё])", "§", text)
            if k and by_name[n] not in tagged:
                errs.append(f"{f.relative_to(root)}: {n} — нет тега {tag} (ДМ31)")
    # Вкладки регламента: строка scope: prom — только у препарата с тегом; у препарата с тегом такая строка есть;
    # строка про земли несельхозназначения всегда с пометкой
    for p in products:
        cf = Path(root) / "content" / "products" / f"{p['slug']}.yml"
        rows = (yaml.safe_load(cf.read_text(encoding="utf-8")) or {}).get("regulation", []) if cf.exists() else []
        name = f"content/products/{p['slug']}.yml"
        for r in rows:
            if r.get("scope") not in (None, "prom"):
                errs.append(f"{name}: неизвестный scope «{r['scope']}» в регламенте (ДМ31)")
            if r.get("scope") == "prom" and p["slug"] not in tagged:
                errs.append(f"{name}: строка регламента scope: prom у препарата без тега {tag} (ДМ31)")
            if r["crop"].startswith("Земли несельскохозяйственного") and r.get("scope") != "prom":
                errs.append(f"{name}: земли несельхозназначения в регламенте без пометки scope: prom (ДМ31)")
        if rows and p["slug"] in tagged and not any(r.get("scope") == "prom" for r in rows):
            errs.append(f"{name}: тег {tag}, но в регламенте нет строк scope: prom (ДМ31)")
    return errs


def check_term(root=ROOT):
    """Довсходовые (ДМ32): тег dovskhodovyy стоит ровно у гербицидов, в регламенте которых есть применение до всходов (госреестр, ПИ10)."""
    errs, tag = [], "dovskhodovyy"
    for p in read_csv(Path(root) / "data" / "products.csv"):
        cf = Path(root) / "content" / "products" / f"{p['slug']}.yml"
        rows = (yaml.safe_load(cf.read_text(encoding="utf-8")) or {}).get("regulation", []) if cf.exists() else []
        has = any(re.search(r"до (?:появления )?всходов", str(r.get("method", ""))) for r in rows)
        tagged = tag in p["tags"].split()
        if tagged and p["category"] != "gerbitsidy":
            errs.append(f"products.csv: {p['slug']} — тег {tag} не у гербицида (ДМ32)")
        elif tagged and not has:
            errs.append(f"products.csv: {p['slug']} — тег {tag}, но в регламенте нет применения до всходов (ДМ32)")
        elif has and not tagged and p["category"] == "gerbitsidy":
            errs.append(f"products.csv: {p['slug']} — в регламенте применение до всходов, нет тега {tag} (ДМ32)")
        if p["category"] == "gerbitsidy" and tagged != ("довсходов" in p["drug_type"].lower()):
            errs.append(f"products.csv: {p['slug']} — тип применения расходится с тегом {tag} (ДМ32)")
    return errs


def selftest():
    bad, _ = check_dir(ROOT / "tests" / "bad", staging=True, journal=ROOT / "tests" / "image-sources.csv")
    bad += check_dir(ROOT / "tests" / "bad", release=True, journal=ROOT / "tests" / "image-sources.csv")[0]
    seo = check_seo(ROOT / "tests" / "seo")
    bad += seo + check_prom(ROOT / "tests" / "seo") + check_term(ROOT / "tests" / "seo") + check_send(ROOT / "tests" / "send-bad", True)
    expected = ["не записана в журнал", "неизвестный статус", "без права использования", "Прямые дистрибьюторы", "гарантии", "cookie", "Щёлково", "наличия", "чужому серверу", "заранее", "не обязательна", "без alt", "GA4", "цена на странице", "битая ссылка /catalog/gerbitsidy/", "битая ссылка /catalog/kultura/", "битая ссылка /catalog/vrednyy-obekt/vrediteli/", "битая ссылка /catalog/seriya/", "не открывает форму заявки", "нет поля territory", "фильтр вместо ссылки", "нет галочки в боковой панели", "«Категория» с одним значением",
                "«Упаковка» с одним значением", "развёрнута, а должна быть под кнопкой", "под кнопкой «Ещё фильтры», а должна быть развёрнута", "не то число групп", "только на листинге категории", "не на месте", "повторяет быстрый вход", "не совпадает с отбором", "balerina-se — тип применения расходится", "miura-ke — тип применения расходится",
                "тег dovskhodovyy не у гербицида", "нет применения до всходов", "нет тега dovskhodovyy",
                "нет noindex", "без robots.txt", "Миура — нет связи", "Тиара — исключена","Бицепс — нет в каталоге", "нет в словаре",
                "не у гербицида", "без связи", "без тега", "Миура — нет тега",
                "неизвестный scope", "scope: prom у препарата без тега", "без пометки scope: prom", "нет строк scope: prom",
                "нет обязательной страницы about", "отменённые страницы /return-policy/", "препарата нет в каталоге", "в политике нет раздела", "недопустимое в отзыве", "sitemap: нет ссылки", "404 не настроена", "404.html: страница не закрыта", "нет файла прайса",
                "колонка .shell растягивается", "длинное слово в заголовке", "крошки не переносятся", "нижняя кнопка на главной", "нет телефонов в первом экране",
                "нет обязательной страницы catalog/all", "нет значка или поля поиска", "в шапке нет номера телефона", "в индексе поиска цена", "индекс ведёт на несобранную страницу",
                "не отправляется в /send.php", "нет скрытого поля territory", "нет скрытого поля page", "нет поля-ловушки", "не показывает телефон", "«Если не ответим", "а send.php нет",
                "не подставлены телефоны", "без галочки согласия не отклоняется", "нет проверки поля-ловушки", "нет ограничения частоты", "настройки не вне папки сайта", "сбой отправки не сообщается", "пароль почты в файле сайта"]
    missing = [e for e in expected if not any(e in x for x in bad)]
    if any("Балерина" in x for x in seo):  # связь через родительскую культуру — не нарушение
        missing.append("ложное срабатывание на Балерину (связь через «пшеницу»)")
    if not any(x.endswith("битая ссылка /catalog/") for x in bad):  # корень каталога без исключения
        missing.append("битая ссылка /catalog/")
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
    errs += check_seo() + check_prom() + check_term()
    for e in errs: print("✗", e)
    print(f"Проверено страниц: {n}, нарушений: {len(errs)}")
    sys.exit(1 if errs else 0)
