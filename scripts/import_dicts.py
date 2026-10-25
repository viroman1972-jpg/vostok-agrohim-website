"""Разовый перенос словарей и связей каталога в data/dict/ и data/links/ (этап 2, «Словари и связи»).

Словари: культуры (52), вредные объекты (68) и действующие вещества (64) — из phase-4-content/dictionary-*.md,
слаги — из dictionary-slugs-v1.md. Культуры — с родителем и группой, объекты — с подтипом, ДВ — с химклассом
(без кодов HRAC/FRAC/IRAC).
Связи препарат → культура и препарат → объект — только по госреестру: снимок регламентов agroxxi
phase-4-content/registry-links-agroxxi-2026-10-24.tsv (ПИ10). Разметка по satom (product-*-mapping-v1.md)
только сравнивается со снимком, расхождения — в отчёт. Препарат → ДВ — по полю dv_text таблицы каталога
(сверено с agroxxi 23.10.2026); антидоты в связи не попадают (в фильтр ДВ не выносятся).
Опубликованные препараты — по тем же правилам (решение Оли 24.10.2026, ПИ10).
Запуск: python -I scripts/import_dicts.py <отчёт.md>
"""
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
P4 = ROOT / "phase-4-content"
DATA = ROOT / "data"
REGISTRY = P4 / "registry-links-agroxxi-2026-10-24.tsv"

PEST_TYPE = {"Сорные растения": "sornyak", "Болезни": "bolezn", "Вредители": "vreditel"}
SUB_KIND = {"Пестициды": "pestitsid", "S": "antidot", "B": "bio", "A": "pav"}
NAME_ALIAS = {"тебузилкс": "tebuzil-tks"}  # в разметке старое название формы
DV_ALIAS = {"дикват": "dikvat-dibromid"}  # в таблице каталога без соли
# Регистрация истекла, действующей нет (К12): регламент в снимке есть, связи не создаются до решения заказчика
EXPIRED = {"lemur-ke": "12.03.2025", "shaman-ke": "21.06.2026"}


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(fields)
        w.writerows(rows)


def md_rows(text):
    """Строки markdown-таблиц как списки ячеек (без заголовков и разделителей)."""
    for line in text.splitlines():
        if line.startswith("| ") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells[0] not in ("ID", "#", "Буква", "Значение", "Что проверено", "satom-значение", "Новый C-код"):
                yield cells


def plain(s):
    return re.sub(r"\*\*|`", "", s).strip()


def load_slugs():
    """ID → (значение, слаг, раздел) из dictionary-slugs-v1.md."""
    out, section = {}, None
    for line in (P4 / "dictionary-slugs-v1.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") or line.startswith("### "):
            section = line.lstrip("#").strip()
        m = re.match(r"^\| (\w+) \| (.+?) \| `([a-z0-9-]+)`", line)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3), section)
    return out


def build_dicts(slugs):
    crops_md = {plain(c[0]): c for c in md_rows((P4 / "dictionary-crops-v1.md").read_text(encoding="utf-8"))
                if re.match(r"C\d", plain(c[0])) and len(c) == 6}
    crops = []
    for cid, (name, slug, sec) in slugs.items():
        if cid.startswith("C"):
            c = crops_md[cid]
            parent = slugs[c[2]][1] if c[2] in slugs else ""
            crops.append((slug, name, parent, c[3]))
    pests = [(slug, name, PEST_TYPE[sec]) for cid, (name, slug, sec) in slugs.items() if sec in PEST_TYPE]
    chem = {}
    for c in md_rows((P4 / "dictionary-active-ingredients-v1.md").read_text(encoding="utf-8")):
        if re.match(r"(DV\d+|[SBA]\d)$", c[0]) and len(c) >= 3:
            chem[c[0]] = c[2].split(" / ")[0].strip()
    subs = []
    for cid, (name, slug, sec) in slugs.items():
        if cid.startswith("DV"):
            subs.append((slug, name, chem[cid], SUB_KIND["Пестициды"]))
        elif re.match(r"[SBA]\d$", cid):
            subs.append((slug, name, chem[cid], SUB_KIND[cid[0]]))
    assert (len(crops), len(pests), len(subs)) == (52, 68, 64), (len(crops), len(pests), len(subs))
    return crops, pests, subs


def key(name):
    return re.sub(r"[^а-яa-z0-9]", "", name.lower().replace("ё", "е"))


def load_mapping(fname, slugs, products):
    """Разметка по satom: slug препарата → множество слагов словаря."""
    keys = sorted(((key(p["name"]), p["slug"]) for p in products), key=lambda kv: -len(kv[0]))
    out = {}
    for c in md_rows((P4 / fname).read_text(encoding="utf-8")):
        if len(c) != 5 or not re.match(r"П", c[1]):
            continue
        k = key(c[2])
        slug = NAME_ALIAS.get(k) or next((s for pk, s in keys if k.startswith(pk)), None)
        if slug is None or slug in out:  # исключённые У02–У06; повтор в приложении Б
            continue
        out[slug] = {slugs[x][1] for x in re.findall(r"[CWDI]\d+a?", c[3]) if x in slugs}
    return out


def dv_links(p, subs):
    """Компоненты dv_text → слаги словаря ДВ (антидоты пропускаются)."""
    by_name = {re.sub(r"\s*\(.*\)", "", n).lower(): s for s, n, _, kind in subs if kind != "antidot"} | DV_ALIAS
    found, unknown = [], []
    for part in p["dv_text"].split(" + "):
        part = re.sub(r"\([^)]*\)", "", part).strip()
        if not part or part.lower().startswith("антидот"):
            continue
        nm = re.split(r",\s+\d", part)[0].strip().lower()
        (found.append(by_name[nm]) if nm in by_name else unknown.append(nm))
    return found, unknown


def main(report_path):
    slugs = load_slugs()
    crops, pests, subs = build_dicts(slugs)
    write_csv(DATA / "dict" / "crops.csv", ["slug", "name", "parent", "group"], crops)
    write_csv(DATA / "dict" / "pests.csv", ["slug", "name", "type"], pests)
    write_csv(DATA / "dict" / "substances.csv", ["slug", "name", "chem_class", "kind"], subs)

    products = read_csv(DATA / "products.csv")
    order = {s: i for i, s in enumerate([c[0] for c in crops] + [p[0] for p in pests])}
    reg = {r["slug"]: r for r in read_csv_tsv(REGISTRY)}
    known = set(order)

    def links(name, field, reg_field):
        rows = []
        for p in products:
            if p["slug"] not in reg or p["slug"] in EXPIRED:
                continue
            vals = reg[p["slug"]][reg_field].split()
            bad = [v for v in vals if v not in known]
            assert not bad, (p["slug"], bad)
            rows += [(p["slug"], v) for v in sorted(vals, key=order.get)]
        write_csv(DATA / "links" / name, ["slug", field], rows)
        return rows
    crop_rows = links("product_crop.csv", "crop", "crops")
    pest_rows = links("product_pest.csv", "pest", "pests")

    sub_rows = []
    dv_unknown = {}
    for p in products:
        found, unknown = dv_links(p, subs)
        sub_rows += [(p["slug"], s) for s in found]
        if unknown or not found:
            dv_unknown[p["slug"]] = unknown
    write_csv(DATA / "links" / "product_substance.csv", ["slug", "substance"], sub_rows)

    m_crop = load_mapping("product-crop-mapping-v1.md", slugs, products)
    m_pest = load_mapping("product-pest-mapping-v1.md", slugs, products)
    write_report(report_path, products, reg, m_crop, m_pest, crop_rows, pest_rows, sub_rows, dv_unknown,
                 crops, pests, subs)


def read_csv_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_report(path, products, reg, m_crop, m_pest, crop_rows, pest_rows, sub_rows, dv_unknown,
                 crops, pests, subs):
    name = {p["slug"]: p["name"] for p in products}
    cname = {c[0]: c[1] for c in crops}
    pname = {p[0]: p[1] for p in pests}
    L = []
    no_reg = [p["slug"] for p in products if p["slug"] not in reg]
    L.append(f"Связи с культурами: {len(crop_rows)}, с вредными объектами: {len(pest_rows)}, с ДВ: {len(sub_rows)}.")
    L.append("")
    L.append("Препараты без связей с культурами и объектами (нет регламента в госреестре): "
             + ", ".join(name[s] for s in no_reg) + ".")
    L.append("Регистрация истекла, связи не созданы (К12): "
             + ", ".join(f"{name[s]} — {d}" for s, d in EXPIRED.items()) + ".")
    L.append("")
    used_c = {v for _, v in crop_rows}
    used_p = {v for _, v in pest_rows}
    used_s = {v for _, v in sub_rows}
    L.append("Значения словарей без единого препарата (страниц не получают): ")
    L.append("- культуры: " + (", ".join(cname[c[0]] for c in crops if c[0] not in used_c) or "нет"))
    L.append("- объекты: " + (", ".join(pname[p[0]] for p in pests if p[0] not in used_p) or "нет"))
    L.append("- ДВ: " + (", ".join(s[1] for s in subs if s[0] not in used_s and s[3] != "antidot") or "нет"))
    L.append("")
    if dv_unknown:
        L.append("ДВ не сопоставлены со словарём:")
        for s, u in dv_unknown.items():
            L.append(f"- {name[s]}: " + (", ".join(u) if u else "в таблице каталога нет состава"))
        L.append("")
    L.append("| Препарат | Культуры: нет в госреестре (убрано) | Культуры: добавлено по госреестру | Объекты: убрано | Объекты: добавлено |")
    L.append("|---|---|---|---|---|")
    for p in products:
        s = p["slug"]
        if s not in reg or s in EXPIRED:
            continue
        rc, rp = set(reg[s]["crops"].split()), set(reg[s]["pests"].split())
        mc, mp = m_crop.get(s, set()), m_pest.get(s, set())
        cells = [", ".join(cname[x] for x in sorted(mc - rc)), ", ".join(cname[x] for x in sorted(rc - mc)),
                 ", ".join(pname[x] for x in sorted(mp - rp)), ", ".join(pname[x] for x in sorted(rp - mp))]
        if any(cells):
            L.append(f"| {p['name']} | " + " | ".join(c or "—" for c in cells) + " |")
    Path(path).write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
