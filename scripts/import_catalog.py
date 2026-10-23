"""Разовый импорт полного каталога в data/products.csv и data/prices.csv (этап 2).

Источники: парс старого сайта (phase-4-content/parsed_v2/parsed_v2_full.zip) — название, категория,
фасовка, цена, характеристики; сверка с agroxxi от 08.08.2026 (verification-snapshot) — действующие
вещества, классы опасности, срок регистрации (ПИ10). Исключённые У02–У06 не переносятся.

Строки, которые уже есть в products.csv / prices.csv, не трогаются: скрипт только дописывает
недостающие препараты со статусом draft. Отчёт о пробелах — в файл, путь которого передан аргументом.
Запуск: python -I scripts/import_catalog.py <отчёт.md>
"""
import csv, json, re, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "phase-4-content" / "parsed_v2" / "parsed_v2_full.zip"
SNAPSHOT = ROOT / "phase-4-content" / "verification-snapshot-2026-08-08.md"

EXCLUDED = {"Ректор", "Альфацин", "Лазурит Ультра", "Лигногумат калийный марка АМ", "Тиара"}  # У02–У06

CATEGORY = {"Гербициды": "gerbitsidy", "Инсектициды": "insektitsidy", "Фунгициды": "fungitsidy",
            "Протравители": "protraviteli", "Стимуляторы роста растений": "stimulyatory-rosta",
            "Адьюванты (Прилипатели, ПАВы)": "adyuvanty", "Десиканты": "gerbitsidy"}  # ПИ08: десикант лежит в гербицидах
MAKER = {"Август": "avgust", "Август/Avgust": "avgust", "Гарант Оптима": "garant-optima",
         "Альбит НПФ": "albit", None: "agrokhiminvest"}  # Лямбда-С без производителя — Агрохиминвест (К7)
NEW_MAKERS = [("garant-optima", "Гарант Оптима", "Гарант Оптима"), ("agrokhiminvest", "Агрохиминвест", "Агрохиминвест"),
              ("albit", "НПФ Альбит", "НПФ Альбит")]

# Формы препаратов; помеченные * — расшифровка не подтверждена этикеткой, см. отчёт
FORMS = {"СЭ": "суспензионная эмульсия", "ВР": "водный раствор", "ВДГ": "водно-диспергируемые гранулы",
         "ВРГ": "водорастворимые гранулы", "ВРК": "водорастворимый концентрат", "КЭ": "концентрат эмульсии",
         "МЭ": "микроэмульсия", "СК": "суспензионный концентрат", "ВСК": "водно-суспензионный концентрат",
         "СП": "смачивающийся порошок", "КС": "концентрат суспензии", "Ж": "жидкость",
         "ВГР": "водно-гликолевый раствор", "МКЭ": "*микроэмульгирующийся концентрат",
         "КМЭ": "*концентрат микроэмульсии", "КНЭ": "*концентрат наноэмульсии",
         "ТКС": "*текучий концентрат суспензии", "ТПС": "*текучая паста"}

# Исправления по сверке 08.08.2026 (раздел «Опечатки и неточности»)
NAME_FIX = {"Колосаль Про, КМЭ": "Колосаль Про, КМЭ", "Тебузил, КС": "Тебузил, ТКС", "Виал Траст, ВСК": "Виал ТрасТ, ВСК",
            "Дублон голд, ВДГ": "Дублон Голд, ВДГ", "Ластик экстра, КЭ": "Ластик Экстра, КЭ",
            "Дракон Супер 7,5 КЭ": "Дракон Супер 7,5, КЭ"}

TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              "a b v g d e e zh z i y k l m n o p r s t u f kh ts ch sh shch - y - e yu ya".split()))

EXPIRY_FIX = {"Альбит": "22.12.2030"}  # две регистрации (фунгицид до 22.12.2030, регулятор роста до 03.03.2036) — ранняя

HUMAN = {"1": "1 (чрезвычайно опасное)", "2": "2 (опасное)", "3": "3 (умеренно опасное)", "4": "4 (малоопасное)"}
BEE = {"1": "1 (высокоопасное)", "2": "2 (среднеопасное)", "3": "3 (малоопасное)"}

FIELDS_NEW = ["country", "tags", "registration_type", "registration_expiry", "notes"]


def slugify(s):
    s = "".join(TR.get(ch, ch) if ch != "-" else "-" for ch in s.lower().replace("ъ", "").replace("ь", ""))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def short_name(full):
    """«Балерина, СЭ (410 г/л + 7,4 г/л)» → «Балерина, СЭ»."""
    m = re.match(r"^(.+?,\s*[А-ЯЁ]{1,4})(?![а-яё])", full) or re.match(r"^(.+? [А-ЯЁ]{2,4})(?=\s*\()", full)
    n = m.group(1) if m else full.strip()
    return NAME_FIX.get(n, n)


def brand(name):
    return name.split(",")[0].strip()


def cap(s):
    return s[:1].upper() + s[1:] if s else s


def read_snapshot():
    """Строки таблиц сверки: бренд → dict(dv, hazard, expiry, raw)."""
    out = {}
    for line in SNAPSHOT.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| П\d+ \|", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        name = re.sub(r"\*|⚠️|✅|→гербицид|\(№92\)", "", cells[1]).strip()
        if len(cells) == 7:          # Август: №, препарат, ДВ, концентрация, регномер, до, класс
            dv, conc, exp, cls = cells[2], cells[3], cells[5], cells[6]
        elif len(cells) == 8:        # Гарант и прочие: №, препарат, регистрант, ДВ+конц., регномер, до, класс, флаг
            dv, conc, exp, cls = cells[3], "", cells[5], cells[6]
        else:                        # ПАВ: класс не присваивается
            dv, conc, exp, cls = cells[2], "", "", ""
        h = re.search(r"(\d|—)\s*/\s*\**\s*(\d|—)", cls.replace("*", ""))
        e = re.search(r"\d\d\.\d\d\.\d{4}", exp)
        out[brand(name)] = dict(dv=dv, conc=conc, human=h.group(1) if h else "", bee=h.group(2) if h else "",
                                expiry=e.group(0) if e else "", pav=len(cells) == 4, raw_cls=cls)
    return out


def dv_text(sn):
    """Действующие вещества в формате карточки: «2,4-Д (2-этилгексиловый эфир), 410 г/л + Флорасулам, 7,4 г/л»."""
    dv = re.sub(r"\*", "", sn["dv"])
    dv = re.sub(r"\s*\((?:не [^)]*|[^)]*не \d[^)]*)\)", "", dv)          # пометки сверки «(не Р!)», «(не флутриафол!)»
    dv = re.sub(r"\s*—.*?!", "", dv).replace("калиевая+натриевая", "калиевая и натриевая")
    conc = sn["conc"]
    if not conc:                                                         # «Клопиралид + Пиклорам 267+67 г/л»
        m = re.search(r",?\s*([\d,]+(?:\s*\+\s*[\d,]+)*)\s*(г/л|г/кг)\s*$", dv)
        if not m:
            return ""
        dv, conc = dv[:m.start()], m.group(1) + " " + m.group(2)
    m = re.match(r"^\s*([\d,\s+]+?)\s*(г/л|г/кг)\s*$", conc)
    if not m:
        return ""
    nums = [x.strip() for x in m.group(1).split("+")]
    names = [x.strip() for x in re.split(r"\s\+\s|\+(?=\s*[А-ЯЁа-яё])", dv) if x.strip()]
    if len(nums) != len(names):
        return ""
    return " + ".join(f"{n if n.startswith('антидот') else cap(n)}, {v} {m.group(2)}" for n, v in zip(names, nums))


def packages(text):
    if not text:
        return ""
    out = []
    for num, unit in re.findall(r"(\d+(?:,\d+)?)\s*(?:и\s*\d+(?:,\d+)?\s*)?(литр\w*|л\b|кг|грамм\w*|г\b|мл)", text):
        u = {"кг": "кг", "мл": "мл"}.get(unit, "г" if unit.startswith("г") else "л")
        out.append(f"{num} {u}")
    for a, b, unit in re.findall(r"(\d+(?:,\d+)?),\s*(\d+(?:,\d+)?)\s*(литр\w*|л\b)", text):  # «Канистра 5, 10 литров»
        out[:] = [x for x in out if x != f"{b} л"] + [f"{a} л", f"{b} л"]
    for a, b, unit in re.findall(r"(\d+(?:,\d+)?)\s*и\s*(\d+(?:,\d+)?)\s*(кг|л)", text):           # «по 0,5 и 1 кг»
        out.append(f"{b} {unit}")
    if re.search(r"пакет\w* по 0,5 кг", text):                                                   # Ордан: водорастворимые пакеты внутри коробки
        out.remove("0,5 кг")
    size = lambda x: float(x.split()[0].replace(",", ".")) * {"мл": 0.001, "г": 0.001}.get(x.split()[1], 1)
    return "; ".join(sorted(set(out), key=size))


def section(text, heads):
    lines = [l.strip() for l in text.split("\n")]
    for i, l in enumerate(lines):
        if any(l.lower().startswith(h) for h in heads) and l.endswith(":"):
            for nxt in lines[i + 1:]:
                if nxt:
                    return "" if nxt.endswith(":") else nxt
    return ""


STOP = re.compile(r"безопас|безвред|нетоксич|не токсич|экологич|щадящ|натурал|природн", re.I)


def phytotox(text, brand_name):
    """Первое предложение раздела «Фитотоксичность» старого сайта; пусто, если оно не про фитотоксичность,
    с числами или со стоп-словами ДЗ04."""
    s = section(text, ("фитотоксичность", "фитоксичность"))
    s = re.split(r"(?<=[а-я])\. ", s)[0].rstrip(".").split(", но ")[0]
    s = re.sub(r"^" + re.escape(brand_name) + r"( \w+)?(?= не)", "Препарат", s, flags=re.I)
    s = s.replace("не фитотоксичен обрабатываемых", "не фитотоксичен для обрабатываемых")
    if not s or re.search(r"\d", s) or STOP.search(s) or not re.search(r"фитотокс|^отсутствует|не отмечается", s, re.I):
        return "", s
    return cap(s), ""


def main(report_path):
    sn = read_snapshot()
    z = zipfile.ZipFile(ZIP)
    items = [json.loads(z.read(n)) for n in sorted(z.namelist()) if n.endswith(".json") and n.count("/") == 1]
    pfile, prfile, mfile = ROOT / "data" / "products.csv", ROOT / "data" / "prices.csv", ROOT / "data" / "dict" / "manufacturers.csv"
    with open(pfile, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        fields, rows = list(rd.fieldnames), list(rd)
    fields += [x for x in FIELDS_NEW if x not in fields]
    have = {r["slug"] for r in rows}
    have_brand = {brand(r["name"]) for r in rows}
    with open(prfile, encoding="utf-8", newline="") as f:
        prices = list(csv.DictReader(f))
    have_price = {r["slug"] for r in prices}
    gaps, notes_all = [], []

    for d in items:
        a = {p["key"]: p["value"] for g in d["attrs"].values() for p in g["pairs"]}
        name = short_name(d["name"])
        b = brand(name)
        if b in EXCLUDED or brand(d["name"]) in EXCLUDED:
            continue
        cat_name = d["breadcrumbs"][2]["name"]
        s = sn.get(b, {})
        slug = slugify(name)
        if b in have_brand:                                  # уже в каталоге (срез 1) — только цена при отсутствии
            slug = next(r["slug"] for r in rows if brand(r["name"]) == b)
        else:
            abbr = name.split(",")[-1].strip() if "," in name else ""
            form = FORMS.get(abbr, "")
            notes = []
            if form.startswith("*"):
                form = form[1:]
                notes.append(f"расшифровка формы {abbr} не сверена с этикеткой")
            cat = "gerbitsidy" if b == "Симба" else CATEGORY[cat_name]   # Симба — гербицид (сверка 08.08.2026)
            vid = (a.get("Вид") or "").lower()
            char = a.get("Характер действия пестицида") or a.get("Характер действия") or vid
            action = "sploshnoy" if "сплошн" in char.lower() else "izbiratelnyy" if "избират" in char.lower() else ""
            pen_src = (a.get("Тип воздействия") or vid).lower()
            pen = "Системный" if "систем" in pen_src else "Контактный" if pen_src.startswith("контакт") else ""
            drug_type = ""
            if cat == "gerbitsidy" and a.get("Срок применения") and action:
                drug_type = cap(a["Срок применения"].replace("за 4-5 недель до посева", "предпосевной")) + (", избирательного действия" if action == "izbiratelnyy" else ", сплошного действия")
            phy, dropped = phytotox(d["description"]["text"], b)
            if dropped:
                notes.append(f"фитотоксичность не перенесена: «{dropped[:120]}»")
            mo = re.search(r"(\d+)", str(d.get("min_order") or ""))
            row = dict.fromkeys(fields, "")
            row.update(slug=slug, status="draft", name=name, category=cat, manufacturer=MAKER[a.get("Производитель")],
                       series="", form=f"{abbr} ({form})" if abbr and form else "", dv_text=dv_text(s) if s else "",
                       drug_type=drug_type, penetration=pen,
                       hazard_human=HUMAN.get(s.get("human", ""), ""), hazard_bee=BEE.get(s.get("bee", ""), ""),
                       phytotox=phy, action_character=action, unit=d["price"]["unit"], min_order=mo.group(1) if mo else "",
                       package_sizes=packages(a.get("Способ упаковки") or a.get("Вид упаковки")),
                       country=a.get("Страна производства", ""),
                       tags="desikaciya" if b == "Суховей" else "",
                       registration_type="ПАВ" if s.get("pav") else "пестицид",
                       registration_expiry=s.get("expiry", "") or EXPIRY_FIX.get(b, ""), notes="; ".join(notes))
            if not s:
                notes.append("нет строки в сверке 08.08.2026")
            row["notes"] = "; ".join(notes)
            rows.append(row)
            have.add(slug)
            have_brand.add(b)
            miss = [k for k in ("form", "dv_text", "drug_type", "penetration", "hazard_human", "hazard_bee", "phytotox",
                                "action_character", "min_order", "package_sizes") if not row[k]]
            gaps.append((cat, name, slug, miss, notes))
        if slug not in have_price:
            prices.append(dict(slug=slug, price=str(int(d["price"]["amount"]))))
            have_price.add(slug)

    # Серии: бренд из 2 и более препаратов в каталоге (ПИ06)
    first = {}
    for r in rows:
        first.setdefault(re.match(r"[А-ЯЁа-яё]+", r["name"]).group(0), []).append(r)
    for word, rs in first.items():
        if len(rs) >= 2:
            for r in rs:
                if not r["series"]:
                    r["series"] = word

    with open(pfile, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    with open(prfile, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "price"], lineterminator="\n")
        w.writeheader()
        w.writerows(prices)
    with open(mfile, encoding="utf-8", newline="") as f:
        makers = list(csv.DictReader(f))
    for slug, nm, badge in NEW_MAKERS:
        if slug not in {m["slug"] for m in makers}:
            makers.append(dict(slug=slug, name=nm, badge=badge))
    with open(mfile, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["slug", "name", "badge"], lineterminator="\n")
        w.writeheader()
        w.writerows(makers)

    Path(report_path).write_text(json.dumps(gaps, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Препаратов в каталоге: {len(rows)}, цен: {len(prices)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
