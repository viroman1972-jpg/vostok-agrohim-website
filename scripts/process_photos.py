"""Очистка фото упаковок: вырезка фона, ровный фон #FCFAF3, мягкая тень, квадрат (ДЗ09, план фото шаг 5).
Пиксели упаковки не перерисовываются — только вырезаются и масштабируются, поэтому этикетка не искажается.
Не входит в сборку сайта; нужны rembg и onnxruntime (pip install rembg onnxruntime).

Использование: process_photos.py ВХОД... --out ПАПКА [--sheet ЛИСТ.png]
ВХОД — файл исходника; результат: ПАПКА/<имя>-1000.webp, ПАПКА/<имя>-480.webp, ПАПКА/<имя>-mask.png."""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BG = (252, 250, 243)  # #FCFAF3 — фон карточек сайта
SIZE = 1000
FILL_H, FILL_W = 0.84, 0.80  # доля кадра под упаковку по высоте и ширине
BASE_Y = 0.93                # где стоит дно упаковки


def cut(img, session):
    from rembg import remove
    rgba = remove(img, session=session, post_process_mask=True)
    a = rgba.getchannel("A").point(lambda v: 255 if v > 128 else 0)  # без полупрозрачных ореолов фона
    return a


def compose(img, alpha):
    box = alpha.getbbox()
    obj, a = img.crop(box), alpha.crop(box)
    k = min(SIZE * FILL_H / obj.height, SIZE * FILL_W / obj.width)
    w, h = round(obj.width * k), round(obj.height * k)
    obj, a = obj.resize((w, h), Image.LANCZOS), a.resize((w, h), Image.LANCZOS)
    x, y = (SIZE - w) // 2, round(SIZE * BASE_Y) - h
    canvas = Image.new("RGB", (SIZE, SIZE), BG)
    sh = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(sh).ellipse((x + w * 0.06, y + h - h * 0.025, x + w * 0.94, y + h + h * 0.035), fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(SIZE * 0.018))
    canvas.paste(Image.new("RGB", (SIZE, SIZE), (60, 55, 45)), (0, 0), sh)
    canvas.paste(obj, (x, y), a)
    return canvas


def sheet(pairs, path, per_sheet=20, cols=4):
    """Листы «до / после»: по per_sheet пар, cols пар в ряд; путь ЛИСТ.png → ЛИСТ-01.png, ЛИСТ-02.png…"""
    W = 260
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    path = Path(path)
    for n in range(0, len(pairs), per_sheet):
        part = pairs[n:n + per_sheet]
        rows = (len(part) + cols - 1) // cols
        out = Image.new("RGB", (W * 2 * cols, (W + 26) * rows), "white")
        d = ImageDraw.Draw(out)
        for k, (name, before, after) in enumerate(part):
            x0, y0 = (k % cols) * W * 2, (k // cols) * (W + 26)
            for j, im in enumerate((before, after)):
                t = im.copy(); t.thumbnail((W - 8, W - 8))
                out.paste(t, (x0 + j * W + (W - t.width) // 2, y0 + 4))
            d.text((x0 + 6, y0 + W + 2), f"{n + k + 1}. {name}", fill="black", font=font)
        out.save(path.with_name(f"{path.stem}-{n // per_sheet + 1:02d}{path.suffix}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--sheet")
    ap.add_argument("--model", default="birefnet-general")
    args = ap.parse_args()
    from rembg import new_session
    session = new_session(args.model)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    pairs = []
    for f in map(Path, args.inputs):
        img = Image.open(f).convert("RGB")
        alpha = cut(img, session)
        res = compose(img, alpha)
        alpha.save(out / f"{f.stem}-mask.png")
        res.save(out / f"{f.stem}-1000.webp", quality=88, method=6)
        res.resize((480, 480), Image.LANCZOS).save(out / f"{f.stem}-480.webp", quality=88, method=6)
        pairs.append((f.stem, img, res))
        print(f"{f.stem}: готово")
    if args.sheet:
        sheet(pairs, args.sheet)


if __name__ == "__main__":
    main()
