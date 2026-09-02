# Bake condensation droplets onto the label textures (assets/label_*.png).
#
# ONE-SHOT like rework_labels.py: running it twice doubles the droplets.
# Pristine labels live in git history (pre-<this commit>) and in
# src-model/labels-pre-condensation/ if you made the local backup first.
#
# Deterministic: seeded per flavour, so a re-run from pristine inputs always
# produces the same file. The label wraps the can (2 repeats across x), so
# droplets near the x edges are drawn again shifted by ±width to keep the
# seam clean.

import os, random
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
FLAVORS = ['citrus', 'berry', 'lime']

# the wordmark band (v-range of the big TEMPO type) gets half density
WORDMARK = (0.42, 0.62)


def droplet_layer(w, h, seed):
    rng = random.Random(seed)
    layer = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def blob(cx, cy, r):
        ry = r * rng.uniform(1.0, 1.25)          # slight gravity stretch
        for dx in (-w, 0, w):                     # wrap the seam
            x = cx + dx
            if x + r < 0 or x - r > w:
                continue
            # body: darken + a hair of shadow low-right
            d.ellipse([x - r, cy - ry, x + r, cy + ry], fill=(20, 10, 5, 34))
            d.ellipse([x - r * .8, cy + ry * .25, x + r * .9, cy + ry * 1.05],
                      fill=(10, 5, 0, 26))
            # refraction highlight: bright arc top-left
            d.arc([x - r * .78, cy - ry * .78, x + r * .78, cy + ry * .78],
                  start=170, end=300, fill=(255, 255, 255, 110), width=max(1, int(r * .16)))
            # specular dot
            sr = max(1, r * .18)
            d.ellipse([x - r * .34 - sr, cy - ry * .38 - sr, x - r * .34 + sr, cy - ry * .38 + sr],
                      fill=(255, 255, 255, 190))

    def keep(cy):
        v = cy / h
        if WORDMARK[0] < v < WORDMARK[1]:
            return rng.random() < 0.5
        return True

    for _ in range(430):                          # small fog of fine drops
        cy = rng.uniform(h * .04, h * .96)
        if keep(cy):
            blob(rng.uniform(0, w), cy, rng.uniform(2.5, 6))
    for _ in range(150):                          # medium
        cy = rng.uniform(h * .05, h * .95)
        if keep(cy):
            blob(rng.uniform(0, w), cy, rng.uniform(6, 12))
    for _ in range(28):                           # a few heavy beads
        cy = rng.uniform(h * .08, h * .92)
        if keep(cy):
            blob(rng.uniform(0, w), cy, rng.uniform(12, 17))

    return layer.filter(ImageFilter.GaussianBlur(0.6))


for i, k in enumerate(FLAVORS):
    p = os.path.join(ROOT, 'assets', 'label_%s.png' % k)
    im = Image.open(p).convert('RGBA')
    im.alpha_composite(droplet_layer(im.width, im.height, seed=1000 + i))
    im.convert('RGB').save(p)
    print('condensed', p)
