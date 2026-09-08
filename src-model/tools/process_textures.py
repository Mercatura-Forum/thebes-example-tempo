# process_textures.py — prepares the street's tiling textures from the
# vendored ambientCG zips (CC0). Color maps only, 512px, brand-matched tints.
# Nothing here is drawn by hand: every pixel comes from ambientcg.com.
# Run: python3 process_textures.py   → out/textures/*.png
import os, zipfile, io
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
VEN = os.path.join(HERE, '..', 'vendor', 'ambientcg')
OUT = os.path.join(HERE, 'out', 'textures')
os.makedirs(OUT, exist_ok=True)


def color_map(zip_name):
    z = zipfile.ZipFile(os.path.join(VEN, zip_name))
    name = next(n for n in z.namelist() if n.endswith('_Color.jpg'))
    im = Image.open(io.BytesIO(z.read(name))).convert('RGB')
    return im.resize((512, 512), Image.LANCZOS)


def tint(im, rgb):
    # multiply toward a target tone — the texture's structure stays ambientCG's
    r, g, b = rgb
    return Image.merge('RGB', [ch.point(lambda v, s=s: min(255, int(v * s)))
                               for ch, s in zip(im.split(), (r, g, b))])


def brightness(im, f):
    return im.point(lambda v: min(255, int(v * f)))


plaster = color_map('Plaster001.zip')
painted = color_map('PaintedPlaster017.zip')
asphalt = color_map('Asphalt033.zip')
paving = color_map('PavingStones138.zip')
wood = color_map('WoodFloor043.zip')
carpet = color_map('Carpet016.zip')
ground = color_map('Ground037.zip')

tint(plaster, (1.10, 0.98, 0.78)).save(os.path.join(OUT, 'plaster_sand.png'))
tint(plaster, (1.12, 0.94, 0.60)).save(os.path.join(OUT, 'plaster_ochre.png'))
tint(painted, (1.10, 0.82, 0.72)).save(os.path.join(OUT, 'plaster_rose.png'))
asphalt.save(os.path.join(OUT, 'asphalt.png'))
brightness(asphalt, 1.18).save(os.path.join(OUT, 'asphalt_old.png'))
tint(paving, (1.06, 0.99, 0.88)).save(os.path.join(OUT, 'sidewalk.png'))
tint(wood, (0.82, 0.66, 0.50)).save(os.path.join(OUT, 'wood.png'))
tint(wood, (1.02, 0.86, 0.66)).save(os.path.join(OUT, 'wood_light.png'))
tint(carpet, (0.55, 0.75, 0.72)).save(os.path.join(OUT, 'rug.png'))
tint(ground, (1.12, 1.00, 0.80)).save(os.path.join(OUT, 'ground.png'))
tint(ground, (0.95, 0.72, 0.50)).save(os.path.join(OUT, 'clay.png'))
print('textures processed:', sorted(os.listdir(OUT)))
