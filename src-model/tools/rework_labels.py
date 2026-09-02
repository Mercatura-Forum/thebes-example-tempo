"""
Rebuild the TEMPO label textures with junction breathing room.

Each 2048x1024 texture is two identical 1024-wide repeats. As originally
committed the wordmark sat flush against the repeat edges, so consecutive
repeats collided on the can ("...POTEM..."). This transform crops one repeat,
scales it uniformly to SCALE, re-centres it on the flavour's flat background
colour, and tiles it x2 — leaving a ~22 deg gap at both junctions.

ONE-SHOT: not idempotent (a second run shrinks the artwork again). The
pristine originals live in git history before commit f2efd55.

Run: python3 rework_labels.py
"""
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SCALE = 0.88
SIZE = 1024

for k in ('citrus', 'berry', 'lime'):
    path = os.path.join(ROOT, 'assets', f'label_{k}.png')
    im = Image.open(path).convert('RGB')
    assert im.size == (2048, 1024), im.size
    corners = {im.getpixel(p) for p in [(2, 2), (2045, 2), (2, 1021), (2045, 1021), (1023, 2)]}
    assert len(corners) == 1, f'{k}: background not flat: {corners}'
    bg = corners.pop()

    rep = im.crop((0, 0, SIZE, SIZE))
    s = round(SIZE * SCALE)
    scaled = rep.resize((s, s), Image.LANCZOS)
    tile = Image.new('RGB', (SIZE, SIZE), bg)
    off = (SIZE - s) // 2
    tile.paste(scaled, (off, off))

    out = Image.new('RGB', (2048, 1024), bg)
    out.paste(tile, (0, 0))
    out.paste(tile, (1024, 0))
    out.save(path)
    print(k, 'rebuilt, bg =', bg, 'gap px per junction =', 2 * off)
