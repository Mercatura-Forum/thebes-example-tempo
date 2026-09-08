"""
Machine gates for the street scene. Every check must print `pass` before it
ships. Checks assets/street/street.glb + runner.glb + poster.webp.

Run: blender -b -P src-model/tools/verify_street_glb.py
"""
import bpy, json, os, struct, sys

# import needs draco too — same borrowed wrapper as build_street.py
_DRACO = '/opt/blender-4.5.11-linux-x64/4.5/scripts/addons_core/io_scene_gltf2/libextern_draco.so'
if os.path.isfile(_DRACO):
    os.environ.setdefault('BLENDER_EXTERN_DRACO_LIBRARY_PATH', _DRACO)

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TOOLS, '..', '..'))
STREET = os.path.join(ROOT, 'assets', 'street', 'street.glb')
RUNNER = os.path.join(ROOT, 'assets', 'street', 'runner.glb')
POSTER = os.path.join(ROOT, 'assets', 'street', 'poster.webp')

# allowed material names — mirror of build_street.py's PALETTE/EMISSIVE/mat_tex
# and build_runner.py's three runner materials. Duplicated as a literal on
# purpose: the gate failing loudly on palette drift is the point.
ALLOWED = {
    'ground', 'sidewalk', 'plasterSand', 'plasterRose', 'plasterOchre',
    'shutter', 'wood', 'woodLight', 'paper', 'ink', 'awningA', 'awningB',
    'metal', 'bulb', 'fridge', 'sign', 'signDrinks', 'signKoshk',
    'asphalt', 'asphaltOld', 'foliage', 'clay', 'shadow',
    'runnerPaper', 'runnerInk', 'runnerAccent',
}

checks = []
def check(name, ok, val=''):
    checks.append((name, 'pass' if ok else 'FAIL', val)); return ok

# ── wire budget ──
wire = sum(os.path.getsize(p) for p in (STREET, RUNNER, POSTER))
check('street+runner+poster wire <= 5MB', wire <= 5_242_880, '%d bytes' % wire)
check('poster.webp <= 150KB', os.path.getsize(POSTER) <= 153_600,
      '%d bytes' % os.path.getsize(POSTER))

# ── street ──
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=STREET)
street_tris = sum(len(p.vertices) - 2 for o in bpy.data.objects
                  if o.type == 'MESH' for p in o.data.polygons)
check('street tris <= 120k', street_tris <= 120_000, str(street_tris))
street_mats = {m.name.split('.')[0] for m in bpy.data.materials}
check('street materials palette-locked', street_mats <= ALLOWED,
      str(sorted(street_mats - ALLOWED)) if not street_mats <= ALLOWED else '')

# ── runner ── all checks read the FILE, not a Blender import round-trip
# (the importer decorates action names and its rig reconstruction distorts
# an evaluated-height measurement; the JSON chunk is the contract three.js
# actually loads)
raw = open(RUNNER, 'rb').read()
ln = struct.unpack('<I', raw[12:16])[0]
doc = json.loads(raw[20:20 + ln])

anims = sorted(a['name'] for a in doc.get('animations', []))
check('runner clips == [Idle, Run, Walk]', anims == ['Idle', 'Run', 'Walk'],
      str(anims))

runner_mats = {m['name'].split('.')[0] for m in doc.get('materials', [])}
check('runner materials palette-locked', runner_mats <= ALLOWED,
      str(sorted(runner_mats - ALLOWED)) if not runner_mats <= ALLOWED else '')

# bind-space POSITION extents == world height, provided no node carries scale
scaled = [n.get('name') for n in doc.get('nodes', [])
          if any(abs(s - 1) > 1e-3 for s in n.get('scale', [1, 1, 1]))]
check('runner nodes carry no scale', not scaled, str(scaled))
ys = []
for m in doc.get('meshes', []):
    for prim in m['primitives']:
        acc = doc['accessors'][prim['attributes']['POSITION']]
        if 'min' in acc and 'max' in acc:
            ys += [acc['min'][1], acc['max'][1]]
height = max(ys) - min(ys) if ys else 0
check('runner height 1.6-1.9m', 1.6 <= height <= 1.9, '%.2f' % height)
check('runner has exactly one skin', len(doc.get('skins', [])) == 1,
      str(len(doc.get('skins', []))))

for name, verdict, val in checks:
    print('%-42s %s  %s' % (name, verdict, val))
sys.exit(1 if any(v == 'FAIL' for _, v, _ in checks) else 0)
