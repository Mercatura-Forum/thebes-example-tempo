# gen_signs.py — bakes the Arabic shop lettering for the street signs.
# Run: python3 src-model/tools/gen_signs.py
# Renders ink-on-paper plaques (Amiri, reshaped + bidi) into out/signs/;
# build_street.py maps them onto the koshk counter and the wooden sign.
import os
import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
try:
    from bidi.algorithm import get_display
except ImportError:
    from bidi import get_display

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, '..', 'vendor', 'amiri-font', 'Amiri-Regular.ttf')
OUT = os.path.join(HERE, 'out', 'signs')
PAPER = (237, 230, 214, 255)   # palette 'paper' in 8-bit
INK = (26, 23, 20, 255)        # palette 'ink' in 8-bit

def bake(text, px, size, name):
    shaped = get_display(arabic_reshaper.reshape(text))
    img = Image.new('RGBA', px, PAPER)
    d = ImageDraw.Draw(img)
    while size > 24:   # fit inside the plaque with margin
        f = ImageFont.truetype(FONT, size)
        bbox = d.textbbox((0, 0), shaped, font=f)
        if bbox[2] - bbox[0] <= px[0] - 48 and bbox[3] - bbox[1] <= px[1] - 32:
            break
        size -= 8
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((px[0] - w) / 2 - bbox[0], (px[1] - h) / 2 - bbox[1]),
           shaped, font=f, fill=INK)
    d.rectangle([3, 3, px[0] - 4, px[1] - 4], outline=INK, width=3)
    os.makedirs(OUT, exist_ok=True)
    img.save(os.path.join(OUT, name))
    print('[signs]', name, px[0], 'x', px[1])

bake('مشروبات باردة', (512, 128), 72, 'sign_drinks.png')
bake('كشك', (256, 256), 128, 'sign_koshk.png')
