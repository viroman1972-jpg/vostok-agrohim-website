"""Автопроверки собранного сайта. Код возврата 1, если есть нарушения.
Использование: check.py [папка]   |   check.py --selftest"""
import re, sys
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

def check_file(path, text):
    errs = []
    low = text.lower()
    for pat, why in STOP_PHRASES:
        if re.search(pat, low):
            errs.append(f"{path}: {why}")
    if EXTERNAL.search(text) or CSS_URL.search(text):
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

def check_dir(d):
    errs, n = [], 0
    for f in sorted(Path(d).rglob("*.html")):
        n += 1
        errs += check_file(f.relative_to(d), f.read_text(encoding="utf-8"))
    if n == 0:
        errs.append(f"{d}: нет ни одной html-страницы")
    return errs, n

def selftest():
    bad, _ = check_dir(ROOT / "tests" / "bad")
    expected = ["Прямые дистрибьюторы", "гарантии", "cookie", "Щёлково", "наличия", "чужому серверу", "заранее", "не обязательна", "без alt", "GA4"]
    missing = [e for e in expected if not any(e in x for x in bad)]
    if missing:
        print("SELFTEST ПРОВАЛЕН, проверки не поймали:", ", ".join(missing)); return 1
    print(f"selftest ок: на плохом примере поймано {len(bad)} нарушений"); return 0

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    d = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist"
    errs, n = check_dir(d)
    for e in errs: print("✗", e)
    print(f"Проверено страниц: {n}, нарушений: {len(errs)}")
    sys.exit(1 if errs else 0)
