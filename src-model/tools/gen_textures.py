# gen_textures.py — bakes the tiling textures for the street's built geometry.
# Deterministic (seeded): the same build always ships the same bytes.
# Run: python3 gen_textures.py   → out/textures/*.png (256px, tiling)
import os, random, math
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out', 'textures')
os.makedirs(OUT, exist_ok=True)
S = 256
rng = random.Random(5)


def clamp8(v):
    return max(0, min(255, int(v)))


def base_noise(tone, amp=7, blur=1.2):
    """Tileable-enough noise sheet around a base tone."""
    im = Image.new('RGB', (S, S), tone)
    px = im.load()
    for y in range(S):
        for x in range(S):
            n = rng.gauss(0, amp)
            r, g, b = px[x, y]
            px[x, y] = (clamp8(r + n), clamp8(g + n), clamp8(b + n))
    return im.filter(ImageFilter.GaussianBlur(blur))


def streaks(im, count, tone, width, alpha, vertical=True):
    """Soft weathering streaks; drawn on a wrapped 2x canvas so tiles seam."""
    big = Image.new('RGBA', (S * 2, S * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for _ in range(count):
        p = rng.randrange(0, S * 2)
        ln = rng.randrange(S // 3, S)
        st = rng.randrange(0, S)
        w = rng.randrange(1, width + 1)
        box = (p, st, p + w, st + ln) if vertical else (st, p, st + ln, p + w)
        d.rectangle(box, fill=tone + (alpha,))
    big = big.filter(ImageFilter.GaussianBlur(2.2))
    for ox in (0, -S):
        for oy in (0, -S):
            im.paste(big, (ox, oy), big)
    return im


def plaster(tone, out):
    im = base_noise(tone, amp=6)
    dark = tuple(clamp8(c * 0.82) for c in tone)
    im = streaks(im, 10, dark, 3, 26, vertical=True)
    light = tuple(clamp8(c * 1.10) for c in tone)
    im = streaks(im, 6, light, 2, 22, vertical=False)
    im.save(os.path.join(OUT, out))


def wood(tone, out, plank=64):
    im = base_noise(tone, amp=5, blur=0.8)
    px = im.load()
    for y in range(S):
        for x in range(S):
            g = math.sin((x / S) * math.pi * 14 + math.sin(y / 17.0) * 1.7) * 6
            r, gg, b = px[x, y]
            px[x, y] = (clamp8(r + g), clamp8(gg + g * 0.8), clamp8(b + g * 0.6))
    d = ImageDraw.Draw(im)
    dark = tuple(clamp8(c * 0.70) for c in tone)
    for gx in range(0, S, plank):
        d.line([(gx, 0), (gx, S)], fill=dark, width=2)
    im.save(os.path.join(OUT, out))


def asphalt(tone, out, cracks=4):
    im = base_noise(tone, amp=9, blur=0.7)
    d = ImageDraw.Draw(im)
    spec = tuple(clamp8(c * 1.35) for c in tone)
    for _ in range(420):
        x, y = rng.randrange(S), rng.randrange(S)
        d.point((x, y), fill=spec)
    dark = tuple(clamp8(c * 0.62) for c in tone)
    for _ in range(cracks):
        x, y = rng.randrange(S), rng.randrange(S)
        for _ in range(rng.randrange(24, 60)):
            nx, ny = (x + rng.randrange(-4, 5)) % S, (y + rng.randrange(1, 5)) % S
            d.line([(x, y), (nx, ny)], fill=dark, width=1)
            x, y = nx, ny
    im.save(os.path.join(OUT, out))


def pavement(tone, out, tile=85):
    im = base_noise(tone, amp=6)
    d = ImageDraw.Draw(im)
    joint = tuple(clamp8(c * 0.74) for c in tone)
    for g in range(0, S + 1, tile):
        d.line([(g, 0), (g, S)], fill=joint, width=3)
        d.line([(0, g), (S, g)], fill=joint, width=3)
    im.save(os.path.join(OUT, out))


def dirt(tone, out):
    im = base_noise(tone, amp=10, blur=1.6)
    dark = tuple(clamp8(c * 0.85) for c in tone)
    im = streaks(im, 8, dark, 5, 20, vertical=False)
    im.save(os.path.join(OUT, out))


def clay(tone, out):
    im = base_noise(tone, amp=7, blur=1.0)
    px = im.load()
    for y in range(S):
        band = math.sin(y / 9.0) * 5
        for x in range(S):
            r, g, b = px[x, y]
            px[x, y] = (clamp8(r + band), clamp8(g + band * 0.7), clamp8(b + band * 0.5))
    im.save(os.path.join(OUT, out))


def rug(tone, out):
    im = base_noise(tone, amp=8, blur=0.6)
    d = ImageDraw.Draw(im)
    border = (210, 200, 180)
    accent = (191, 77, 40)
    d.rectangle([6, 6, S - 7, S - 7], outline=border, width=5)
    d.rectangle([20, 20, S - 21, S - 21], outline=accent, width=3)
    cx = S // 2
    d.polygon([(cx, 58), (S - 58, cx), (cx, S - 58), (58, cx)], outline=border, width=4)
    d.polygon([(cx, 88), (S - 88, cx), (cx, S - 88), (88, cx)], outline=accent, width=3)
    im.save(os.path.join(OUT, out))


PLASTER_SAND = (209, 184, 140)
PLASTER_ROSE = (194, 148, 128)
PLASTER_OCHRE = (204, 168, 107)
WOOD = (115, 82, 51)
WOOD_LIGHT = (148, 112, 71)
ASPHALT = (117, 110, 100)
ASPHALT_OLD = (133, 122, 110)
SIDEWALK = (184, 168, 143)
GROUND = (158, 140, 115)
CLAY = (158, 97, 61)
RUG = (64, 89, 84)

plaster(PLASTER_SAND, 'plaster_sand.png')
plaster(PLASTER_ROSE, 'plaster_rose.png')
plaster(PLASTER_OCHRE, 'plaster_ochre.png')
wood(WOOD, 'wood.png')
wood(WOOD_LIGHT, 'wood_light.png', plank=85)
asphalt(ASPHALT, 'asphalt.png')
asphalt(ASPHALT_OLD, 'asphalt_old.png', cracks=2)
pavement(SIDEWALK, 'sidewalk.png')
dirt(GROUND, 'ground.png')
clay(CLAY, 'clay.png')
rug(RUG, 'rug.png')
print('textures baked:', sorted(os.listdir(OUT)))
