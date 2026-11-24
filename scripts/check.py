"""Автопроверки собранного сайта. Код возврата 1, если есть нарушения.
Использование: check.py [папка] [--staging | --release]   |   check.py --selftest
Переадресации со старого сайта: data/redirects.csv ↔ .htaccess сборки.
--staging: дополнительно проверить, что тестовая копия закрыта от индексации.
--release: боевой сайт — картинки только с правом использования (журнал ДЗ09, статус «разрешено» или «своё»).
Кроме собранных страниц проверяются исходные SEO-тексты content/seo (правило 4: названия препаратов — по таблице связей)."""
import csv, html, json, re, sys
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
IMG_REF = re.compile(r"""(?:src|data-front|data-back)\s*=\s*["']/static/(img/[^"']+?)(?:-\d+)?\.(?:webp|svg|jpe?g|png)(?:\?v=\w+)?["']""", re.I)
# Метки версий (24.11.2026): Timeweb отдаёт /static/ с хранением в браузере на год — без метки после выкладки остаются старые стили и скрипты
STATIC_REF = re.compile(r"""(?:src|href|data-front|data-back)\s*=\s*["']/static/([^"'?#]+)(\?v=\w+)?["']""", re.I)
JOURNAL = ROOT / "assets" / "image-sources.csv"
STATUSES = {"разрешено", "своё", "ожидает", "уточнить"}  # первые два допустимы на боевом сайте (ДЗ09)
RELEASE_OK = {"разрешено", "своё"}
REQUIRED = ("catalog/all/index.html", "about/index.html", "contacts/index.html", "comments/index.html", "privacy-policy/index.html", "sitemap/index.html", "404.html")  # план §2.4
PRICE_FILE = "files/prays-list.pdf"  # П07
# Политика (чек-лист D, ДЗ08): без этих разделов страница не проходит
POLICY_MUST = ("Оператор персональных данных", "ИНН", "Какие данные обрабатываются", "Цели обработки", "Правовые основания", "хранятся", "Ваши права", "Отозвать согласие", "10 рабочих дней", "Кому передаются", "cookie", "Яндекс.Метрика", "Редакция от")
# Отзывы (ДЗ04, ДЗ06, B.9): стоп-слова, непроверяемые обещания, упоминание физлиц. Имён авторов здесь нет намеренно — это персональные данные
COMMENTS_OFF = r"безопасн|безвредн|экологичн|100\s*%|гарантированн|физлиц|физическ\w+ лиц|частн\w+ лиц"
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
# Стоп-слова 109-ФЗ ст. 17 и 38-ФЗ ст. 5 ч. 3 (ДЗ04, чек-лист A.1, C): по тексту страниц, alt, title, meta, подписям и по исходным текстам,
# включая черновики. Разрешённые контексты — только в scripts/stopwords-allow.txt
LEGAL_STOP = [
    (r"безопас(?:н|ен)\w*", "«безопасный» о препарате"), (r"безвред(?:н|ен)\w*", "«безвредный»"), (r"\bне\s*токсич(?:н|ен)\w*", "«нетоксичный»"),
    (r"экологичн\w*|экологически\s+(?:безопасн|чист)\w*|\bэко[-\s]\w*|экочист\w*", "«экологичный», «эко-»"), (r"биобезопасн\w*", "«биобезопасный»"),
    (r"щадящ\w*", "«щадящий»"), (r"мягк\w*\s+(?:действ|препарат|для)\w*", "«мягкий» о действии препарата"),
    (r"натуральн\w*", "«натуральный» о препарате"), (r"природн\w*", "«природный» о препарате"),
    (r"без\s+(?:вреда|ущерб\w*|побочн\w*|последстви\w*)", "«без вреда / последствий»"), (r"не\s+наносит\s+вред\w*|не\s+вредит", "«не наносит вреда»"),
    (r"малоопас(?:н|ен)\w*|малотоксич(?:н|ен)\w*","«малоопасный» вне классификации в скобках"),
    (r"полностью\s+защищ\w*|полн\w*\s+защит\w*|100\s*%", "обещание полной защиты (38-ФЗ)"),
    (r"гарантир\w*\s+(?:результат|эффект|защит)\w*|гарантированн\w*", "гарантия результата (38-ФЗ)"),
    (r"моментальн\w*\s+гибел\w*", "«моментальная гибель» (38-ФЗ)"), (r"без\s+ограничений\s+по\s+стади\w*", "«без ограничений по стадиям»"),
]
ALLOW_FILE = ROOT / "scripts" / "stopwords-allow.txt"
# Сегментация покупателей (ДЗ05, НР13, чек-лист B.5, B.6, B.9): ни ярлыков, ни противопоставления физ/юр, опт/розница. Политика — вне правила
SEGMENT = r"физлиц\w*|физическ\w+\s+лиц\w*|юрлиц\w*|юридическ\w+\s+лиц\w*|только\s+для\s+профессионал\w*|оптов\w+\s+(?:покупател|клиент)\w*|розничн\w+\s+(?:покупател|клиент)\w*|\b(?:0|6|12|16|18)\+"
# Карточка (решение Прутяна 24.08.2026, ДЗ05, П10): ровно эти 7 характеристик; регномер, свидетельство и ДОПОГ не публикуются
SPECS7 = ("Действующее вещество", "Форма препарата", "Тип применения", "Способ проникновения", "Класс опасности для человека", "Класс опасности для пчёл", "Фитотоксичность")
CARD_OFF = r"\d{3}-\d{2}-\d{3,5}-\d|свидетельств\w*\s+о\s+(?:гос\w*\s+)?регистрац\w*|регистрационн\w+\s+номер|допог|\badr\b|номер\s+оон|\bun\s?\d{4}\b"
GUARANTEE = "Гарантия качества и происхождения от производителя на всю продукцию."  # ДЗ10
EXCLUDED = ("Ректор", "Альфацин", "Лазурит Ультра", "Лигногумат", "Тиара", "Лемур", "Шаман")  # У02–У06, У08
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
    for group, title in (("cat", "Категория"), ("pack", "Упаковка"), ("hazard", "Класс опасности")):
        if len(re.findall(rf'type="checkbox" data-group="{group}"', text)) == 1:
            errs.append(f"{path}: фильтр «{title}» с одним значением (ДМ32)")
    # Фильтр «Класс опасности» (ДЗ05): есть на листинге, если в сетке два и более класса
    if len(set(re.findall(r'<a class="card"[^>]*\bdata-hazard="([1-4])"', text))) > 1 and 'data-group="hazard"' not in text:
        errs.append(f"{path}: на листинге нет фильтра «Класс опасности» (ДЗ05)")
    # Панель фильтров (ДМ23): под кнопкой «Ещё фильтры (N)» ровно эти группы, N — их число на странице
    extra = 0
    for m in re.finditer(r'<div class="fgroup( extra)?" data-group="(\w+)"( hidden)?>', text):
        want = m.group(2) in ("action", "term", "pack", "hazard", "price")
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


def read_allow(path=ALLOW_FILE):
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return [re.compile(x.strip()) for x in lines if x.strip() and not x.lstrip().startswith("#")]


def strings(o):
    if isinstance(o, dict):
        for v in o.values(): yield from strings(v)
    elif isinstance(o, list):
        for v in o: yield from strings(v)
    elif isinstance(o, str):
        yield o


def page_words(text):
    """Всё, что видит посетитель или поисковик: текст, alt, title, aria-label, placeholder, meta и строки разметки ld+json (ДЗ04, чек-лист C)."""
    ld = []
    for m in LD.finditer(text):
        try:
            ld += strings(json.loads(m.group(1)))
        except ValueError:
            pass
    t = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    attrs = re.findall(r'\b(?:alt|title|aria-label|placeholder|content)\s*=\s*"([^"]*)"', t, re.I)
    return html.unescape(" ".join([re.sub(r"<[^>]+>", " ", t)] + attrs + ld))


def stop_hits(where, text, allow):
    """Стоп-слова ДЗ04 вне разрешённых контекстов: по одному сообщению на найденный оборот."""
    low = text.lower()
    for a in allow:
        low = a.sub(" ", low)
    errs = []
    for pat, why in LEGAL_STOP:
        for m in re.finditer(pat, low):
            ctx = re.sub(r"\s+", " ", low[max(0, m.start() - 40):m.end() + 40]).strip()
            errs.append(f"{where}: {why} — «…{ctx}…» (ДЗ04)")
    return list(dict.fromkeys(errs))


def check_legal(path, text, allow, s):
    """Правовой аудит страницы (этап 7, чек-лист A–D): стоп-слова, сегментация, подвал, окно cookie, согласие, ДЗ10, карточка."""
    rel = Path(path).as_posix()
    words = page_words(text)
    errs = stop_hits(rel, words, allow)
    if not rel.startswith("privacy-policy/"):
        for m in sorted(set(x.group(0) for x in re.finditer(SEGMENT, words.lower()))):
            errs.append(f"{rel}: «{m}» — сегментация покупателей или возрастной знак (ДЗ05, НР13, НР15)")
    foot = re.search(r"<footer\b.*?</footer>", text, re.S)
    if not foot:
        errs.append(f"{rel}: нет подвала с реквизитами (чек-лист B.1)")
    else:
        ft = html.unescape(re.sub(r"<[^>]+>", " ", foot.group(0)))
        ft = re.sub(r"\s+", " ", ft)
        lg = s["legal"]
        for must in (s["company"], f"ИНН {lg['inn']}", f"КПП {lg['kpp']}", f"ОГРН {lg['ogrn']}", f"Оператор персональных данных № {lg['pd_operator']}",
                     s["address"], s["email"], f"© {s['company']}"):
            if must not in ft:
                errs.append(f"{rel}: в подвале нет «{must}» (чек-лист B.1, ДЗ03)")
        if 'href="/privacy-policy/"' not in foot.group(0):
            errs.append(f"{rel}: в подвале нет ссылки на Политику (ДЗ01)")
    ck = re.search(r'<div[^>]*\bid="cookie"[^>]*>(.*?)</div>\s*</div>', text, re.S)
    buttons = re.findall(r"<button\b[^>]*>(.*?)</button>", ck.group(1), re.S) if ck else []
    if [b.strip() for b in buttons] != ["Принять"]:
        errs.append(f"{rel}: в окне cookie не одна кнопка «Принять» (ДЗ08)")
    if not ck or 'href="/privacy-policy/"' not in ck.group(1):
        errs.append(f"{rel}: в окне cookie нет ссылки на Политику (ДЗ08)")
    form = re.search(r'<form\b[^>]*\bid="lead-form"[^>]*>(.*?)</form>', text, re.S)
    if form:
        boxes = re.findall(r'<input\b[^>]*type="checkbox"[^>]*>', form.group(1))
        lab = re.search(r'<label class="consent">(.*?)</label>', form.group(1), re.S)
        if len(boxes) != 1 or not lab:
            errs.append(f"{rel}: в форме заявки не одна отдельная галочка согласия (ДЗ07 п. 1)")
        elif not re.search(r"согласие на обработку персональных данных для \w+", lab.group(1)) or 'href="/privacy-policy/"' not in lab.group(1):
            errs.append(f"{rel}: в подписи согласия нет цели обработки или ссылки на Политику (ДЗ07 п. 3)")
        elif re.search(r"рассылк|оферт|услови\w+ работ", lab.group(1), re.I):
            errs.append(f"{rel}: согласие смешано с рассылкой или условиями (ДЗ07 п. 1)")
    if rel == "index.html" and GUARANTEE not in text:
        errs.append(f"{rel}: в блоке «Производители» нет «{GUARANTEE}» (ДЗ10)")
    if any('"@type": "Product"' in m or '"@type":"Product"' in m for m in LD.findall(text)):
        mob = re.search(r"<summary>Характеристики препарата</summary>(.*?)</details>", text, re.S)
        dts = re.findall(r"<dt>(.*?)</dt>", mob.group(1)) if mob else []
        # Пустое поле не выводится (фитотоксичность — только при утверждении производителя), лишних и переставленных быть не может
        if tuple(dts) != tuple(k for k in SPECS7 if k in dts) or set(re.findall(r'<div class="spec"><dt>(.*?)</dt>', text)) != set(dts):
            errs.append(f"{rel}: в карточке характеристики не из списка семи или не по порядку (решение 24.08.2026)")
        for k, v in re.findall(r'<div class="spec"><dt>(.*?)</dt><dd>(.*?)</dd>', text):
            if k.startswith("Класс опасности") and not re.match(r"[1-4]\b", v):
                errs.append(f"{rel}: «{k}» — не класс 1–4 (ДЗ05, ОВ41)")
        for m in sorted(set(x.group(0) for x in re.finditer(CARD_OFF, words.lower()))):
            errs.append(f"{rel}: в карточке «{m}» — регномер, свидетельство и ДОПОГ не публикуются (ДЗ05)")
        if not re.search(r'<div class="p-origin">Производитель: [^<]+ · страна происхождения: [^<]+</div>', text):
            errs.append(f"{rel}: в карточке нет изготовителя и страны происхождения (ЗоЗПП ст. 10, решение 24.11.2026)")
        h1 = re.search(r'<h1 class="p-title">(.*?)</h1>', text)
        if h1 and h1.group(1).startswith(EXCLUDED):
            errs.append(f"{rel}: карточка исключённого препарата {h1.group(1)} (У02–У06, У08)")
    return list(dict.fromkeys(errs))


def check_legal_sources(root=ROOT):
    """Стоп-слова ДЗ04 и сегментация в исходных текстах, включая черновики: чтобы нарушение не всплыло при публикации."""
    root, allow, errs = Path(root), read_allow(), []
    for f in sorted((root / "content").rglob("*.yml")):
        rel = f.relative_to(root).as_posix()
        text = "\n".join(strings(yaml.safe_load(f.read_text(encoding="utf-8"))))
        errs += stop_hits(rel, text, allow)
        if f.stem != "privacy-policy":
            for m in sorted(set(x.group(0) for x in re.finditer(SEGMENT, text.lower()))):
                errs.append(f"{rel}: «{m}» — сегментация покупателей или возрастной знак (ДЗ05, НР13, НР15)")
    pf = root / "data" / "products.csv"
    if pf.is_file():
        for p in read_csv(pf):
            text = "\n".join(p.get(k, "") for k in ("name", "description", "drug_type", "phytotox", "action_character", "dv_text"))
            errs += stop_hits(f"products.csv: {p['slug']}", text, allow)
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
    # Закрытая папка внутри сайта: выкладка не должна её стирать, общий .htaccess её закрывает
    if ".vostok-private" in t:
        wf = ROOT / ".github" / "workflows" / "deploy.yml"
        if wf.is_file() and "--exclude='/.vostok-private'" not in wf.read_text(encoding="utf-8"):
            errs.append("deploy.yml: выкладка сотрёт закрытую папку заявок .vostok-private")
        ht = Path(d) / ".htaccess"
        if ht.is_file() and ".vostok-private" not in ht.read_text(encoding="utf-8"):
            errs.append(".htaccess: нет запрета на закрытую папку заявок")
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
        if not body or not re.search(r"снять.{0,80}vostokxim@mail\.ru", body.group(0), re.S):
            errs.append("comments: нет способа попросить снять отзыв (ДЗ06 п. 5)")
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


CLOSED = ("404.html", "catalog/all/index.html")  # закрыты от поиска всегда (ДМ38), в том числе на тестовой копии
NOINDEX = 'name="robots" content="noindex'


def ld_blocks(text):
    out = []
    for m in LD.finditer(text):
        try:
            out.append(json.loads(m.group(1)))
        except ValueError:
            pass  # о нечитаемой разметке сообщает check_file
    return out


def ld_has(obj, keys):
    """Есть ли где-нибудь в разметке ключ из keys (рейтинг, отзывы)."""
    if isinstance(obj, dict):
        return any(k in keys for k in obj) or any(ld_has(v, keys) for v in obj.values())
    return isinstance(obj, list) and any(ld_has(v, keys) for v in obj)


def tag_text(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", s)).replace("\xad", "").split())


def check_markup(d, staging=False):
    """SEO-минимум (план §5, ДМ40): у страниц, открытых для поиска, свои title и description, canonical на себя, есть в sitemap.xml;
    разметка читается и совпадает с видимым: крошки, сетка листинга, цена; Organization на главной, LocalBusiness на /contacts/; рейтинга нет.
    sitemap.xml и robots.txt боевого сайта: только открытые страницы, ничего открытого не закрыто."""
    d, errs = Path(d), []
    site = yaml.safe_load((ROOT / "data" / "settings.yml").read_text(encoding="utf-8"))["site_url"]
    prices = {r["slug"]: r["price"] for r in read_csv(ROOT / "data" / "prices.csv")}
    seen = {"title": {}, "description": {}}
    open_urls = set()
    for f in sorted(d.rglob("*.html")):
        rel = f.relative_to(d).as_posix()
        url = "/" + rel.removesuffix("index.html")
        text = f.read_text(encoding="utf-8")
        lds = ld_blocks(text)
        for ld in lds:
            if ld.get("@context") != "https://schema.org":
                errs.append(f"{rel}: в разметке нет @context https://schema.org")
            if ld_has(ld, ("aggregateRating", "review", "reviewRating")):
                errs.append(f"{rel}: рейтинг или отзывы в разметке — не ставим (ДМ40)")
        if rel in CLOSED or (not staging and NOINDEX in text):
            continue
        open_urls.add(url)
        head = text.split("</head>")[0]
        for key, pat in (("title", r"<title>(.*?)</title>"), ("description", r'<meta name="description" content="([^"]*)"')):
            m = re.search(pat, head, re.S)
            val = html.unescape(m.group(1)).strip() if m else ""
            if not val:
                errs.append(f"{rel}: нет {key} (SEO-минимум)")
            elif val in seen[key]:
                errs.append(f"{rel}: {key} повторяется — такой же у {seen[key][val]} (SEO-минимум)")
            else:
                seen[key][val] = rel
        m = re.search(r'<link rel="canonical" href="([^"]*)"', head)
        if not m or m.group(1) != site + url:
            errs.append(f"{rel}: canonical не на себя ({m.group(1) if m else 'нет'}, нужен {site + url})")
        types = {ld.get("@type"): ld for ld in lds}
        # Крошки: на всех страницах, кроме главной; звенья разметки = видимые звенья
        if url != "/":
            crumbs = re.search(r'<div class="crumbs">(.*?)</div>', text, re.S)
            bc = types.get("BreadcrumbList")
            if not crumbs or not bc:
                errs.append(f"{rel}: нет хлебных крошек или разметки BreadcrumbList (ДМ40)")
            else:
                vis = [(tag_text(n), site + h) for h, n in re.findall(r'<a href="([^"]*)">(.*?)</a>', crumbs.group(1))]
                cur = re.search(r'<span class="cur">(.*?)</span>', crumbs.group(1))
                vis.append((tag_text(cur.group(1)) if cur else "", site + url))
                got = [(x.get("name"), x.get("item")) for x in bc.get("itemListElement", [])]
                if got != vis or [x.get("position") for x in bc.get("itemListElement", [])] != list(range(1, len(got) + 1)):
                    errs.append(f"{rel}: BreadcrumbList не совпадает с видимыми крошками (ДМ40)")
        # Листинг: CollectionPage + ItemList в порядке сетки
        cards = re.findall(r'<a class="card" href="([^"]+)" data-name=', text)  # сетка листинга; «Смотрите также» в карточке — без data-name
        if cards:
            cp = types.get("CollectionPage")
            il = cp.get("mainEntity", {}) if cp else {}
            urls = [x.get("url") for x in il.get("itemListElement", [])] if isinstance(il, dict) else []
            if not cp or il.get("@type") != "ItemList":
                errs.append(f"{rel}: листинг без разметки CollectionPage/ItemList (ДМ33, ДМ40)")
            elif urls != [site + c for c in cards] or il.get("numberOfItems") != len(cards):
                errs.append(f"{rel}: ItemList не совпадает с карточками листинга (ДМ33)")
        if url == "/" and not {"name", "url", "telephone", "address"} <= set(types.get("Organization", {})):
            errs.append(f"{rel}: на главной нет разметки Organization с названием, адресом и телефоном (ДМ40)")
        if url == "/contacts/" and not {"name", "telephone", "address"} <= set(types.get("LocalBusiness", {})):
            errs.append(f"{rel}: на /contacts/ нет разметки LocalBusiness с названием, адресом и телефоном (ДМ40)")
        prod = types.get("Product")
        if prod:
            offer = prod.get("offers") or {}
            slug = url.strip("/").split("/")[-1]
            if offer.get("@type") != "Offer" or offer.get("priceCurrency") != "RUB":
                errs.append(f"{rel}: в Product нет Offer в рублях (ДМ40)")
            if offer.get("url") != site + url:
                errs.append(f"{rel}: адрес в Offer не равен адресу карточки")
            if slug not in prices or str(offer.get("price")) != str(int(float(prices[slug]))):
                errs.append(f"{rel}: цена в Offer не из prices.csv ({offer.get('price')} и {prices.get(slug, 'нет')})")
    if staging:
        return errs
    # sitemap.xml и robots.txt боевого сайта
    sm = d / "sitemap.xml"
    if not sm.is_file():
        errs.append(f"{d}: нет sitemap.xml (ДМ40)")
    else:
        locs = re.findall(r"<loc>(.*?)</loc>", sm.read_text(encoding="utf-8"))
        paths = {html.unescape(x).removeprefix(site) for x in locs}
        for x in locs:
            if not x.startswith(site + "/") or x.removeprefix(site) not in open_urls:
                errs.append(f"sitemap.xml: {x} — закрытая от поиска или несуществующая страница (ДМ40)")
        for u in sorted(open_urls - paths):
            errs.append(f"sitemap.xml: нет открытой страницы {u} (SEO-минимум)")
        if len(locs) != len(set(locs)):
            errs.append("sitemap.xml: адрес повторяется")
    rb = d / "robots.txt"
    rt = rb.read_text(encoding="utf-8") if rb.is_file() else ""
    if not rt:
        errs.append(f"{d}: нет robots.txt боевого сайта (ДМ40)")
    else:
        if f"Sitemap: {site}/sitemap.xml" not in rt.splitlines():
            errs.append("robots.txt: нет строки Sitemap со ссылкой на sitemap.xml (ДМ40)")
        for rule in re.findall(r"(?im)^Disallow:\s*(\S+)", rt):
            hit = sorted(u for u in open_urls if u.startswith(rule.replace("*", "")))
            if hit:
                errs.append(f"robots.txt: Disallow {rule} закрывает открытые страницы ({hit[0]}…)")
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


REDIRECT = re.compile(r"^RedirectMatch\s+301\s+(\S+)\s+(\S+)\s*$", re.M)


def check_redirects(d, table=ROOT / "data" / "redirects.csv", release=False):
    """Переадресации 301 (ДМ40 п. 4): таблица без повторов и цепочек; в .htaccess каждая цель собрана,
    правило не закрывает собранную страницу и не ведёт на другой переадресуемый адрес; на боевом сайте подключены все строки."""
    d, errs = Path(d), []
    rows = read_csv(table) if Path(table).is_file() else []
    if not rows:
        errs.append(f"{table}: нет таблицы переадресаций со старого сайта")
    seen = set()
    for r in rows:
        old, new = r["old"], r["new"]
        if not old.startswith("/") or not new.startswith("/") or new.startswith("//"):
            errs.append(f"redirects.csv: {old} → {new}: адрес не с «/» своего сайта")
        if old.rstrip("/") in seen:
            errs.append(f"redirects.csv: старый адрес {old} повторяется")
        seen.add(old.rstrip("/"))
        if new.rstrip("/") in {x["old"].rstrip("/") for x in rows}:
            errs.append(f"redirects.csv: цепочка переадресаций {old} → {new} → …")
    ht = d / ".htaccess"
    rules = REDIRECT.findall(ht.read_text(encoding="utf-8")) if ht.is_file() else []
    pages = {"/" + p.relative_to(d).as_posix().removesuffix("index.html") for p in d.rglob("*") if p.is_file()}
    for pat, target in rules:
        try:
            rx = re.compile(pat)
        except re.error:
            errs.append(f".htaccess: ошибка в шаблоне переадресации {pat}"); continue
        if target not in pages:
            errs.append(f".htaccess: цель переадресации {target} не существует ({pat})")
        if any(re.search(p2, target) for p2, _ in rules):
            errs.append(f".htaccess: цепочка переадресаций {pat} → {target} → …")
        hit = sorted(p for p in pages if rx.search(p))
        if hit:
            errs.append(f".htaccess: переадресация {pat} закрывает собранную страницу {hit[0]}")
    if release:
        emitted = {t for _, t in rules}
        for r in rows:
            if r["new"] not in emitted or not any(re.search(p, r["old"]) for p, _ in rules):
                errs.append(f"redirects.csv: переадресация {r['old']} → {r['new']} не подключена — новый адрес не собран")
    return errs


YM_GOALS = ("lead_sent",)  # ДМ40 п. 5: цель «Заявка с сайта»; телефон и почта — цели Метрики по ссылкам (нужен trackLinks)


def check_metrika(d, staging=False, release=False):
    """Метрика (ДМ40 п. 5, ДЗ08): номер счётчика на каждой странице боевой сборки, на тестовой копии — нет;
    в самой странице счётчика нет (иначе он загрузится до «Принять»); site.js грузит его только после «Принять»,
    без Вебвизора, с тремя целями."""
    d, errs, ids = Path(d), [], set()
    for f in sorted(d.rglob("*.html")):
        text = f.read_text(encoding="utf-8")
        m = re.search(r'id="cookie"[^>]*\bdata-ym="(\d*)"', text)
        if m:
            ids.add(m.group(1))
        elif release:
            errs.append(f"{f.relative_to(d)}: нет номера счётчика Метрики (data-ym)")
        if re.search(r"mc\.yandex\.ru|metrika/tag\.js|\bym\(", text):
            errs.append(f"{f.relative_to(d)}: счётчик Метрики в коде страницы — загрузится до «Принять» (ДЗ08)")
    if staging and ids:
        errs.append(f"{d}: на тестовой копии подключён счётчик Метрики — тестовые визиты попадут в статистику")
    if len(ids) > 1:
        errs.append(f"{d}: на страницах разные номера счётчика: {', '.join(sorted(ids))}")
    js = d / "static" / "site.js"
    if ids and js.is_file():
        code = js.read_text(encoding="utf-8")
        if re.search(r"webvisor\s*:\s*true", code) or not re.search(r"webvisor\s*:\s*false", code):
            errs.append("site.js: Вебвизор не выключен явно (ДМ40 п. 5)")
        if not re.search(r"trackLinks\s*:\s*true", code):
            errs.append("site.js: без trackLinks не работают цели «Позвонить» и «Клик по почте»")
        start = re.search(r"function startYm\(\)\s*\{(.*?)\n  \}", code, re.S)
        if not start or "tag.js" not in start.group(1) or code.count("tag.js") != 1:
            errs.append("site.js: счётчик загружается не только из startYm()")
        if not re.search(r"if \(v === 'yes'\) startYm\(\)", code) or not re.search(r"if \(saved === 'yes'\) startYm\(\)", code):
            errs.append("site.js: счётчик загружается не по кнопке «Принять» (ДЗ08)")
        for g in YM_GOALS:
            if f"'{g}'" not in code:
                errs.append(f"site.js: нет цели {g} (ДМ40 п. 5)")
    return errs


def check_dir(d, staging=False, release=False, journal=JOURNAL):
    errs, n, has_form = [], 0, False
    jr = read_journal(journal)
    allow, s = read_allow(), yaml.safe_load((ROOT / "data" / "settings.yml").read_text(encoding="utf-8"))
    for f in sorted(Path(d).rglob("*.html")):
        n += 1
        text = f.read_text(encoding="utf-8")
        has_form = has_form or 'id="lead-form"' in text
        errs += check_file(f.relative_to(d), text, Path(d))
        errs += check_images(f.relative_to(d), text, jr, release)
        errs += check_legal(f.relative_to(d), text, allow, s)
        for rel_s, v in sorted(set(STATIC_REF.findall(text))):
            if (Path(d) / "static" / rel_s).is_file() and not v and not rel_s.startswith("fonts/"):
                errs.append(f"{f.relative_to(d)}: /static/{rel_s} без метки версии — после выкладки браузер покажет старый файл")
        if re.search(r'class="sep">·</span>(?!<wbr>)', text):
            errs.append(f"{f.relative_to(d)}: крошки не переносятся — после разделителя нужен <wbr>")
        if staging and 'name="robots" content="noindex' not in text:
            errs.append(f"{f.relative_to(d)}: тестовая копия не закрыта от индексации (нет noindex)")
    if n == 0:
        errs.append(f"{d}: нет ни одной html-страницы")
    errs += check_service(d, release) + check_css(d) + check_search(d) + check_send(d, has_form) + check_markup(d, staging) + check_metrika(d, staging, release)
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
    legal = check_legal_sources(ROOT / "tests" / "seo")
    bad += legal + seo + check_prom(ROOT / "tests" / "seo") + check_term(ROOT / "tests" / "seo") + check_send(ROOT / "tests" / "send-bad", True)
    bad += check_redirects(ROOT / "tests" / "bad", ROOT / "tests" / "seo" / "data" / "redirects.csv", release=True)
    expected = ["не записана в журнал", "неизвестный статус", "без права использования", "Прямые дистрибьюторы", "гарантии", "cookie", "Щёлково", "наличия", "чужому серверу", "заранее", "не обязательна", "без alt", "GA4", "цена на странице", "битая ссылка /catalog/gerbitsidy/", "битая ссылка /catalog/kultura/", "битая ссылка /catalog/vrednyy-obekt/vrediteli/", "битая ссылка /catalog/seriya/", "не открывает форму заявки", "нет поля territory", "фильтр вместо ссылки", "нет галочки в боковой панели", "«Категория» с одним значением",
                "«Упаковка» с одним значением", "«Класс опасности» с одним значением", "нет фильтра «Класс опасности»", "развёрнута, а должна быть под кнопкой", "под кнопкой «Ещё фильтры», а должна быть развёрнута", "не то число групп", "только на листинге категории", "не на месте", "повторяет быстрый вход", "не совпадает с отбором", "balerina-se — тип применения расходится", "miura-ke — тип применения расходится",
                "тег dovskhodovyy не у гербицида", "нет применения до всходов", "нет тега dovskhodovyy",
                "нет noindex", "без robots.txt", "Миура — нет связи", "Тиара — исключена","Бицепс — нет в каталоге", "нет в словаре",
                "не у гербицида", "без связи", "без тега", "Миура — нет тега",
                "неизвестный scope", "scope: prom у препарата без тега", "без пометки scope: prom", "нет строк scope: prom",
                "нет обязательной страницы about", "отменённые страницы /return-policy/", "препарата нет в каталоге", "в политике нет раздела", "недопустимое в отзыве", "sitemap: нет ссылки", "404 не настроена", "404.html: страница не закрыта", "нет файла прайса",
                "колонка .shell растягивается", "длинное слово в заголовке", "крошки не переносятся", "нижняя кнопка на главной", "нет телефонов в первом экране",
                "нет обязательной страницы catalog/all", "нет значка или поля поиска", "в шапке нет номера телефона", "в индексе поиска цена", "индекс ведёт на несобранную страницу",
                "нет title", "title повторяется", "description повторяется", "canonical не на себя", "нет @context", "рейтинг или отзывы в разметке",
                "нет хлебных крошек или разметки BreadcrumbList", "BreadcrumbList не совпадает", "ItemList не совпадает", "нет разметки Organization", "нет разметки LocalBusiness",
                "нет Offer в рублях", "адрес в Offer не равен", "цена в Offer не из prices.csv", "закрытая от поиска или несуществующая", "sitemap.xml: нет открытой страницы",
                "нет строки Sitemap", "закрывает открытые страницы",
                "не отправляется в /send.php", "нет скрытого поля territory", "нет скрытого поля page", "нет поля-ловушки", "не показывает телефон", "«Если не ответим", "а send.php нет",
                "цель переадресации /catalog/net-takoy/ не существует", "цепочка переадресаций ^/", "закрывает собранную страницу", "старый адрес /products/ повторяется", "redirects.csv: цепочка", "адрес не с «/»", "не подключена",
                "счётчик Метрики в коде страницы", "на тестовой копии подключён счётчик", "нет номера счётчика Метрики", "Вебвизор не выключен", "не по кнопке «Принять»", "нет цели lead_sent", "без trackLinks",
                "«безопасный» о препарате — «…препарат безопасен", "«натуральный» о препарате", "гарантия результата", "legal-bad.yml: «физлицам»",
                "«щадящий»", "«экологичный»", "обещание полной защиты", "«безвредный»", "«только для профессионалов»", "«18+»", "в подвале нет «ИНН 7447186421»",
                "в подвале нет ссылки на Политику", "не одна кнопка «Принять»", "в окне cookie нет ссылки", "нет цели обработки или ссылки на Политику", "нет «Гарантия качества",
                "карточка исключённого препарата Шаман", "нет изготовителя и страны происхождения", "/static/site.js без метки версии", "не из списка семи", "не класс 1–4", "«109-03-3245-1»", "«допог»", "«un 3082»", "нет подвала с реквизитами",
                "comments: нет способа попросить снять отзыв", "в политике нет раздела «10 рабочих дней»",
                "не подставлены телефоны", "без галочки согласия не отклоняется", "нет проверки поля-ловушки", "нет ограничения частоты", "настройки не вне папки сайта", "сбой отправки не сообщается", "пароль почты в файле сайта"]
    missing = [e for e in expected if not any(e in x for x in bad)]
    if any(w in x for x in legal + bad for w in ("безопасного выхода", "обезвред", "(малоопасный)", "природные гормоны")):
        missing.append("ложное срабатывание на разрешённый контекст ДЗ04")
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
    errs += check_seo() + check_prom() + check_term() + check_legal_sources() + check_redirects(d, release="--release" in sys.argv)
    for e in errs: print("✗", e)
    print(f"Проверено страниц: {n}, нарушений: {len(errs)}")
    sys.exit(1 if errs else 0)
