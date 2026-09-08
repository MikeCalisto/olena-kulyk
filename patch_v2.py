#!/usr/bin/env python3
"""Збирає morskyi-peyzazh-v2 з проду і вшиває три предметні сцени (блоки 3, 4, 7).

Ідемпотентний: щоразу копіює свіжий morskyi-peyzazh/index.html і накладає
objects.css + сцени. Запуск:  python3 patch_v2.py
"""
import pathlib, re
import copy_edits

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE / "morskyi-peyzazh-v2"
SCRATCH = HERE
A = "/morskyi-peyzazh/assets"

def ver(name):
    """?v=<mtime> у посиланні. Ассети віддаються з річним immutable-кешем, тож
    без версії браузер, який уже качав файл, показував би старий ролик."""
    f = ROOT.parent / "morskyi-peyzazh" / "assets" / name
    return f"{A}/{name}?v={int(f.stat().st_mtime)}"


SPRITE = """
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<symbol id="o-brush" viewBox="0 0 24 24"><path d="M4 20.5c2.2.4 3.7-.6 4.3-2.3.5-1.5-.3-2.9-1.6-3.2-1.5-.4-2.6.6-2.8 2-.2 1.4-.4 2.7.1 3.5Z"/><path d="M8.9 15.2 18.4 5.7a1.9 1.9 0 0 1 2.7 2.7l-9.5 9.5"/></symbol>
<symbol id="o-palette" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.8-.8 1.8-1.7 0-1.6 1-2.3 2.4-2.3H18a3.5 3.5 0 0 0 3.5-3.5C21.5 7.6 17.4 3 12 3Z"/><circle cx="7.6" cy="12.2" r="1.1"/><circle cx="9.6" cy="7.9" r="1.1"/><circle cx="14.4" cy="7.3" r="1.1"/><circle cx="17.6" cy="10.6" r="1.1"/></symbol>
<symbol id="o-tube" viewBox="0 0 24 24"><path d="M9 3h6v2.4H9z"/><path d="M8.2 5.4h7.6l1 3.2v10a2.4 2.4 0 0 1-2.4 2.4H9.6a2.4 2.4 0 0 1-2.4-2.4v-10z"/><path d="M7.4 11.6h9.2"/></symbol>
<symbol id="o-canvas" viewBox="0 0 24 24"><rect x="3.4" y="4" width="17.2" height="12.4" rx="1.4"/><path d="M3.4 12.6 8 9l3.4 2.6L15.6 7l5 4.4"/><path d="M12 16.4V21M8.4 21h7.2"/></symbol>
<symbol id="o-wave" viewBox="0 0 24 24"><path d="M2.5 9.5c1.9 0 1.9 1.8 3.8 1.8s1.9-1.8 3.8-1.8 1.9 1.8 3.8 1.8 1.9-1.8 3.8-1.8 1.9 1.8 3.8 1.8"/><path d="M2.5 15c1.9 0 1.9 1.8 3.8 1.8S8.2 15 10.1 15s1.9 1.8 3.8 1.8S15.8 15 17.7 15s1.9 1.8 3.8 1.8"/></symbol>
<symbol id="o-drop" viewBox="0 0 24 24"><path d="M12 3.2c3.4 4 6.2 7 6.2 10.2A6.2 6.2 0 0 1 5.8 13.4c0-3.2 2.8-6.2 6.2-10.2Z"/></symbol>
<symbol id="o-clock" viewBox="0 0 24 24"><circle cx="12" cy="13" r="8.4"/><path d="M12 8.6V13l3 2M9.4 2.6h5.2"/></symbol>
<symbol id="o-doc" viewBox="0 0 24 24"><path d="M13.6 2.8H7a2 2 0 0 0-2 2v14.4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.2z"/><path d="M13.6 2.8v5.4H19M8.6 13h6.8M8.6 16.6h4.6"/></symbol>
<symbol id="o-frame" viewBox="0 0 24 24"><rect x="4" y="3.4" width="16" height="17.2" rx="1.4"/><rect x="7.2" y="6.6" width="9.6" height="10.8" rx=".8"/></symbol>
<symbol id="o-gift" viewBox="0 0 24 24"><rect x="3.4" y="9.4" width="17.2" height="11.4" rx="1.6"/><path d="M3.4 13.6h17.2M12 9.4v11.4"/><path d="M12 9.4S10.6 4.6 8.2 4.6a2.2 2.2 0 0 0 0 4.8h3.8Zm0 0s1.4-4.8 3.8-4.8a2.2 2.2 0 0 1 0 4.8H12Z"/></symbol>
<symbol id="o-cart" viewBox="0 0 24 24"><path d="M2.6 3.6h2.6l2.4 11.2h9.8l2-7.6H6.4"/><circle cx="9.4" cy="19.4" r="1.6"/><circle cx="17" cy="19.4" r="1.6"/></symbol>
</defs></svg>
"""

STAGE_BRUSHES = f"""  <div class="obj-art st-brushes reveal" aria-hidden="true">
    <img class="obj" src="{A}/obj-brushes.webp" alt="" width="586" height="900" loading="lazy" decoding="async">
    <span class="obj-chip k1"><svg><use href="#o-brush"/></svg></span>
    <span class="obj-chip k2"><svg><use href="#o-wave"/></svg></span>
    <span class="obj-chip k3"><svg><use href="#o-canvas"/></svg></span>
  </div>
"""

STAGE_TUBES = f"""  <div class="obj-art st-tubes reveal" aria-hidden="true">
    <img class="obj" src="{A}/obj-paint.webp" alt="" width="710" height="900" loading="lazy" decoding="async">
  </div>
"""

STAGE_PALETTE = f"""  <div class="obj-stage st-palette reveal" aria-hidden="true">
    <img class="obj" src="{A}/obj-palette.webp" alt="" width="821" height="900" loading="lazy" decoding="async">
    <span class="obj-chip k1"><svg><use href="#o-palette"/></svg></span>
    <span class="obj-chip k2"><svg><use href="#o-cart"/></svg></span>
    <span class="obj-chip k3"><svg><use href="#o-brush"/></svg></span>
  </div>
"""

STAGE_TOOLS = f"""  <div class="obj-stage st-tools" aria-hidden="true">
    <img class="obj" src="{A}/obj-tools.webp" alt="" width="620" height="900" loading="lazy" decoding="async">
  </div>
"""

STAGE_EASEL = f"""  <div class="obj-stage st-easel" aria-hidden="true">
    <img class="obj" src="{A}/obj-easel.webp" alt="" width="470" height="900" loading="lazy" decoding="async">
  </div>
"""

EXTRA_JS = """<script>
(function(){
  var sl=[].slice.call(document.querySelectorAll('.cyc img')),
      dt=[].slice.call(document.querySelectorAll('.cyc .dots i'));
  if(sl.length>1){
    var n=0; sl[0].className='on'; if(dt[0])dt[0].className='on';
    setInterval(function(){
      sl[n].className=''; if(dt[n])dt[n].className='';
      n=(n+1)%sl.length;
      sl[n].className='on'; if(dt[n])dt[n].className='on';
    },3600);
  }
  var vs=[].slice.call(document.querySelectorAll('.vidbox video'));
  if(vs.length&&'IntersectionObserver'in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      var v=e.target;
      if(e.isIntersecting){
        v.preload='auto';
        var pr=v.play();
        if(pr&&pr.catch)pr.catch(function(){
          v.addEventListener('canplay',function(){v.play().catch(function(){})},{once:true});
        });
      } else v.pause();
    })},{threshold:.25});
    vs.forEach(function(v){io.observe(v)});
  }
})();
</script>
"""


# --- 0. свіжа копія посадки (скрипт ідемпотентний) ---
SRC = ROOT.parent / "morskyi-peyzazh"
ROOT.mkdir(exist_ok=True)
for f in ("index.html", "politika.html", "oferta.html"):
    t = (SRC / f).read_text(encoding="utf-8")
    t = t.replace("/morskyi-peyzazh/assets/", "assets/").replace("assets/", "/morskyi-peyzazh/assets/")
    t = t.replace('href="politika.html"', 'href="/morskyi-peyzazh-v2/politika.html"')
    t = t.replace('href="oferta.html"', 'href="/morskyi-peyzazh-v2/oferta.html"')
    if f == "index.html":
        t = t.replace('<meta name="description"', '<meta name="robots" content="noindex">\n<meta name="description"', 1)
        t = t.replace("<title>Швидкий морський пейзаж — міні-курс Олени Кулик Діріл</title>",
                      "<title>Швидкий морський пейзаж — v2 (великі обʼєкти)</title>")
    (ROOT / f).write_text(t, encoding="utf-8")

p = ROOT / "index.html"
s = p.read_text(encoding="utf-8")

# 1. CSS сцен — останнім у <style>, щоб перекривало базові правила
css = (SCRATCH / "objects.css").read_text(encoding="utf-8")
assert s.count("</style>\n</head>") == 1
s = s.replace("</style>\n</head>", css + "</style>\n</head>", 1)

# 2. спрайт іконок
assert s.count('<div class="phone">') == 1
s = s.replace('<div class="phone">', '<div class="phone">\n' + SPRITE, 1)


def to_row(block, art_cls, last_chip, lead_open, lead_close, tail_open=None, tail_end_text=None):
    """Складає предмет і текстові елементи в паралельний рядок."""
    i = block.index(f'<div class="{art_cls}'.replace(art_cls, f'obj-art {art_cls}'))
    anchor = block.index('</span>', block.rindex(last_chip, i)) if last_chip else i
    j = block.index('</div>', anchor) + len('</div>')
    art = block[i:j]
    k = block.index(lead_open, j)
    m = block.index(lead_close, k) + len(lead_close)
    lead = block[k:m]
    if tail_open:
        c = block.index(tail_open, m)
        c_end = block.index('</div>', block.index(tail_end_text, c)) + len('</div>')
        tail = '\n' + block[c:c_end]
    else:
        tail, c_end = '', m
    return (block[:i] + '  <div class="obj-row">\n' + art
            + '\n    <div class="obj-col">\n' + lead + tail
            + '\n    </div>\n  </div>' + block[c_end:])


def patch_section(text, marker, old_tag, new_tag, stage, anchor="</h2>"):
    """Міняє клас секції й ставить сцену одразу після anchor (типово — заголовка)."""
    i = text.index(marker)
    j = text.index("</section>", i) + len("</section>")
    block = text[i:j]
    assert old_tag in block, marker
    block = block.replace(old_tag, new_tag, 1)
    k = block.index(anchor) + len(anchor)
    block = block[:k] + "\n\n" + stage.rstrip() + block[k:]
    return text[:i] + block + text[j:], (i, i + len(block))


# 3. блок 3 — кисті на глибокому синьому
s, span3 = patch_section(
    s, "<!-- ==================== 3. ЧОМУ САМЕ ЦЯ КАРТИНА",
    '<section class="sec sec-paper">', '<section class="sec obj-sec dark">', STAGE_BRUSHES)
b3 = s[span3[0]:span3[1]].replace('<div class="closebox reveal d1">', '<div class="obj-close reveal d1">', 1)
b3 = b3.replace('<p class="lead reveal d1" style="margin-top:22px;text-align:center">',
                '<p class="lead obj-lead reveal d1">', 1)
b3 = to_row(b3, 'st-brushes', 'obj-chip k3',
            '<p class="lead obj-lead reveal d1">', '</p>')
s = s[:span3[0]] + b3 + s[span3[1]:]

# 4. блок 4 — тюбики на піску
s, span4 = patch_section(
    s, "<!-- ==================== 4. ОЛІЯ ПРОСТІША ЗА АКВАРЕЛЬ",
    '<section class="sec sec-white">', '<section class="sec obj-sec sand">', STAGE_TUBES)
b4 = s[span4[0]:span4[1]].replace(
    '  <div class="emoji-rail reveal" aria-hidden="true"><span>💧</span><span>⚔️</span><span>🎨</span></div>\n', '', 1)
b4 = b4.replace('<p class="lead reveal d1" style="margin-top:20px">', '<p class="lead obj-lead reveal d1">', 1)
# сцена і абзац з\'єднуються в один рядок: предмет ліворуч, текст праворуч
b4 = to_row(b4, 'st-tubes', None,
            '<p class="lead obj-lead reveal d1">', '</p>',
            '<div class="callout reveal d2">', 'готової картини.')
s = s[:span4[0]] + b4 + s[span4[1]:]

# 5. блок 7 — палітра на глибокому морському
s, span7 = patch_section(
    s, "<!-- ==================== 7. МАТЕРІАЛИ",
    '<section class="sec sec-white">', '<section class="sec obj-sec deep">', STAGE_PALETTE)
b7 = s[span7[0]:span7[1]]
b7 = b7.replace(
    '  <div class="emoji-rail reveal" aria-hidden="true"><span>🛒</span><span>🖌</span><span>🎨</span></div>\n', '', 1)
# фото пензлів у білій рамці більше не потрібне — його роль грає предмет у блоці 3
i = b7.index('<div class="showcase reveal d1"')
j = b7.index('</div>', b7.index('</picture>', i)) + len('</div>')
j = b7.index('</div>', j) + len('</div>')
b7 = b7[:i] + b7[j:]
s = s[:span7[0]] + b7 + s[span7[1]:]

# 6. роздільник між блоками 3 і 4 — у колір піску
old = '<div class="divider alt" aria-hidden="true"><span class="ps ps-blue"></span></div>'
assert s.count(old) == 1
s = s.replace(old, '<div class="divider alt obj-div" aria-hidden="true"><span class="ps ps-blue"></span></div>', 1)

# 8. блок 8 «Програма» — мастихін і медіум
s, _ = patch_section(
    s, "<!-- ==================== 8. ПРОГРАМА",
    '<section class="sec sec-mint">', '<section class="sec sec-mint obj-sec mint">', STAGE_TOOLS,
    anchor='<section class="sec sec-mint obj-sec mint">')

# 9. блок 15 «Фінальний офер» — мольберт на вже темному фоні
s, _ = patch_section(
    s, "<!-- ==================== 15. ФІНАЛЬНИЙ ОФЕР",
    '<section class="sec sec-deep">', '<section class="sec sec-deep obj-sec">', STAGE_EASEL)


# 10. гірлянди емодзі над заголовками — прибрані з усіх блоків
rails = re.findall(r'[ \t]*<div class="emoji-rail[^>]*>.*?</div>\n', s)
assert len(rails) == 4, f"емодзі-гірлянд знайдено {len(rails)}, очікувалось 4"
for r in rails:
    s = s.replace(r, "", 1)


# 11. блок «Гарантія» переїжджає під «За чотири уроки ти»
i = s.index("<!-- ==================== 14. ГАРАНТІЯ")
i = s.rindex('<div class="divider"', 0, i)                    # разом із роздільником перед ним
j = s.index("</section>", i) + len("</section>")
guard = s[i:j].replace('<section class="sec sec-mint">', '<section class="sec sec-paper">', 1)
s = s[:i] + s[j:]
k = s.index("</section>", s.index("<!-- ==================== 10. ЧЕКЛІСТ")) + len("</section>")
s = s[:k] + "\n" + guard + s[k:]

# 12. «Мої роботи» — дванадцять справжніх робіт замість заглушок
old_gallery = s[s.index('<div class="gallery reveal d1">'):
               s.index('</div>', s.rindex('</figure>', 0, s.index('</div>', s.index('<div class="gallery reveal d1">')) + 400)) + len('</div>')]
works = "\n".join(
    f'    <figure><img src="{A}/work-{n:02d}.webp" alt="Картина Олени Кулик Діріл" loading="lazy" decoding="async"></figure>'
    for n in range(1, 13))
s = s.replace(old_gallery, '<div class="gallery reveal d1">\n' + works + '\n  </div>', 1)

# 13. превʼю уроків — справжні відео, автоплей без звуку, зациклено
boxes = re.findall(r'<div class="vidbox">.*?</div>', s, re.S)
assert len(boxes) == 4, f"vidbox знайдено {len(boxes)}, очікувалось 4"
for n, box in enumerate(boxes, 1):
    s = s.replace(box, f'<div class="vidbox"><video src="{ver(f"lesson-{n}.mp4")}" '
                       f'poster="{ver(f"lesson-{n}-poster.webp")}" muted loop playsinline preload="none" '
                       f'aria-label="Уривок з уроку {n}"></video></div>', 1)

# 14. «Про автора» — карусель кадрів кар\'єри замість однієї фотографії
old_portrait = s[s.index('<div class="portrait reveal d1">'):
                 s.index('</div>', s.index('</picture>', s.index('<div class="portrait reveal d1">'))) + len('</div>')]
shots = [("olena.jpg", "Олена Кулик Діріл пише морський пейзаж на пленері")] + [
    (f"olena-{n}.webp", "Олена Кулик Діріл на відкритті персональної виставки") for n in range(1, 6)]
slides = "\n".join(
    f'      <img src="{A}/{f}" alt="{alt}" loading="lazy" decoding="async">' for f, alt in shots)
dots = "".join("<i></i>" for _ in shots)
s = s.replace(old_portrait,
              '<div class="cyc reveal d1">\n    <div class="frame">\n' + slides +
              '\n    </div>\n    <div class="dots" aria-hidden="true">' + dots + '</div>\n  </div>', 1)

# 15. карусель і відео — окремий скрипт наприкінці
s = s.replace("</body>", EXTRA_JS + "</body>", 1)



# 16. два обʼєкти першого екрана — обидва діти .hero, тож їхні координати
#     рахуються від самої секції, а не від заголовка
BG = '<div class="hero-bg"><div class="wall"></div><div class="bokeh"></div><div class="veil"></div></div>'
assert s.count(BG) == 1
s = s.replace(BG, BG + '\n  '
              f'<img class="hero-obj ho-wave" src="{A}/hero-wave.webp" alt="" '
              'width="738" height="760" aria-hidden="true" loading="lazy" decoding="async">\n  '
              f'<img class="hero-obj ho-stroke" src="{A}/hero-stroke.webp" alt="" '
              'width="675" height="760" aria-hidden="true" decoding="async">', 1)


s = copy_edits.apply(s)

p.write_text(s, encoding="utf-8")
print("ok:", len(s), "байт ·", len(copy_edits.EDITS), "правок копірайту")
for tag in ('obj-sec dark', 'obj-sec sand', 'obj-sec deep', 'st-brushes', 'st-tubes', 'st-palette', 'obj-close'):
    print(f"  {tag}: {s.count(tag)}")
print("  showcase лишилось:", s.count('class="showcase'))
print("  emoji-rail лишилось:", s.count('emoji-rail'))
