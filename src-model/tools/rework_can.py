"""
TEMPO can rework — label wraps the can with a clean cylindrical unwrap;
seam ring, lid, tab, base ring, bottom dome and interior are silver Metal.

Reads the shipped GLB (site coordinate frame preserved), reassigns face
materials by lathe profile, regenerates the label UVs in code, embeds the
citrus label as the Label base colour, exports out/tempo-can.glb.
Idempotent: everything is re-derived from geometry on each run.

Run: blender -b -P rework_can.py
"""
import bpy, math, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC = os.path.join(ROOT, 'assets', 'tempo-can.glb')
LABEL_TEX = os.path.join(ROOT, 'assets', 'label_citrus.png')
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
OUT = os.path.join(OUT_DIR, 'tempo-can.glb')

# Lathe profile (measured): base ring below the loop at y=0.1088; wall + neck
# taper up to the loop at y=1.8988; seam trough starts at y=1.909.
Y_BOT = 0.10          # every vertex of a label face must sit above this
Y_TOP = 1.90          # ... and below this
# NOTE: no normal-direction test — the donor mesh's winding is flipped
# (double-sided material + correct custom normals), and the y-band alone
# selects the outer wall (verified: no interior shell there). Classification
# is per-VERTEX, not face center: the transition rings are triangulated with
# alternating diagonals, and center tests split them into a sawtooth.
FRONT_U = 0.25        # +Z (site camera front) lands on the first label repeat

os.makedirs(OUT_DIR, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

can = bpy.data.objects['Cylinder']
me = can.data
mat_label = bpy.data.materials['Label']
mat_metal = bpy.data.materials['Metal']

# Slots on the can: keep Label at its index, add Metal if absent
slot_names = [s.material.name if s.material else '' for s in can.material_slots]
if 'Metal' not in slot_names:
    me.materials.append(mat_metal)
    slot_names.append('Metal')
IDX_LABEL = slot_names.index('Label')
IDX_METAL = slot_names.index('Metal')

# --- classify faces -------------------------------------------------------
label_polys = []
for p in me.polygons:
    if all(Y_BOT <= me.vertices[v].co.y <= Y_TOP for v in p.vertices):
        p.material_index = IDX_LABEL
        label_polys.append(p)
    else:
        p.material_index = IDX_METAL

ys = [me.vertices[v].co.y for p in label_polys for v in p.vertices]
y0, y1 = min(ys), max(ys)
print(f"label faces={len(label_polys)}/{len(me.polygons)} band y=[{y0:.4f},{y1:.4f}]")

# --- cylindrical unwrap of the label band ---------------------------------
# Blender UV origin is bottom-left; the glTF exporter flips V, so
# v_blender = (y - y0)/(y1 - y0) puts image-top at the can top in glTF.
uv = me.uv_layers.active.data
for p in label_polys:
    loops = []
    for li in p.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        u = FRONT_U + math.atan2(co.x, co.z) / (2 * math.pi)
        loops.append((li, u, (co.y - y0) / (y1 - y0)))
    umin = min(u for _, u, _ in loops)
    umax = max(u for _, u, _ in loops)
    for li, u, vv in loops:
        if umax - umin > 0.5 and (u - umin) < 0.5:
            u += 1.0                      # seam face: keep the face contiguous
        uv[li].uv = (u, vv)

# --- materials ------------------------------------------------------------
# Label: embed the citrus label as base colour (the site swaps .map at runtime,
# which only works if the material ships textured)
tree = mat_label.node_tree
principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
img_node = next((n for n in tree.nodes if n.type == 'TEX_IMAGE'), None)
if img_node is None:
    img_node = tree.nodes.new('ShaderNodeTexImage')
    tree.links.new(img_node.outputs['Color'], principled.inputs['Base Color'])
old_img = img_node.image
img_node.image = bpy.data.images.load(LABEL_TEX)
img_node.image.colorspace_settings.name = 'sRGB'
img_node.extension = 'REPEAT'
if old_img and old_img.users == 0:
    bpy.data.images.remove(old_img)
principled.inputs['Metallic'].default_value = 0.08
principled.inputs['Roughness'].default_value = 0.42

# Metal: bare aluminium, matches the values can3d.js applies at runtime
mtree = mat_metal.node_tree
mp = next(n for n in mtree.nodes if n.type == 'BSDF_PRINCIPLED')
mp.inputs['Base Color'].default_value = (0.843, 0.851, 0.871, 1.0)  # 0xd7d9de
mp.inputs['Metallic'].default_value = 1.0
mp.inputs['Roughness'].default_value = 0.26

# --- export ---------------------------------------------------------------
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print("wrote", OUT, os.path.getsize(OUT), "bytes")
