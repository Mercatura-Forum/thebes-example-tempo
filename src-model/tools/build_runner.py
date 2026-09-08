# build_runner.py — the Quaternius "Character Animated" becomes the TEMPO
# brand runner: citrus jersey carrying the TEMPO wordmark, ink shorts, paper
# shoes, natural skin. Clips Idle/Walk/Run kept and baked in place.
# Run: blender -b -P src-model/tools/build_runner.py
import bpy, json, math, os, re, sys

_DRACO = '/opt/blender-4.5.11-linux-x64/4.5/scripts/addons_core/io_scene_gltf2/libextern_draco.so'
if os.path.isfile(_DRACO):
    os.environ.setdefault('BLENDER_EXTERN_DRACO_LIBRARY_PATH', _DRACO)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')
OUT = os.path.join(ROOT, 'assets', 'street', 'runner.glb')
CHAR_GLB = os.path.join(VENDOR, 'quaternius-character', 'character_animated.glb')
CREST = os.path.join(HERE, 'out', 'tcrest.png')

CITRUS = (1.0, 0.478, 0.102, 1)
PAPER = (0.93, 0.90, 0.84, 1)
INK = (0.10, 0.09, 0.08, 1)

# shipped material name → (brand name, recolor or None=keep shipped color)
KIT = {
    'Shirt': ('runnerKit', CITRUS),
    'UnderShirt': ('runnerPaper', PAPER),
    'Pants': ('runnerInk', INK),
    'Boots': ('runnerPaper', PAPER),
    'Detail': ('runnerInk', INK),
    'Hair': ('runnerInk', INK),
    'Eye': ('runnerInk', INK),
    'Pupil': ('runnerInk', INK),
    'White': ('runnerPaper', PAPER),
    'Skin': ('runnerSkin', None),
    'Material.006': ('runnerInk', INK),   # the big hair mesh (Rogue.001)
}


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)
    return list(bpy.context.selected_objects)


def jersey_texture(shirt_mat, body_obj, shirt_slot_idx):
    """Fill the jersey citrus and print the TEMPO wordmark on the chest.

    The chest is found honestly: shirt faces whose deformed-rest normal points
    the way the character faces; their UV bbox receives the wordmark.
    """
    me = body_obj.data
    uv = me.uv_layers.active.data
    front, back = [], []
    for poly in me.polygons:
        if poly.material_index != shirt_slot_idx:
            continue
        n = body_obj.matrix_world.to_3x3() @ poly.normal
        if abs(n.y) < 0.35:
            continue
        (front if n.y < 0 else back).append(poly)
    # the character faces -Y in Blender after glTF import (+Z forward glTF)
    chest = front if front else back
    panels = [p for p in (front, back) if p]
    us, vs = [], []
    for poly in chest:
        for li in poly.loop_indices:
            u, v = uv[li].uv
            us.append(u); vs.append(v)
    if not us:
        print('[runner] WARNING: no chest faces found — jersey stays plain')
        return
    u0, u1, v0, v1 = min(us), max(us), min(vs), max(vs)
    print(f'[runner] chest UV bbox: u {u0:.2f}..{u1:.2f}  v {v0:.2f}..{v1:.2f} ({len(chest)} faces)')
    S = 512
    import numpy as np
    img = bpy.data.images.new('runnerKitTex', S, S, alpha=False)
    base = [CITRUS[0], CITRUS[1], CITRUS[2], 1.0]
    px = base * (S * S)
    wm = bpy.data.images.load(CREST)
    ww, wh = wm.size
    wpx = list(wm.pixels)

    def rasterize(faces):
        m = np.zeros((S, S), dtype=bool)
        idx = {p.index for p in faces}
        for tri in me.loop_triangles:
            if tri.polygon_index not in idx:
                continue
            pts = [(uv[li].uv[0] * S, uv[li].uv[1] * S) for li in tri.loops]
            (x1t, y1t), (x2t, y2t), (x3t, y3t) = pts
            xs2 = [p[0] for p in pts]; ys2 = [p[1] for p in pts]
            d = (y2t - y3t) * (x1t - x3t) + (x3t - x2t) * (y1t - y3t)
            if abs(d) < 1e-9:
                continue
            for yy in range(max(0, int(min(ys2))), min(S, int(max(ys2)) + 1)):
                for xx in range(max(0, int(min(xs2))), min(S, int(max(xs2)) + 1)):
                    a = ((y2t - y3t) * (xx - x3t) + (x3t - x2t) * (yy - y3t)) / d
                    b = ((y3t - y1t) * (xx - x3t) + (x1t - x3t) * (yy - y3t)) / d
                    if a >= -0.01 and b >= -0.01 and (1 - a - b) >= -0.01:
                        m[yy, xx] = True
        return m

    me.calc_loop_triangles()
    for panel in panels:
        m = rasterize(panel)
        ys_m, xs_m = np.nonzero(m)
        if not len(xs_m):
            continue
        cx = int(xs_m.mean())
        cy = int(ys_m.mean() + (ys_m.max() - ys_m.min()) * 0.10)
        row_x = np.nonzero(m[cy])[0]
        row_w = row_x.max() - row_x.min() if len(row_x) else 50
        span_x = int(row_w * 0.78)
        span_y = max(8, int(span_x * wh / ww))
        x0 = cx - span_x // 2; x1 = cx + span_x // 2
        y0 = cy - span_y // 2; y1 = cy + span_y // 2
        stamped = 0
        for y in range(max(0, y0), min(S, y1)):
            sy = int((y - y0) / max(1, y1 - y0) * wh)
            for x in range(max(0, x0), min(S, x1)):
                if not m[y, x]:
                    continue
                sx = int((x - x0) / max(1, x1 - x0) * ww)
                if wpx[(sy * ww + sx) * 4 + 3] > 0.4:
                    i = (y * S + x) * 4
                    px[i] = px[i + 1] = px[i + 2] = 0.97
                    stamped += 1
        print(f'[runner] crest stamped: {stamped} texels at ({cx},{cy}) span {span_x}')
    img.pixels = px
    img.pack()

    shirt_mat.use_nodes = True
    b = shirt_mat.node_tree.nodes['Principled BSDF']
    t = shirt_mat.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = img
    shirt_mat.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    shirt_mat.diffuse_color = CITRUS
    print('[runner] jersey texture applied')


def brand_kit():
    body = bpy.data.objects.get('Rogue')
    shirt_idx = None
    # snapshot ORIGINAL names before any rename — renaming while iterating
    # would re-visit renamed materials as "unmapped"
    originals = [(m, m.name) for m in list(bpy.data.materials)]
    for m, orig in originals:
        key = orig if orig in KIT else orig.split('.')[0]
        if key in KIT:
            new, col = KIT[key]
        else:
            print('[runner] unmapped material kept as skin:', orig)
            new, col = 'runnerSkin', None
        if col is not None and m.use_nodes:
            m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = col
            m.diffuse_color = col
        m.name = new
        if key == 'Shirt' and body:
            for i, sl in enumerate(body.material_slots):
                if sl.material == m:
                    shirt_idx = i
        print(f'[runner] material {orig!r} → {m.name!r}' + (' (recolored)' if col else ' (shipped color kept)'))
    if body is not None and shirt_idx is not None:
        shirt_mat = body.material_slots[shirt_idx].material
        jersey_texture(shirt_mat, body, shirt_idx)


def zero_xz_fcurves(action, bone_name):
    dp = f'pose.bones["{bone_name}"].location'
    removed = 0
    for fc in list(action.fcurves):
        if fc.data_path == dp and fc.array_index in (0, 2):
            vals = [kp.co[1] for kp in fc.keyframe_points]
            if vals and max(abs(v) for v in vals) > 0.01:
                action.fcurves.remove(fc)
                removed += 1
    if removed:
        print(f'[runner] {action.name}: removed {removed} XZ root fcurves ({bone_name})')


def normalize_height(char_arm):
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']

    def skinned_height():
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        zs = []
        for o in meshes:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            zs += [(ev.matrix_world @ v.co).z for v in me.vertices]
            ev.to_mesh_clear()
        return max(zs) - min(zs)

    h = skinned_height()
    print(f'[runner] skinned height: {h:.3f}m (target 1.75)')
    s = 1.75 / h
    from mathutils import Matrix
    M = Matrix.Scale(s, 4)
    char_arm.data.transform(M)
    for o in meshes:
        o.data.transform(M)
    for act in bpy.data.actions:
        for fc in act.fcurves:
            if fc.data_path.endswith('.location'):
                for kp in fc.keyframe_points:
                    kp.co.y *= s
                    kp.handle_left.y *= s
                    kp.handle_right.y *= s
    print(f'[runner] scaled ×{s:.4f} → {skinned_height():.3f}m')
    # ground the feet at z=0 (the runtime stands the runner at y=0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zmin = min((o.evaluated_get(dg).matrix_world @ v.co).z
               for o in meshes for v in o.evaluated_get(dg).to_mesh().vertices)
    T = Matrix.Translation((0, 0, -zmin))
    char_arm.data.transform(T)
    for o in meshes:
        o.data.transform(T)
    print(f'[runner] grounded: feet lifted by {-zmin:.3f}m')


print('[runner] starting — TEMPO brand runner from Character Animated')
bpy.ops.wm.read_factory_settings(use_empty=True)
objs = import_glb(CHAR_GLB)
arm = next((o for o in objs if o.type == 'ARMATURE'), None)
if arm is None:
    print('ERROR: no armature'); sys.exit(1)

# junk sweep: keep meshes that are skinned OR bone-parented to the rig (the
# hair/eyes mesh rides a head bone, no armature modifier); named template
# junk (Icosphere) goes regardless
def reaches_arm(o):
    p = o.parent
    while p is not None:
        if p == arm: return True
        p = p.parent
    return False
for o in list(bpy.data.objects):
    if o.type != 'MESH': continue
    skinned = any(m.type == 'ARMATURE' for m in o.modifiers)
    if o.name.startswith('Icosphere') or not (skinned or reaches_arm(o)):
        print('[runner] junk strip:', o.name)
        bpy.data.objects.remove(o)

# the import rides in with node scale on the armature — clear it BEFORE the
# data bake (glTF would export it; the gate rejects scaled nodes) and let
# normalize_height re-measure through the depsgraph
print('[runner] armature node scale on import:', tuple(arm.scale))
arm.scale = (1, 1, 1)
arm.location = (0, 0, 0)

# clips: the pack ships each clip twice ('X' and 'CharacterArmature|X') — keep
# the plain trio, drop everything else
trio = {}
for label in ('Idle', 'Walk', 'Run'):
    a = bpy.data.actions.get(f'{label}_CharacterArmature') or bpy.data.actions.get(label)
    if a is None:
        print('ERROR: missing clip', label); sys.exit(1)
    trio[label] = a
for label, a in trio.items():
    for bone in ('Root', 'root', 'Hips', 'hips', 'Torso'):
        zero_xz_fcurves(a, bone)

brand_kit()
normalize_height(arm)

for new_name, action in trio.items():
    action.name = new_name
    action.use_fake_user = True
for a in list(bpy.data.actions):
    if a.name not in ('Idle', 'Walk', 'Run'):
        bpy.data.actions.remove(a)
arm.animation_data_create()
arm.animation_data.action = bpy.data.actions['Idle']
for name in ('Idle', 'Walk', 'Run'):
    action = bpy.data.actions[name]
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, int(action.frame_range[0]), action)
print('[runner] final actions:', sorted(a.name for a in bpy.data.actions))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
kwargs = dict(filepath=OUT, export_format='GLB', export_yup=True,
              export_animations=True, export_apply=False)
try:
    bpy.ops.export_scene.gltf(**kwargs, export_draco_mesh_compression_enable=True)
except Exception as e:
    print('[runner] draco unavailable (%s), plain export' % e)
    bpy.ops.export_scene.gltf(**kwargs)
print('[runner] glb bytes:', os.path.getsize(OUT))

# eyeball render
scene = bpy.context.scene
cam_data = bpy.data.cameras.new('c'); cam = bpy.data.objects.new('c', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0.35, -2.6, 1.25)
tgt = bpy.data.objects.new('t', None); bpy.context.collection.objects.link(tgt)
tgt.location = (0, 0, 0.9)
tc = cam.constraints.new('TRACK_TO'); tc.target = tgt
tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
scene.camera = cam
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.color_type = 'TEXTURE'
scene.display.shading.show_cavity = True
scene.render.resolution_x = 700; scene.render.resolution_y = 900
scene.world = bpy.data.worlds.new('w'); scene.world.color = (0.9, 0.85, 0.78)
scene.render.filepath = os.path.join(HERE, 'out', 'runner_check.png')
bpy.ops.render.render(write_still=True)
print('[runner] done')
