#!/usr/bin/env python3
"""Готує згенеровані елементи (мазки й крейди) з папки `пастель/` у ассети.

Мазки приходять намальованими на власному аркуші паперу. Його треба прибрати
зовсім, інакше на сторінці буде видно прямокутник. Вирізати по яскравості не
можна: «зуб» паперу всередині мазка теж світлий і має лишитися дірками, крізь
які видно фактуру самої сторінки.

Тому пігмент відділяємо за насиченістю й темрявою — папір нейтральний і
світлий, пігмент кольоровий — і зберігаємо цю вагу як альфу. Так мазок лягає
на будь-який фон без blend-режимів.

Два обʼємні предмети приходять із альфою — їх просто обрізаємо по bbox.
"""
import numpy as np, pathlib, re, sys
from PIL import Image, ImageFilter

SRC = pathlib.Path(__file__).parent.parent.parent / "пастель"
OUT = pathlib.Path(__file__).parent / "assets"
# мітка часу з імені файлу → елемент. Імена ChatGPT відрізняються за локаллю,
# тож на сортування за назвою покладатися не можна.
NAMES = {
    "12_48_19": "sweep",   "12_48_25": "bands",  "12_48_30": "broken",
    "12_48_36": "stick",   "12_48_46": "dashes", "12_48_53": "divider",
    "17_03_25": "objects", "17_12_18": "ways",
    "17_44_56": "who",     "17_46_43": "how",    "17_48_40": "bonus",
    "18_07_14": "chalk",
}

def flatten(im, block=64):
    """Прибирає віньєтку й нерівність освітлення: ділимо на локально-світлий рівень."""
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    pad = np.pad(a, ((0, (-h) % block), (0, (-w) % block), (0, 0)), mode="edge")
    H, W = pad.shape[0] // block, pad.shape[1] // block
    tiles = pad.reshape(H, block, W, block, 3).transpose(0, 2, 1, 3, 4).reshape(H, W, -1, 3)
    bg = np.percentile(tiles, 92, axis=2)
    bg = Image.fromarray(np.clip(bg, 1, 255).astype(np.uint8)).resize((pad.shape[1], pad.shape[0]), Image.BICUBIC)
    bg = np.asarray(bg.filter(ImageFilter.GaussianBlur(block / 2))).astype(np.float32)[:h, :w]
    return np.clip(a / np.maximum(bg, 1) * 255.0, 0, 255)

def pigment(im, floor=.38):
    """floor нижче — зберігається більше блідого пігменту. Розтерта пальцем
    пляма майже ненасичена, при жорсткому порозі від неї лишається розсип."""
    a = flatten(im)
    weight = np.clip((np.maximum((a.max(2) - a.min(2)) / 16.0, (255.0 - a.mean(2)) / 64.0) - floor) / (1 - floor), 0, 1)
    rgba = np.dstack([a, weight * 255.0])
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8)), weight

def harden_alpha(im, lo=100, hi=215):
    """Генератор віддає предмети з мʼякою альфою: навколо зламаної крейди йде
    напівпрозорий білий ореол. Розтягуємо альфу так, щоб тіло стало щільним,
    а ореол пішов у нуль."""
    import numpy as np
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    # білуватий «туман» пилу: світлий, ненасичений і напівпрозорий одночасно.
    # Щільні частини предмета (обгортка крейди) мають повну альфу й не чіпаються.
    fog = (rgb.mean(2) > 200) & ((rgb.max(2) - rgb.min(2)) < 18) & (al < 240)
    al = np.where(fog, 0.0, al)
    a[..., 3] = np.clip((al - lo) / (hi - lo) * 255.0, 0, 255)
    out = Image.fromarray(a.astype(np.uint8))
    return out.crop(out.getchannel("A").getbbox())

def bands(mask, frac=.013, min_h=.02, merge_gap=.012):
    """Горизонтальні смуги з пігментом. Сусідні смуги зливаємо, якщо між ними
    менше merge_gap висоти аркуша — інакше хмарка пилу над коробкою або крапка
    над знаком стає окремим елементом."""
    on = mask.sum(1) > mask.shape[1] * frac
    raw, start = [], None
    for i, v in enumerate(on):
        if v and start is None: start = i
        if not v and start is not None: raw.append((start, i)); start = None
    if start is not None: raw.append((start, len(on)))
    merged = []
    for a, b in raw:
        if merged and a - merged[-1][1] < mask.shape[0] * merge_gap:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return [(a, b) for a, b in merged if b - a > mask.shape[0] * min_h]


def box(mask, frac_x=.02, frac_y=.02):
    rows = np.where(mask.sum(1) > mask.shape[1] * frac_y)[0]
    cols = np.where(mask.sum(0) > mask.shape[0] * frac_x)[0]
    return cols.min(), rows.min(), cols.max() + 1, rows.max() + 1

def pad_crop(im, b, pad=.05):
    x0, y0, x1, y1 = b
    px, py = int((x1 - x0) * pad) + 2, int((y1 - y0) * pad) + 2
    return im.crop((max(0, x0 - px), max(0, y0 - py), min(im.width, x1 + px), min(im.height, y1 + py)))

def save(im, name, cap=900, q=84):
    im = im.copy(); im.thumbnail((cap, cap), Image.LANCZOS)
    im.save(OUT / f"el-{name}.webp", "WEBP", quality=q, method=6)
    print(f"  el-{name}.webp  {im.width}x{im.height}  ratio {im.width/im.height:.2f}  "
          f"{(OUT/f'el-{name}.webp').stat().st_size//1024} KB")

def main():
    pairs, unknown = [], []
    for f in sorted(SRC.glob("ChatGPT*.png")):
        stamp = re.search(r"(\d\d_\d\d_\d\d)", f.name)
        key = stamp.group(1) if stamp else None
        (pairs.append((f, NAMES[key])) if key in NAMES else unknown.append(f.name))
    if unknown:
        print("невідомі файли (пропускаю):", *unknown, sep="\n  ")
    for f, name in pairs:
        src = Image.open(f)
        if name in ("objects", "bonus"):               # предмети в ряд однією картинкою
            im = harden_alpha(src)
            al = np.asarray(im)[..., 3] > 8
            cols = al.sum(0) > al.shape[0] * .004
            spans, start = [], None
            for i, v in enumerate(cols):
                if v and start is None: start = i
                if not v and start is not None:
                    if i - start > im.width * .04: spans.append((start, i))
                    start = None
            if start is not None: spans.append((start, len(cols)))
            print(f"  предметів: {len(spans)}")
            slugs = ("set", "paper", "kneaded") if name == "objects" else ("bonus-1", "bonus-2")
            for (x0, x1), nm in zip(spans, slugs):
                piece = im.crop((max(0, x0 - 6), 0, min(im.width, x1 + 6), im.height))
                save(piece.crop(piece.getchannel("A").getbbox()), nm, cap=800)
            continue
        if "A" in src.getbands():                      # обʼємні предмети
            save(harden_alpha(src), name, cap=900)
            continue
        im, w = pigment(src)
        mask = w > .2                                  # маска геометрії: жорсткий поріг, щоб межі позначок були чіткі
        if name == "ways":                             # пікселі беремо з мʼякого порогу — інакше зникає розтерта пляма
            im, _ = pigment(src, floor=.17)
        if name == "dashes":                           # аркуш свотчів ріжемо на штрихи
            rows = mask.sum(1) > mask.shape[1] * .006
            spans, start = [], None
            for i, v in enumerate(rows):
                if v and start is None: start = i
                if not v and start is not None:
                    if i - start > 20: spans.append((start, i))
                    start = None
            if start is not None and len(rows) - start > 20: spans.append((start, len(rows)))
            print(f"  свотчів: {len(spans)}")
            for i, (y0, y1) in enumerate(spans, 1):
                sub, subm = im.crop((0, y0, im.width, y1)), mask[y0:y1]
                cols = np.where(subm.sum(0) > subm.shape[0] * .02)[0]
                save(sub.crop((max(0, cols.min() - 4), 0, min(sub.width, cols.max() + 5), sub.height)),
                     f"dash-{i}", cap=240)
        elif name in ("who", "how", "chalk"):          # аркуші піктограм
            im, _ = pigment(src, floor=.2)             # мʼякший поріг: у малюнках багато світлої заливки
            spans = bands(mask)
            print(f"  піктограм: {len(spans)}")
            for i, (y0, y1) in enumerate(spans, 1):
                pad = int((y1 - y0) * .06)
                sub = im.crop((0, max(0, y0 - pad), im.width, min(im.height, y1 + pad)))
                subm = mask[max(0, y0 - pad):min(im.height, y1 + pad)]
                cols = np.where(subm.sum(0) > subm.shape[0] * .015)[0]
                save(sub.crop((max(0, cols.min() - 6), 0, min(sub.width, cols.max() + 7), sub.height)),
                     f"{name}-{i}", cap=300)
            continue
        elif name == "ways":                           # чотири позначки одним аркушем
            rows = mask.sum(1) > mask.shape[1] * .006
            spans, start = [], None
            for i, v in enumerate(rows):
                if v and start is None: start = i
                if not v and start is not None:
                    if i - start > 24: spans.append((start, i))
                    start = None
            if start is not None and len(rows) - start > 24: spans.append((start, len(rows)))
            print(f"  позначок: {len(spans)}")
            for (y0, y1), nm in zip(spans, ("way-side", "way-tip", "way-finger", "tick")):
                sub, subm = im.crop((0, y0, im.width, y1)), mask[y0:y1]
                cols = np.where(subm.sum(0) > subm.shape[0] * .02)[0]
                save(sub.crop((max(0, cols.min() - 5), 0, min(sub.width, cols.max() + 6), sub.height)), nm, cap=420)
            continue
        elif name == "divider":                        # мазок на всю ширину: ріжемо лише по вертикалі
            rows = np.where(mask.sum(1) > mask.shape[1] * .03)[0]
            pad = int((rows.max() - rows.min()) * .5)
            save(im.crop((0, max(0, rows.min() - pad), im.width, min(im.height, rows.max() + pad))), name, cap=1400)
        else:
            save(pad_crop(im, box(mask)), name)

if __name__ == "__main__":
    main()
