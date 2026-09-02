"""
Machine gates for the reworked can GLB. Run after rework_can.py; every check
must print `pass` before the model ships. Checks out/tempo-can.glb.

Run: blender -b -P verify_glb.py
"""
import bpy, math, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TOOLS, 'out', 'tempo-can.glb')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=OUT)

checks = []
def check(name, ok, val=''):
    checks.append((name, 'pass' if ok else 'FAIL', val)); return ok

mats = {m.name.split('.')[0] for m in bpy.data.materials}
check('materials == {Label, Metal}', mats == {'Label', 'Metal'}, str(mats))

total_label = total_metal = 0
label_band = [10, -10]; metal_in_band = 0
uv_bad = 0; useam_max_span = 0
for o in bpy.data.objects:
    if o.type != 'MESH': continue
    me = o.data
    uv = me.uv_layers.active.data if me.uv_layers.active else None
    for p in me.polygons:
        m = o.material_slots[p.material_index].material
        nm = m.name.split('.')[0] if m else '?'
        c = p.center
        if nm == 'Label':
            total_label += 1
            label_band[0] = min(label_band[0], c.y); label_band[1] = max(label_band[1], c.y)
            us = [uv[li].uv.x for li in p.loop_indices]
            vs = [uv[li].uv.y for li in p.loop_indices]
            span = max(us) - min(us)
            useam_max_span = max(useam_max_span, span)
            if span > 0.25 or min(vs) < -0.001 or max(vs) > 1.001: uv_bad += 1
        else:
            total_metal += 1
            if 0.15 <= c.y <= 1.85: metal_in_band += 1

check('label poly count == 384', total_label == 384, total_label)
check('metal poly count == 7504-384+1682', total_metal == 7504 - 384 + 1682, total_metal)
check('label centers within [0.10,1.90]',
      0.10 <= label_band[0] and label_band[1] <= 1.90,
      str([round(x, 3) for x in label_band]))
check('no metal faces inside the wall band', metal_in_band == 0, metal_in_band)
check('label UVs contiguous per face, v in [0,1]', uv_bad == 0,
      f'bad={uv_bad} max_u_span={useam_max_span:.3f}')

# Label must ship textured (the site swaps .map at runtime), Metal metallic
lm = next(m for m in bpy.data.materials if m.name.startswith('Label'))
pn = next(n for n in lm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
check('Label base color is textured', pn.inputs['Base Color'].is_linked)
mm = next(m for m in bpy.data.materials if m.name.startswith('Metal'))
pm = next(n for n in mm.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
check('Metal metallic == 1.0', abs(pm.inputs['Metallic'].default_value - 1.0) < 1e-3)

import mathutils
pts = [o.matrix_world @ mathutils.Vector(b) for o in bpy.data.objects if o.type == 'MESH' for b in o.bound_box]
lo = [min(p[i] for p in pts) for i in range(3)]; hi = [max(p[i] for p in pts) for i in range(3)]
diag = math.dist(lo, hi)
check('bbox diag in [0.01,100] m', 0.01 <= diag <= 100, f'{diag:.3f} m')

print('\n=== VERIFY ===')
for n, s, v in checks: print(f'{s:5} {n} {v}')
sys.exit(0 if all(s == 'pass' for _, s, _ in checks) else 1)
