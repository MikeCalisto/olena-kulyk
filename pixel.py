# -*- coding: utf-8 -*-
"""Meta Pixel — одне місце, з якого його тягнуть усі сторінки.

ID міняється тільки тут. `sync()` перезаписує /pixel.js і вшиває в <head>
кожної .html однаковий блок між маркерами. Функція ідемпотентна: якщо блок
уже стоїть, він замінюється новим, а не дублюється, тож зміна ID підхоплюється
наступною збіркою на всіх сторінках одразу.
"""
import pathlib
import re

PIXEL_ID = "1643966413961899"
ROOT = pathlib.Path(__file__).parent

OPEN, CLOSE = "<!-- Meta Pixel -->", "<!-- /Meta Pixel -->"

JS = """/* Meta Pixel. Не редагувати руками — файл перезаписує pixel.py. */
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '%s');
fbq('track', 'PageView');
""" % PIXEL_ID

# noscript-піксель мусить бути картинкою в розмітці, JS його не підставить,
# тому ID тут дублюється — але підставляє його той самий PIXEL_ID вище.
SNIPPET = (
    f"{OPEN}\n"
    '<script src="/pixel.js" async></script>\n'
    '<noscript><img height="1" width="1" style="display:none" alt=""\n'
    f'src="https://www.facebook.com/tr?id={PIXEL_ID}&amp;ev=PageView&amp;noscript=1"></noscript>\n'
    f"{CLOSE}"
)


def stamp(html):
    """Вшиває блок одразу після <meta charset>. Уже вшитий — переставляє новий.

    Саме туди, а не перед </head>: patch_v2.py вклеює CSS сцен по якорю
    "</style>\\n</head>", і блок між ними ламав би збірку. Та й пікселю
    корисніше стартувати раніше.
    """
    if OPEN in html:
        i = html.index(OPEN)
        j = html.index(CLOSE, i) + len(CLOSE)
        if html[j:j + 1] == "\n":      # інакше на місці блоку лишиться порожній рядок
            j += 1
        html = html[:i] + html[j:]

    m = re.search(r"<meta\s+charset=[^>]*>", html, re.I) or re.search(r"<head[^>]*>", html, re.I)
    if not m:
        return None            # нема куди вшивати — sync() поскаржиться
    k = m.end()
    return html[:k] + "\n" + SNIPPET + html[k:]


def sync(verbose=True):
    (ROOT / "pixel.js").write_text(JS, encoding="utf-8")
    touched, skipped = [], []
    for f in sorted(ROOT.rglob("*.html")):
        if "preview" in f.parts:
            continue
        t = f.read_text(encoding="utf-8")
        n = stamp(t)
        if n is None:
            skipped.append(f.relative_to(ROOT))
            continue
        if n != t:
            f.write_text(n, encoding="utf-8")
            touched.append(f.relative_to(ROOT))
    if verbose:
        print(f"піксель {PIXEL_ID}: оновлено сторінок — {len(touched)}")
        for t in touched:
            print("  ", t)
    return touched


if __name__ == "__main__":
    sync()
