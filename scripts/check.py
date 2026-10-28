"""Автопроверки собранного сайта. Код возврата 1, если есть нарушения.
Использование: check.py [папка] [--staging | --release]   |   check.py --selftest
--staging: дополнительно проверить, что тестовая копия закрыта от индексации.
--release: боевой сайт — картинки только с правом использования (журнал ДЗ09, статус «разрешено» или «своё»)."""
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
PLANNED = ("/catalog/kultura/", "/catalog/vrednyy-obekt/", "/catalog/dv/", "/catalog/seriya/", "/contacts/", "/about/",
           "/comments/", "/sitemap/", "/privacy-policy/", "/send.php", "/catalog/insektitsidy/", "/catalog/fungitsidy/",
           "/catalog/protraviteli/", "/catalog/stimulyatory-rosta/", "/catalog/adyuvanty/", "/catalog/desikanty/")
HREF = re.compile(r"""<a\b[^>]*\bhref\s*=\s*["'](/[^"'#?]*)""", re.I)
PRICE_VIS = re.compile(r'class="price">\s*([\d\s ]+)\s*₽')
IMG_REF = re.compile(r"""(?:src|data-front|data-back)\s*=\s*["']/static/(img/[^"']+?)(?:-\d+)?\.(?:webp|svg|jpe?g|png)["']""", re.I)
JOURNAL = ROOT / "assets" / "image-sources.csv"
STATUSES = {"разрешено", "своё", "ожидает", "уточнить"}  # первые два допустимы на боевом сайте (ДЗ09)
RELEASE_OK = {"разрешено", "своё"}
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


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
            if not link_exists(root, href) and not href.startswith(PLANNED) and href != "/catalog/":
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


def selftest():
    bad, _ = check_dir(ROOT / "tests" / "bad", staging=True, journal=ROOT / "tests" / "image-sources.csv")
    bad += check_dir(ROOT / "tests" / "bad", release=True, journal=ROOT / "tests" / "image-sources.csv")[0]
    expected = ["не записана в журнал", "неизвестный статус", "без права использования", "Прямые дистрибьюторы", "гарантии", "cookie", "Щёлково", "наличия", "чужому серверу", "заранее", "не обязательна", "без alt", "GA4", "цена на странице", "битая ссылка",
                "нет noindex", "без robots.txt"]
    missing = [e for e in expected if not any(e in x for x in bad)]
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
    for e in errs: print("✗", e)
    print(f"Проверено страниц: {n}, нарушений: {len(errs)}")
    sys.exit(1 if errs else 0)
