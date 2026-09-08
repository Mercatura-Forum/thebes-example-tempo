# build_street.py — builds the Cairo koshk-corner diorama for section 05.
# Run: blender -b -P src-model/tools/build_street.py
# Reads street_layout.json (single source of truth shared with street-sim),
# exports assets/street/street.glb and renders assets/street/poster.webp.
import bpy, bmesh, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))

# this box's apt Blender 4.0 ships without libextern_draco; borrow the wrapper
# from the 4.5 install when present (the exporter reads this env var). Missing
# file → env untouched → export_glb's plain-GLB fallback still applies.
_DRACO = '/opt/blender-4.5.11-linux-x64/4.5/scripts/addons_core/io_scene_gltf2/libextern_draco.so'
if os.path.isfile(_DRACO):
    os.environ.setdefault('BLENDER_EXTERN_DRACO_LIBRARY_PATH', _DRACO)
LAYOUT = json.load(open(os.path.join(HERE, 'street_layout.json')))
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')
OUT_GLB = os.path.join(ROOT, 'assets', 'street', 'street.glb')
OUT_POSTER_PNG = os.path.join(HERE, 'out', 'street_poster.png')

# ── palette (locked to the site: paper / ink / sand / accent) ──
PALETTE = {
    'ground':      (0.62, 0.55, 0.45, 1),
    'sidewalk':    (0.72, 0.66, 0.56, 1),
    'plasterSand': (0.82, 0.72, 0.55, 1),
    'plasterRose': (0.76, 0.58, 0.50, 1),
    'plasterOchre':(0.80, 0.66, 0.42, 1),
    'shutter':     (0.16, 0.15, 0.13, 1),
    'wood':        (0.45, 0.32, 0.20, 1),
    'woodLight':   (0.58, 0.44, 0.28, 1),
    'paper':       (0.93, 0.90, 0.84, 1),
    'ink':         (0.10, 0.09, 0.08, 1),
    'awningA':     (0.75, 0.30, 0.16, 1),
    'awningB':     (0.25, 0.35, 0.33, 1),
    'metal':       (0.35, 0.34, 0.32, 1),
    'asphalt':     (0.46, 0.43, 0.39, 1),
    'asphaltOld':  (0.52, 0.48, 0.43, 1),
    'foliage':     (0.30, 0.42, 0.32, 1),
    'clay':        (0.62, 0.38, 0.24, 1),
    'rug':         (0.25, 0.35, 0.33, 1),
}
EMISSIVE = {
    'bulb':   ((1.0, 0.75, 0.4, 1), 6.0),
    'fridge': ((1.0, 0.85, 0.6, 1), 2.2),
    'sign':   ((1.0, 0.45, 0.10, 1), 3.0),
}

def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.textures):
        for d in list(coll):
            coll.remove(d)

TEXTURED = {
    'ground': 'ground.png', 'sidewalk': 'sidewalk.png',
    'plasterSand': 'plaster_sand.png', 'plasterRose': 'plaster_rose.png',
    'plasterOchre': 'plaster_ochre.png', 'wood': 'wood.png',
    'woodLight': 'wood_light.png', 'asphalt': 'asphalt.png',
    'asphaltOld': 'asphalt_old.png', 'clay': 'clay.png', 'rug': 'rug.png',
}

MATS = {}
def mat(name):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    if name == 'shadow':
        b.inputs['Base Color'].default_value = (0.06, 0.05, 0.05, 1)
        b.inputs['Alpha'].default_value = 0.28
        b.inputs['Roughness'].default_value = 1.0
        m.blend_method = 'BLEND'
        m.diffuse_color = (0.06, 0.05, 0.05, 0.28)
        MATS[name] = m
        return m
    if name in TEXTURED:
        img = bpy.data.images.load(os.path.join(HERE, 'out', 'textures', TEXTURED[name]))
        t = m.node_tree.nodes.new('ShaderNodeTexImage')
        t.image = img
        m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
        b.inputs['Roughness'].default_value = 0.9
        m.diffuse_color = PALETTE.get(name, (0.7, 0.6, 0.5, 1))
        MATS[name] = m
        return m
    if name in EMISSIVE:
        col, strength = EMISSIVE[name]
        b.inputs['Base Color'].default_value = col
        b.inputs['Emission Color'].default_value = col
        b.inputs['Emission Strength'].default_value = strength
        m.diffuse_color = col          # Workbench reads the viewport color
    else:
        b.inputs['Base Color'].default_value = PALETTE[name]
        b.inputs['Roughness'].default_value = 0.9
        m.diffuse_color = PALETTE[name]
    MATS[name] = m
    return m

def mat_tex(name, img_file):
    # baked sign texture (gen_signs.py output); Workbench poster shows the
    # paper tone via diffuse_color, the runtime GLB carries the image
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    img = bpy.data.images.load(os.path.join(HERE, 'out', 'signs', img_file))
    t = m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = img
    m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    m.diffuse_color = PALETTE['paper']
    MATS[name] = m
    return m

def sign_plane(name, tex_mat, sx, sy, wx, wy, wz, rz):
    # a textured quad (planes carry full 0..1 UVs; cube UVs are a cross layout)
    bpy.ops.mesh.primitive_plane_add(size=1, location=P(wx, wy, wz),
                                     rotation=(math.radians(90), 0, rz))
    o = bpy.context.active_object
    o.scale = (sx, sy, 1)
    o.name = name
    o.data.materials.append(tex_mat)
    return o

def box(name, sx, sy, sz, x, y, z, m, ry=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z), rotation=(0, ry, 0))
    o = bpy.context.active_object
    o.scale = (sx, sz, sy)          # blender Z-up: our (x, y-up, z) → (x, -z, y) handled at export
    o.name = name
    o.data.materials.append(mat(m))
    return o

# NOTE ON AXES: we model in Blender's own Z-up world using (x, -z_site, y_site)
# and export with +Y up, so runtime three.js coordinates match street_layout.
def P(x, y, z):  # site coords → blender coords
    return (x, -z, y)

def site_box(name, m, cx, cy, cz, sx, sy, sz, ry=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=P(cx, cy, cz), rotation=(0, 0, ry))
    o = bpy.context.active_object
    o.scale = (sx, sz, sy)
    o.name = name
    o.data.materials.append(mat(m))
    return o

def join(objs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.name = name
    return obj

def shrink_new_images(before):
    for img in set(bpy.data.images) - before:
        w, h = img.size
        if max(w, h) > 512:
            f = 512 / max(w, h)
            img.scale(max(1, round(w * f)), max(1, round(h * f)))
            print('[street] image shrunk', img.name, f'{w}x{h} -> {img.size[0]}x{img.size[1]}')

def import_vendor(ref, drop=()):
    # ref: "vendor:<dir>/<relpath>" — resolves under src-model/vendor/
    # drop: object-name prefixes to discard (ground planes riding along in the file)
    path = os.path.join(VENDOR, ref.split(':', 1)[1])
    before = set(bpy.data.objects)
    before_imgs = set(bpy.data.images)
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=path)
    elif ext == '.obj': bpy.ops.wm.obj_import(filepath=path)
    else: raise ValueError('unsupported vendor format: ' + path)
    new = set(bpy.data.objects) - before
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        # flatten: keep the WORLD transform (Sketchfab roots carry rotations)
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        for m in list(o.modifiers): o.modifiers.remove(m)   # armatures die below; bind pose stays
    for o in new:
        if o.type != 'MESH': bpy.data.objects.remove(o)
    shrink_new_images(before_imgs)
    kept = []
    for o in meshes:
        hidden = o.hide_viewport or not o.visible_get()
        if hidden or any(o.name.startswith(d) for d in drop):
            print('[street] import_vendor dropped', o.name, '(hidden)' if hidden else '')
            bpy.data.objects.remove(o)
        else:
            kept.append(o)
    return kept

def normalize_height(objs, name, height):
    obj = join(objs, name) if len(objs) > 1 else objs[0]
    obj.name = name
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    lo = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    hi = max((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    s = height / max(1e-6, hi - lo)
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    # bake "feet at z=0, XY-centered" INTO the mesh, so the later absolute
    # placement (obj.location = P(...)) can't undo the grounding
    ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
    obj.location.x -= (min(w.x for w in ws) + max(w.x for w in ws)) / 2
    obj.location.y -= (min(w.y for w in ws) + max(w.y for w in ws)) / 2
    obj.location.z -= min(w.z for w in ws)
    bpy.ops.object.transform_apply(location=True)
    return obj

def decimate_to(obj, tris):
    cur = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if cur <= tris * 1.5: return
    m = obj.modifiers.new('dec', 'DECIMATE')
    m.ratio = tris / cur
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='dec')

def build_vendor_props():
    for vp in LAYOUT.get('vendorProps', []):
        objs = import_vendor(vp['ref'], drop=vp.get('drop', ()))
        if vp.get('recolor_slots'):
            for slot_name, rgb in vp['recolor_slots'].items():
                col = tuple(rgb) + (1,)
                for o in objs:
                    for sl in o.material_slots:
                        if sl.material and sl.material.name.split('.')[0] == slot_name:
                            sl.material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = col
                            sl.material.diffuse_color = col
        if vp.get('recolor'):
            # a vendor material whose shipped tone doesn't survive daylight
            col = tuple(vp['recolor']) + (1,)
            for o in objs:
                for sl in o.material_slots:
                    if sl.material and sl.material.use_nodes:
                        sl.material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = col
                        sl.material.diffuse_color = col
        obj = normalize_height(objs, vp['name'], vp['height'])
        decimate_to(obj, vp.get('tris', 3000))
        obj.location = P(vp['x'], vp.get('y', 0), vp['z'])
        obj.rotation_mode = 'XYZ'   # glTF imports arrive QUATERNION — euler writes are silently ignored
        obj.rotation_euler = (0, 0, vp.get('ry', 0))
        print('[street] vendor prop', vp['name'],
              sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris')

def build_ground():
    site_box('ground', 'ground', 0, -0.05, 1.0, 60, 0.1, 46)
    site_box('sidewalk', 'sidewalk', -2.2, 0.06, -4.55, 17.6, 0.12, 0.9)
    site_box('sidewalk_l', 'sidewalk', -10.75, 0.06, 1.0, 0.9, 0.12, 13.0)

def build_buildings():
    for b in LAYOUT['buildings']:
        x0, x1 = b['x']; z0, z1 = b['z']; h = b['h']
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if b.get('ref'):
            # vendored facade: the asset brings its own detail — no parapet/windows
            objs = import_vendor(b['ref'], drop=b.get('drop', ()))
            obj = normalize_height(objs, 'bld_' + b['name'], h)
            decimate_to(obj, b.get('tris', 9000))
            ws = [obj.matrix_world @ v.co for v in obj.data.vertices]
            wx = max(w.x for w in ws) - min(w.x for w in ws)
            wy = max(w.y for w in ws) - min(w.y for w in ws)
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            obj.scale = ((x1 - x0) / max(1e-6, wx), (z1 - z0) / max(1e-6, wy), 1)
            bpy.ops.object.transform_apply(scale=True)
            obj.location = P(cx, 0, cz)
            print('[street] vendor facade', b['name'],
                  sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris')
            continue
        parts = [site_box(b['name'], b['mat'], cx, h / 2, cz, x1 - x0, h, z1 - z0)]
        parts.append(site_box(b['name'] + '_parapet', 'paper', cx, h + 0.12, cz, (x1 - x0) + 0.15, 0.24, (z1 - z0) + 0.15))
        # windows: dark punched shutters on the street face (z1 side for back row,
        # x1 side for the left building)
        if b['name'] != 'left':
            zf = z1 + 0.03
            cols = max(2, int((x1 - x0) / 1.6))
            rows = max(2, int(h / 2.2))
            for i in range(cols):
                for j in range(rows):
                    wx = x0 + (i + 0.5) * (x1 - x0) / cols
                    wy = 1.5 + j * (h - 2.2) / max(1, rows - 1)
                    parts.append(site_box('w', 'shutter', wx, wy, zf, 0.62, 0.95, 0.06))
                    parts.append(site_box('ws', 'paper', wx, wy + 0.55, zf + 0.02, 0.78, 0.09, 0.1))
        else:
            xf = x1 + 0.03
            for j in range(3):
                for k in range(4):
                    parts.append(site_box('w', 'shutter', xf, 1.6 + j * 2.1, -6.2 + k * 3.1, 0.06, 0.95, 0.62))
        join(parts, 'bld_' + b['name'])



def build_koshk():
    # the structure is the vendored Market Stand (placed via vendorProps);
    # what's built here is only the shop fixture set: shelf boards + lips,
    # the glow panel, the TEMPO sign, and the hand-painted banner.
    K = LAYOUT['koshk']; x, z, ry = K['x'], K['z'], K['ry']
    parts = []
    def kbox(name, m, lx, ly, lz, sx, sy, sz):
        c, s = math.cos(ry), math.sin(ry)
        wx = x + lx * c + lz * s
        wz = z - lx * s + lz * c
        parts.append(site_box(name, m, wx, ly, wz, sx, sy, sz, ry=ry))
    kbox('k_glow', 'fridge', 0, 1.35, 0.55, 2.0, 1.9, 0.05)
    for y in K['shelves']['ys']:
        kbox('k_shelf', 'woodLight', 0, y + 0.38, K['shelves']['slotZ'], 2.1, 0.05, 0.55)
        kbox('k_lip', 'wood', 0, y + 0.43, K['shelves']['slotZ'] - 0.28, 2.1, 0.06, 0.05)
    kbox('k_signboard', 'ink', 0, 2.85, -0.5, 2.9, 0.5, 0.1)
    join(parts, 'koshk_fixtures')
    # the hand-painted "cold drinks" strip on the stand's counter front
    c, s = math.cos(ry), math.sin(ry)
    lx, lz = 0, -1.02
    sign_plane('k_banner', mat_tex('signDrinks', 'sign_drinks.png'), 2.2, 0.32,
               x + lx * c + lz * s, 0.60, z - lx * s + lz * c, ry + math.pi)
    # TEMPO sign text (emissive)
    bpy.ops.object.text_add()
    t = bpy.context.active_object
    t.data.body = 'TEMPO'
    t.data.extrude = 0.02
    t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    lx, lz = 0, -0.56
    t.location = P(x + lx * c + lz * s, 2.85, z - lx * s + lz * c)
    t.rotation_euler = (math.radians(90), 0, ry + math.pi)
    t.scale = (0.55, 0.55, 0.55)
    bpy.ops.object.convert(target='MESH')
    t = bpy.context.active_object
    t.name = 'koshk_sign'
    t.data.materials.append(mat('sign'))


def build_minaret():
    mn = LAYOUT['props']['minaret']
    if mn.get('ref'):
        # the Samarra spiral — the silhouette against the sky is the whole point
        objs = import_vendor(mn['ref'])
        obj = normalize_height(objs, 'minaret', mn['h'])
        decimate_to(obj, mn.get('tris', 6000))
        obj.location = P(mn['x'], 0, mn['z'])
        print('[street] vendor minaret',
              sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris')
        return
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.9, depth=mn['h'], location=P(mn['x'], mn['h'] / 2, mn['z']))
    body = bpy.context.active_object
    body.data.materials.append(mat('plasterSand'))
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=1.25, depth=0.5, location=P(mn['x'], mn['h'] * 0.72, mn['z']))
    ring = bpy.context.active_object
    ring.data.materials.append(mat('paper'))
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=1.0, depth=2.4, location=P(mn['x'], mn['h'] + 1.2, mn['z']))
    top = bpy.context.active_object
    top.data.materials.append(mat('awningA'))
    join([body, ring, top], 'minaret')

def build_signage():
    # the كشك plaque, both faces of the hanging wooden-sign board. The board
    # interior is the sign's only woodLight-tinted region — measure it in
    # world space instead of trusting eyeballed offsets.
    vp = next((v for v in LAYOUT.get('vendorProps', []) if v['name'] == 'woodenSign'), None)
    obj = bpy.data.objects.get('woodenSign')
    if not vp or not obj: return
    # native vendor materials now — find the board face by its shipped name
    slot = next((i for i, sl in enumerate(obj.material_slots)
                 if sl.material and 'light wood' in sl.material.name.lower()), None)
    if slot is None:
        slot = next((i for i, sl in enumerate(obj.material_slots)
                     if sl.material and 'wood' in sl.material.name.lower()), None)
    if slot is None:
        print('[street] build_signage: no wood slot on the sign — plaque skipped')
        return
    # measure in the sign's LOCAL frame (mesh data is normalized; the object
    # carries rotation + location) so the thin axis is found honestly
    from mathutils import Vector
    bpy.context.view_layer.update()   # matrix_world is lazy — flush the placement above
    ls = []
    for p in obj.data.polygons:
        if p.material_index == slot:
            for vi in p.vertices:
                ls.append(obj.data.vertices[vi].co)
    lo = [min(v[i] for v in ls) for i in range(3)]
    hi = [max(v[i] for v in ls) for i in range(3)]
    dims = [hi[i] - lo[i] for i in range(3)]
    center = [(lo[i] + hi[i]) / 2 for i in range(3)]
    thin = 0 if dims[0] < dims[1] else 1
    ry = vp.get('ry', 0)
    m = mat_tex('signKoshk', 'sign_koshk.png')
    w = 0.8 * max(dims[0], dims[1])
    h = 0.8 * dims[2]
    for k, rz in ((1, ry), (-1, ry + math.pi)):
        off = list(center)
        off[thin] += k * (dims[thin] / 2 + 0.012)
        wp = obj.matrix_world @ Vector(off)
        bpy.ops.mesh.primitive_plane_add(size=1, location=wp,
                                         rotation=(math.radians(90), 0, rz))
        o = bpy.context.active_object
        o.scale = (w, h, 1)
        o.name = 'sign_ar'
        o.data.materials.append(m)
    print('[street] sign board face', [round(d, 2) for d in dims], 'plaque', round(w, 2), 'x', round(h, 2))


def local_frame(x, z, ry):
    c, s = math.cos(ry), math.sin(ry)
    return lambda lx, lz: (x + lx * c + lz * s, z - lx * s + lz * c)

def build_roadbed():
    # the street stops being a void: an asphalt strip with patch repairs and
    # manholes; the sand stays as aprons and the sidewalks stand proud as kerbs
    rb = LAYOUT['props']['roadbed']
    cx = (rb['x'][0] + rb['x'][1]) / 2; cz = (rb['z'][0] + rb['z'][1]) / 2
    site_box('roadbed', 'asphalt', cx, -0.015, cz, rb['x'][1] - rb['x'][0], 0.04, rb['z'][1] - rb['z'][0])
    for i, pa in enumerate(rb['patches']):
        site_box('patch_%d' % i, 'asphaltOld', pa['x'], 0.008, pa['z'], pa['w'], 0.01, pa['d'], ry=pa.get('ry', 0))
    for i, mh in enumerate(rb['manholes']):
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.32, depth=0.02, location=P(mh['x'], 0.012, mh['z']))
        o = bpy.context.active_object
        o.name = 'manhole_%d' % i
        o.data.materials.append(mat('metal'))






def build_rug():
    r = LAYOUT['props']['rug']
    site_box('rug', 'rug', r['x'], 0.02, r['z'], r['w'], 0.008, r['d'], ry=r.get('ry', 0))


def build_blob_shadows():
    # baked contact shadows: without them every prop floats on the flat ground.
    # (the runner gets a dynamic one at runtime)
    V = {v['name']: v for v in LAYOUT.get('vendorProps', [])}
    blobs = [
        (V['tuktuk']['x'], V['tuktuk']['z'], 1.75, 0.85, V['tuktuk']['ry']),
        (V['scooter']['x'], V['scooter']['z'], 0.95, 0.5, V['scooter']['ry']),
        (V['cart']['x'], V['cart']['z'], 1.1, 0.85, V['cart']['ry']),
        (-9.95, 0.4, 1.75, 1.6, 0),                    # ahwa cluster
        (V['canFridge']['x'], V['canFridge']['z'], 0.55, 0.55, 0),
        (6.45, -2.6, 0.78, 0.78, 0),                   # koshk crates
        (V['clayPots']['x'], V['clayPots']['z'], 0.5, 0.5, 0),
        (V['woodenSign']['x'], V['woodenSign']['z'], 0.5, 0.5, 0),
        (V['palmA']['x'], V['palmA']['z'], 0.85, 0.85, 0),
        (V['palmB']['x'], V['palmB']['z'], 0.75, 0.75, 0),
        (9.9, 1.35, 0.85, 1.05, 0),                    # east crate stack
    ]
    for i, (x, z, rx, rz, ry) in enumerate(blobs):
        bpy.ops.mesh.primitive_circle_add(vertices=16, radius=1, fill_type='TRIFAN',
                                          location=P(x, 0.028, z), rotation=(0, 0, ry))
        o = bpy.context.active_object
        o.scale = (rx, rz, 1)
        o.name = 'blob_%d' % i
        o.data.materials.append(mat('shadow'))

def uv_world_project(tile=2.0):
    # built geometry is textured now: project UVs from WORLD coords along each
    # face's dominant axis so one texture tile spans `tile` metres everywhere
    from mathutils import Vector
    bpy.context.view_layer.update()
    for obj in bpy.data.objects:
        if obj.type != 'MESH': continue
        names = {sl.material.name.split('.')[0] for sl in obj.material_slots if sl.material}
        if not (names & set(TEXTURED)): continue
        me = obj.data
        if not me.uv_layers: me.uv_layers.new(name='UVMap')
        uv = me.uv_layers.active.data
        mw = obj.matrix_world
        for poly in me.polygons:
            n = (mw.to_3x3() @ poly.normal)
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            for li in poly.loop_indices:
                co = mw @ me.vertices[me.loops[li].vertex_index].co
                if az >= ax and az >= ay: u, v = co.x, co.y
                elif ax >= ay:            u, v = co.y, co.z
                else:                     u, v = co.x, co.z
                uv[li].uv = (u / tile, v / tile)

def export_glb():
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    # the runtime fetches the same layout the sim and this build were made from
    with open(os.path.join(ROOT, 'assets', 'street', 'layout.json'), 'w') as f:
        json.dump(LAYOUT, f, indent=2)
    kwargs = dict(filepath=OUT_GLB, export_format='GLB', export_yup=True, export_apply=True)
    for extra in (dict(export_draco_mesh_compression_enable=True, export_image_format='WEBP', export_image_quality=72),
                  dict(export_draco_mesh_compression_enable=True),
                  dict()):
        try:
            bpy.ops.export_scene.gltf(**kwargs, **extra)
            print('[street] exported with', sorted(extra) or ['plain'])
            break
        except Exception as e:
            print('[street] export retry (%s)' % e)
    print('[street] glb bytes:', os.path.getsize(OUT_GLB))

def render_poster():
    scene = bpy.context.scene
    cam_data = bpy.data.cameras.new('poster_cam')
    cam_data.lens = 38
    cam = bpy.data.objects.new('poster_cam', cam_data)
    bpy.context.collection.objects.link(cam)
    cam_data.lens = 33
    cam.location = P(-1.2, 5.2, 8.6)
    # aim at the koshk corner via a track-to target
    tgt = bpy.data.objects.new('poster_tgt', None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = P(2.8, 2.2, -2.4)
    tc = cam.constraints.new('TRACK_TO')
    tc.target = tgt
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    scene.camera = cam
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'TEXTURE'   # baked sign textures show; textureless mats fall back to viewport color
    sh.show_cavity = True
    sh.show_shadows = True
    scene.display.shadow_focus = 0.6
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('w')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.93, 0.87, 0.78, 1)
    scene.world.color = (0.93, 0.87, 0.78)   # Workbench reads world.color, not the node tree
    os.makedirs(os.path.dirname(OUT_POSTER_PNG), exist_ok=True)
    scene.render.filepath = OUT_POSTER_PNG
    bpy.ops.render.render(write_still=True)
    print('[street] poster rendered')

clean()
build_ground()
build_roadbed()
build_buildings()
build_koshk()
build_vendor_props()
build_signage()
build_minaret()
build_rug()
build_blob_shadows()
uv_world_project()
export_glb()
render_poster()
print('[street] done')
