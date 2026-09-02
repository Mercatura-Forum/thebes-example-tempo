"""
Build assets-ready splash.glb from the raw Sketchfab "Water Splash" download
(water_splash.glb in the repo root, NOT redistributed raw; CC-BY-4.0, credited
in NOTICE.md).

Keeps the three frozen splash arms, discards the sim's stand-in column
('Boole') and its dead spec-gloss textures, bakes all node transforms,
decimates ~211k -> ~15k tris, and rescales/centres the composition onto the
TEMPO can's frame: column radius -> can wall radius 0.5207, column mid-height
-> can mid-height (y=1.0 in glTF terms). Arms ship as three objects under one
'Water' material — the site re-materials and animates them per-arm.

Run: blender -b -P build_splash.py     -> out/splash.glb
"""
import bpy, os
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TOOLS, '..', '..'))
SRC = os.path.join(ROOT, 'water_splash.glb')
OUT = os.path.join(TOOLS, 'out', 'splash.glb')

CAN_R = 0.5207          # can wall radius in the site's model units
CAN_MID = 1.0           # can mid-height (can spans 0..2)
CLEARANCE = 1.02
DECIMATE = 0.07

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

# world-space column bbox drives the mapping
boole = bpy.data.objects['Boole_Mat_0']
pts = [boole.matrix_world @ Vector(b) for b in boole.bound_box]
lo = Vector((min(p[i] for p in pts) for i in range(3)))
hi = Vector((max(p[i] for p in pts) for i in range(3)))
cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
zc = (lo.z + hi.z) / 2
col_r = max(hi.x - lo.x, hi.y - lo.y) / 2
s = CAN_R * CLEARANCE / col_r
print(f'column r={col_r:.2f} center=({cx:.2f},{cy:.2f},{zc:.2f}) scale={s:.6f}')

arms = [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Mesher')]
water = bpy.data.materials.new('Water')
water.use_nodes = True
wp = next(n for n in water.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
wp.inputs['Base Color'].default_value = (0.55, 0.75, 1.0, 1.0)
wp.inputs['Roughness'].default_value = 0.12

# bake: world transform -> mesh data, then map column frame -> can frame
M = (Matrix.Translation((0, 0, CAN_MID)) @
     Matrix.Scale(s, 4) @
     Matrix.Translation((-cx, -cy, -zc)))
for i, o in enumerate(arms):
    o.data.transform(M @ o.matrix_world)
    o.parent = None                       # unparent FIRST: clearing the parent
    o.matrix_world = Matrix.Identity(4)   # after matrix_world would re-apply
                                          # the empties' inverse and teleport the arm
    mod = o.modifiers.new('dec', 'DECIMATE')
    mod.ratio = DECIMATE
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier='dec')
    o.data.materials.clear()
    o.data.materials.append(water)
    o.name = o.data.name = 'Splash%d' % i

# keep only the arms
for o in list(bpy.data.objects):
    if o not in arms:
        bpy.data.objects.remove(o, do_unlink=True)
for img in list(bpy.data.images):
    bpy.data.images.remove(img)

tris = sum(len(o.data.polygons) for o in arms)
print('arms tris after decimate:', tris)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
