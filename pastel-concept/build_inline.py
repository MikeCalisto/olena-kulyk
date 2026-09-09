#!/usr/bin/env python3
"""Збирає self-contained копію концепт-сторінки: картинки вшиваються як data:URI.
Потрібно, щоб макет відкривався одним файлом і публікувався як Artifact."""
import base64, mimetypes, re, pathlib

here = pathlib.Path(__file__).parent
src = (here / "index.html").read_text(encoding="utf-8")

def inline(m):
    name = m.group(1)
    path = here / "assets" / name
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return 'src="data:%s;base64,%s"' % (mime, base64.b64encode(path.read_bytes()).decode())

out = re.sub(r'src="assets/([^"]+)"', inline, src)
dst = here / "preview-inline.html"
dst.write_text(out, encoding="utf-8")
print(dst, f"{len(out)/1024:.0f} KB")
