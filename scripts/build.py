"""Сборка сайта: data/*.csv + site/templates -> dist/. Цены берутся только из prices.csv."""
import csv, shutil, sys
from pathlib import Path
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent.parent

def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def money(v):
    return f"{int(float(v)):,}".replace(",", " ") + " ₽"

def build(data=ROOT / "data", tpl=ROOT / "site" / "templates", out=ROOT / "dist"):
    s = yaml.safe_load((data / "settings.yml").read_text(encoding="utf-8"))
    prices = {r["slug"]: r["price"] for r in read_csv(data / "prices.csv")}
    products = read_csv(data / "products.csv")
    for p in products:
        if p["slug"] not in prices:
            sys.exit(f"Нет цены для {p['slug']} в prices.csv")
        p["price_text"] = money(prices[p["slug"]])
    env = Environment(loader=FileSystemLoader(tpl), undefined=StrictUndefined, autoescape=True)
    if out.exists():
        shutil.rmtree(out)
    def write(rel, html):
        f = out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    write("index.html", env.get_template("home.html").render(s=s, title="Главная", products=products))
    write("gerbicidy/index.html", env.get_template("listing.html").render(s=s, title="Гербициды", products=products))
    for p in products:
        write(f"p/{p['slug']}/index.html", env.get_template("product.html").render(s=s, title=p["name"], p=p))
    return out

if __name__ == "__main__":
    o = build()
    print(f"Собрано страниц: {sum(1 for _ in o.rglob('*.html'))} в {o}")
