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

MATS = {}
def mat(name):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
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

def import_vendor(ref, drop=()):
    # ref: "vendor:<dir>/<relpath>" — resolves under src-model/vendor/
    # drop: object-name prefixes to discard (ground planes riding along in the file)
    path = os.path.join(VENDOR, ref.split(':', 1)[1])
    before = set(bpy.data.objects)
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
    kept = []
    for o in meshes:
        hidden = o.hide_viewport or not o.visible_get()
        if hidden or any(o.name.startswith(d) for d in drop):
            print('[street] import_vendor dropped', o.name, '(hidden)' if hidden else '')
            bpy.data.objects.remove(o)
        else:
            kept.append(o)
    return kept

def palette_strip(objs, tints):
    # every source material dies here; the palette is the only survivor
    for o in objs:
        names = [s.material.name.split('.')[0] if s.material else '' for s in o.material_slots]
        idx = [p.material_index for p in o.data.polygons]   # materials.clear() resets these to 0
        o.data.materials.clear()
        while o.data.uv_layers:             # flat palette colors never sample UVs
            o.data.uv_layers.remove(o.data.uv_layers[0])
        keys = [next((v for k, v in tints.items() if k != '*' and k.lower() in n.lower()),
                     tints.get('*', 'paper')) for n in names] or [tints.get('*', 'paper')]
        for key in keys: o.data.materials.append(mat(key))
        if len(keys) > 1:   # restore per-face slots, clamped
            for p, i in zip(o.data.polygons, idx):
                p.material_index = min(i, len(keys) - 1)

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
    if cur <= tris: return
    m = obj.modifiers.new('dec', 'DECIMATE')
    m.ratio = tris / cur
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='dec')

def build_vendor_props():
    for vp in LAYOUT.get('vendorProps', []):
        objs = import_vendor(vp['ref'], drop=vp.get('drop', ()))
        palette_strip(objs, vp.get('tints', {'*': 'paper'}))
        obj = normalize_height(objs, vp['name'], vp['height'])
        decimate_to(obj, vp.get('tris', 3000))
        obj.location = P(vp['x'], vp.get('y', 0), vp['z'])
        obj.rotation_mode = 'XYZ'   # glTF imports arrive QUATERNION — euler writes are silently ignored
        obj.rotation_euler = (0, 0, vp.get('ry', 0))
        print('[street] vendor prop', vp['name'],
              sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris')

def build_ground():
    site_box('ground', 'ground', 0, -0.05, -0.25, 27, 0.1, 16.5)
    site_box('sidewalk', 'sidewalk', -2.2, 0.06, -4.55, 17.6, 0.12, 0.9)
    site_box('sidewalk_l', 'sidewalk', -10.75, 0.06, 1.0, 0.9, 0.12, 13.0)

def build_buildings():
    for b in LAYOUT['buildings']:
        x0, x1 = b['x']; z0, z1 = b['z']; h = b['h']
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if b.get('ref'):
            # vendored facade: the asset brings its own detail — no parapet/windows
            objs = import_vendor(b['ref'], drop=b.get('drop', ()))
            palette_strip(objs, b.get('tints', {'*': b['mat']}))
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
            # a couple of AC units
            parts.append(site_box('ac', 'metal', x0 + 1.1, h - 1.3, zf + 0.12, 0.7, 0.45, 0.3))
        else:
            xf = x1 + 0.03
            for j in range(3):
                for k in range(4):
                    parts.append(site_box('w', 'shutter', xf, 1.6 + j * 2.1, -6.2 + k * 3.1, 0.06, 0.95, 0.62))
        join(parts, 'bld_' + b['name'])

def build_awnings():
    for a in LAYOUT['props']['awnings']:
        parts = []
        stripes = 6
        for i in range(stripes):
            sx = a['w'] / stripes
            x = a['x'] - a['w'] / 2 + (i + 0.5) * sx
            m = a['mats'][i % 2]
            bpy.ops.mesh.primitive_cube_add(size=1, location=P(x, a['y'], a['z'] + a['d'] / 2))
            o = bpy.context.active_object
            o.scale = (sx * 0.98, a['d'], 0.04)
            o.rotation_euler = (0.35, 0, 0)
            o.data.materials.append(mat(m))
            parts.append(o)
        join(parts, 'awning')

def build_mashrabiya():
    mb = LAYOUT['props']['mashrabiya']
    parts = [site_box('mb_base', 'wood', mb['x'], mb['y'] - mb['h'] / 2, mb['z'] + mb['d'] / 2, mb['w'], 0.1, mb['d'])]
    parts.append(site_box('mb_top', 'wood', mb['x'], mb['y'] + mb['h'] / 2, mb['z'] + mb['d'] / 2, mb['w'], 0.1, mb['d']))
    n = 9
    for i in range(n):
        x = mb['x'] - mb['w'] / 2 + (i + 0.5) * mb['w'] / n
        parts.append(site_box('mb_v', 'woodLight', x, mb['y'], mb['z'] + mb['d'], 0.05, mb['h'], 0.05))
    for j in range(4):
        y = mb['y'] - mb['h'] / 2 + (j + 0.5) * mb['h'] / 4
        parts.append(site_box('mb_h', 'woodLight', mb['x'], y, mb['z'] + mb['d'], mb['w'], 0.05, 0.05))
    join(parts, 'mashrabiya')

def build_koshk():
    K = LAYOUT['koshk']; x, z, ry = K['x'], K['z'], K['ry']
    parts = []
    def kbox(name, m, lx, ly, lz, sx, sy, sz):
        c, s = math.cos(ry), math.sin(ry)
        wx = x + lx * c + lz * s
        wz = z - lx * s + lz * c
        parts.append(site_box(name, m, wx, ly, wz, sx, sy, sz, ry=ry))
    # shell: back, roof, floor, sides; open front (front = local -z)
    kbox('k_back', 'wood', 0, 1.25, 0.95, 2.9, 2.5, 0.12)
    kbox('k_roof', 'wood', 0, 2.56, 0.15, 3.3, 0.14, 2.2)
    kbox('k_floor', 'woodLight', 0, 0.2, 0.15, 3.0, 0.4, 1.9)
    kbox('k_l', 'wood', -1.45, 1.25, 0.15, 0.12, 2.5, 1.9)
    kbox('k_r', 'wood', 1.45, 1.25, 0.15, 0.12, 2.5, 1.9)
    # glow panel behind the shelves + shelf boards
    kbox('k_glow', 'fridge', 0, 1.35, 0.85, 2.6, 1.9, 0.05)
    for y in K['shelves']['ys']:
        kbox('k_shelf', 'woodLight', 0, y + 0.38, K['shelves']['slotZ'], 2.5, 0.05, 0.55)
    # counter + sign board
    kbox('k_counter', 'woodLight', 0, 0.55, -0.85, 2.9, 0.5, 0.35)
    kbox('k_signboard', 'ink', 0, 2.85, -0.6, 3.2, 0.5, 0.1)
    join(parts, 'koshk')
    # the hand-painted "cold drinks" strip across the counter front
    c, s = math.cos(ry), math.sin(ry)
    lx, lz = 0, -1.045
    sign_plane('k_banner', mat_tex('signDrinks', 'sign_drinks.png'), 2.5, 0.34,
               x + lx * c + lz * s, 0.60, z - lx * s + lz * c, ry + math.pi)
    # TEMPO sign text (separate, emissive)
    bpy.ops.object.text_add()
    t = bpy.context.active_object
    t.data.body = 'TEMPO'
    t.data.extrude = 0.02
    t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    c, s = math.cos(ry), math.sin(ry)
    lx, lz = 0, -0.66
    t.location = P(x + lx * c + lz * s, 2.85, z - lx * s + lz * c)
    t.rotation_euler = (math.radians(90), 0, ry + math.pi)
    t.scale = (0.55, 0.55, 0.55)
    bpy.ops.object.convert(target='MESH')
    t = bpy.context.active_object
    t.name = 'koshk_sign'
    t.data.materials.append(mat('sign'))

def build_props():
    for i, cr in enumerate(LAYOUT['props']['crates']):
        p = [site_box('crate', 'wood', cr['x'], cr['y'], cr['z'], cr['s'], cr['s'], cr['s'], ry=cr['ry'])]
        p.append(site_box('crate_t', 'woodLight', cr['x'], cr['y'] + cr['s'] * 0.28, cr['z'], cr['s'] * 1.04, cr['s'] * 0.1, cr['s'] * 1.04, ry=cr['ry']))
        join(p, 'crate_%d' % i)
    # (the cat is a vendored Quaternius blob now — see vendorProps)
    for lp in LAYOUT['props']['lampPosts']:
        p = [site_box('lp', 'ink', lp['x'], 2.2, lp['z'], 0.09, 4.4, 0.09)]
        p.append(site_box('lp_head', 'ink', lp['x'], 4.45, lp['z'], 0.3, 0.16, 0.3))
        join(p, 'lamp')

def build_string_lights():
    for si, sl in enumerate(LAYOUT['props']['stringLights']):
        ax, ay, az = sl['a']; bx, by, bz = sl['b']
        pts = []
        n = 24
        for i in range(n + 1):
            t = i / n
            x = ax + (bx - ax) * t
            z = az + (bz - az) * t
            y = ay + (by - ay) * t - sl['sag'] * math.sin(math.pi * t)
            pts.append((x, y, z))
        cu = bpy.data.curves.new('wire', 'CURVE')
        cu.dimensions = '3D'; cu.bevel_depth = 0.012; cu.bevel_resolution = 1
        sp = cu.splines.new('POLY'); sp.points.add(n)
        for i, (x, y, z) in enumerate(pts):
            bx_, by_, bz_ = P(x, y, z)
            sp.points[i].co = (bx_, by_, bz_, 1)
        ob = bpy.data.objects.new('wire_%d' % si, cu)
        bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat('ink'))
        bulbs = []
        for i in range(sl['bulbs']):
            t = (i + 1) / (sl['bulbs'] + 1)
            x = ax + (bx - ax) * t
            z = az + (bz - az) * t
            y = ay + (by - ay) * t - sl['sag'] * math.sin(math.pi * t) - 0.09
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=0.05, location=P(x, y, z))
            o = bpy.context.active_object
            o.data.materials.append(mat('bulb'))
            bulbs.append(o)
        join(bulbs, 'bulbs_%d' % si)

def build_minaret():
    mn = LAYOUT['props']['minaret']
    if mn.get('ref'):
        # the Samarra spiral — the silhouette against the sky is the whole point
        objs = import_vendor(mn['ref'])
        palette_strip(objs, mn.get('tints', {'*': 'plasterSand'}))
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
    slot = next((i for i, sl in enumerate(obj.material_slots)
                 if sl.material and sl.material.name == 'woodLight'), None)
    if slot is None:
        print('[street] build_signage: no woodLight slot on the sign — plaque skipped')
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

def export_glb():
    os.makedirs(os.path.dirname(OUT_GLB), exist_ok=True)
    # the runtime fetches the same layout the sim and this build were made from
    with open(os.path.join(ROOT, 'assets', 'street', 'layout.json'), 'w') as f:
        json.dump(LAYOUT, f, indent=2)
    kwargs = dict(filepath=OUT_GLB, export_format='GLB', export_yup=True, export_apply=True)
    try:
        bpy.ops.export_scene.gltf(**kwargs, export_draco_mesh_compression_enable=True)
        print('[street] exported with draco')
    except Exception as e:
        print('[street] draco unavailable (%s), plain export' % e)
        bpy.ops.export_scene.gltf(**kwargs)
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
build_buildings()
build_awnings()
build_mashrabiya()
build_koshk()
build_props()
build_vendor_props()
build_signage()
build_string_lights()
build_minaret()
export_glb()
render_poster()
print('[street] done')
