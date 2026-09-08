# build_runner.py — the KayKit adventurer becomes the TEMPO runner.
# Run: blender -b -P src-model/tools/build_runner.py
# Imports the vendored character + animation clips, strips the fantasy gear,
# re-tints to the brand (paper body / ink head / accent band), bakes the
# clips in place (the sim owns position) and exports assets/street/runner.glb.
import bpy, json, math, os, re, sys

# borrowed draco wrapper — same story as build_street.py
_DRACO = '/opt/blender-4.5.11-linux-x64/4.5/scripts/addons_core/io_scene_gltf2/libextern_draco.so'
if os.path.isfile(_DRACO):
    os.environ.setdefault('BLENDER_EXTERN_DRACO_LIBRARY_PATH', _DRACO)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')
OUT = os.path.join(ROOT, 'assets', 'street', 'runner.glb')
MAN = json.load(open(os.path.join(VENDOR, 'manifest.json')))

CHAR_GLB = os.path.join(VENDOR, 'kaykit-adventurers', 'Rogue.glb')
ANIM_GLB = os.path.join(VENDOR, 'kaykit-animations', 'Rig_Medium_MovementBasic.glb')

# Gear objects to strip — matched against object name (node name in glTF)
GEAR = re.compile(
    r'Knife_Offhand|Knife$|Throwable|1H_Crossbow|2H_Crossbow|Rogue_Cape'
    r'|sword|shield|axe|bow|staff|dagger|bag|hat|helmet|armor|quiver|potion|mug',
    re.I
)

PALETTE = {
    'runnerPaper':  (0.93, 0.90, 0.84, 1),
    'runnerInk':    (0.10, 0.09, 0.08, 1),
    'runnerAccent': (1.0, 0.478, 0.102, 1),
}

# ── material builder (same idiom as build_street.py) ──────────────────────────
MATS = {}
def mat(name):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = PALETTE[name]
    b.inputs['Roughness'].default_value = 0.9
    m.diffuse_color = PALETTE[name]   # Workbench reads viewport color
    MATS[name] = m
    return m


def clean():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                 bpy.data.textures, bpy.data.armatures, bpy.data.actions):
        for d in list(coll):
            coll.remove(d)


def import_glb(path):
    bpy.ops.import_scene.gltf(filepath=path)
    return list(bpy.context.selected_objects)


def get_armature(objects):
    for o in objects:
        if o.type == 'ARMATURE':
            return o
    return None


def strip_gear(char_objects):
    """Delete mesh objects whose names match the GEAR pattern. Print all."""
    kept, deleted = [], []
    for o in char_objects:
        if o.type != 'MESH':
            continue
        if GEAR.search(o.name):
            deleted.append(o.name)
        else:
            kept.append(o.name)
    print('[runner] gear strip — kept:', kept)
    print('[runner] gear strip — deleted:', deleted)
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.data.objects:
        if o.type == 'MESH' and GEAR.search(o.name):
            o.select_set(True)
    bpy.ops.object.delete()
    # asset packs ride with junk (the Rogue ships a 2m hidden Icosphere
    # template): the runner is ONE skinned character — any mesh with no
    # armature deform is not the runner and would ship as dead weight
    for o in list(bpy.data.objects):
        if o.type == 'MESH' and not any(m.type == 'ARMATURE' for m in o.modifiers):
            print('[runner] junk strip — deleted unskinned mesh:', o.name)
            kept = [k for k in kept if k != o.name]
            bpy.data.objects.remove(o)
    return kept


def verify_bones(arm_a, arm_b):
    """
    Compare bone sets.  The character rig may contain extra IK-controller bones
    (IK-foot, kneeIK, heelIK, elbowIK, control-*) not present in the animation
    rig — those are safe extras used for Blender IK solving.  What matters is
    that every bone in the animation rig exists in the character rig so that
    transferred actions can drive the character.  Abort only if the animation
    rig has bones MISSING from the character rig.
    """
    bones_a = set(arm_a.data.bones.keys())   # character
    bones_b = set(arm_b.data.bones.keys())   # animation rig
    char_only = bones_a - bones_b
    anim_only = bones_b - bones_a           # these would be truly missing
    print('[runner] char bones:', sorted(bones_a))
    print('[runner] anim bones:', sorted(bones_b))
    print('[runner] char-only (IK helpers OK):', sorted(char_only))
    print('[runner] anim-only (would be BLOCKED):', sorted(anim_only))
    if anim_only:
        print('BLOCKED: animation rig has bones absent from character rig.')
        print('Missing from char:', sorted(anim_only))
        sys.exit(1)
    if char_only:
        # Inspect whether they are all IK/control helpers
        ik_pattern = re.compile(r'IK|control|kneeIK|heelIK|elbowIK|handIK', re.I)
        non_ik = [b for b in char_only if not ik_pattern.search(b)]
        if non_ik:
            print('[runner] WARNING: char has non-IK extra bones:', non_ik)
        else:
            print('[runner] char extra bones are all IK helpers — safe to proceed')
    print('[runner] bone compatibility: OK — proceeding with character\'s own actions')


def pick_locomotion_trio():
    """
    From all actions in bpy.data.actions, pick Idle, Walk, Run.
    The character GLB already ships Idle, Walking_A, Running_A.
    Prefer Unarmed_Idle for a clean hand pose, Walking_A, Running_A.
    Returns dict: {'Idle': action, 'Walk': action, 'Run': action}
    """
    print('[runner] all actions in scene:',
          sorted(a.name for a in bpy.data.actions))
    result = {}
    # Actions are imported with the armature name appended, e.g. "Idle_Rig"
    idle_candidates  = ['Unarmed_Idle_Rig', 'Unarmed_Idle', 'Idle_Rig', 'Idle']
    walk_candidates  = ['Walking_A_Rig', 'Walking_A', 'Walk_A_Rig', 'Walk_A']
    run_candidates   = ['Running_A_Rig', 'Running_A', 'Run_A_Rig', 'Run_A']

    def pick(candidates, label):
        for name in candidates:
            a = bpy.data.actions.get(name)
            if a:
                print(f'[runner] picked {label}: {name!r}')
                return a
        # fallback: regex search — prefer most specific match
        # For Idle: prefer Unarmed_Idle over 2H_Melee_Idle etc.
        if label == 'Idle':
            for a in sorted(bpy.data.actions, key=lambda x: x.name):
                if re.search(r'unarmed_idle', a.name, re.I):
                    print(f'[runner] picked {label} (unarmed): {a.name!r}')
                    return a
            for a in sorted(bpy.data.actions, key=lambda x: x.name):
                # match bare "Idle" not preceded by other words
                if re.search(r'(?<![A-Za-z])Idle(?![A-Za-z])', a.name):
                    print(f'[runner] picked {label} (bare): {a.name!r}')
                    return a
        pattern = re.compile(r'^' + label.lower(), re.I)
        for a in sorted(bpy.data.actions, key=lambda x: x.name):
            if pattern.search(a.name):
                print(f'[runner] picked {label} (prefix): {a.name!r}')
                return a
        print(f'[runner] ERROR: could not find {label} action')
        sys.exit(1)

    result['Idle'] = pick(idle_candidates, 'Idle')
    result['Walk'] = pick(walk_candidates, 'Walk')
    result['Run']  = pick(run_candidates,  'Run')
    return result


def zero_xz_fcurves(action, bone_name):
    """
    For the given bone's location channels (X=array_index 0, Z=array_index 2
    in Blender's bone-space where Y is up the bone), zero the XZ channels.
    Bone location data_path: pose.bones["hips"].location
    Array indices: 0=X, 1=Y, 2=Z in bone local space, but for root/hips
    translating in world XZ corresponds to indices 0 and 2.
    """
    dp = f'pose.bones["{bone_name}"].location'
    to_remove = []
    for fc in action.fcurves:
        if fc.data_path == dp and fc.array_index in (0, 2):
            # Measure max displacement before removal
            vals = [kp.co[1] for kp in fc.keyframe_points]
            disp = max(abs(v) for v in vals) if vals else 0.0
            print(f'[runner] {action.name} {bone_name} axis={fc.array_index} '
                  f'max_displacement={disp:.4f}m')
            if disp > 0.01:
                to_remove.append(fc)
    for fc in to_remove:
        action.fcurves.remove(fc)
    print(f'[runner] {action.name}: removed {len(to_remove)} XZ fcurves from {bone_name}')
    # Brief Step 2: re-verify XZ displacement after removal (must be < 0.01m)
    dp_check = f'pose.bones["{bone_name}"].location'
    post_disp = 0.0
    for fc in action.fcurves:
        if fc.data_path == dp_check and fc.array_index in (0, 2):
            vals = [kp.co[1] for kp in fc.keyframe_points]
            d = max(abs(v) for v in vals) if vals else 0.0
            post_disp = max(post_disp, d)
    clip = action.name
    print(f'[runner] {clip} post-bake XZ displacement: {post_disp:.4f}m')
    if post_disp >= 0.01:
        print(f'ERROR: post-bake XZ displacement {post_disp:.4f}m >= 0.01m for {clip} / {bone_name}')
        sys.exit(1)


def bake_in_place(trio):
    """Zero XZ root motion on hips (and root if present) for all three actions."""
    root_bones = ['hips', 'root', 'Root', 'Hips']
    for label, action in trio.items():
        print(f'[runner] root motion check: {label} ({action.name!r})')
        for bone in root_bones:
            zero_xz_fcurves(action, bone)


def retint_materials(char_mesh_objects):
    """
    Assign runnerPaper / runnerInk / runnerAccent.
    Brand spec: paper body, accent STRIPE (one narrow surface), ink head.
    Arms → runnerPaper, Legs → runnerPaper, Head → runnerInk.

    Priority ladder (first rung that applies fires):
      0. Log all original material slot names for each kept object.
      1. If Body has a slot matching belt|strap|trim and that slot's faces are
         < 15% of the body face count: per-slot retint (slot → accent, rest → paper).
      2. Else if any leg/foot object or slot matches boot|foot|shoe: that surface → accent.
      3. Else (fallback): waist face-band — append runnerAccent slot to body mesh
         and assign it to faces whose world-space center height falls in
         [0.44, 0.49] × total mesh height (a thin ring, ~5% of total height).
    """
    import bmesh as _bmesh

    # ── Step 0: log every kept object's original slot names ──────────────────
    print('[runner] material slot inventory (before retint):')
    for o in char_mesh_objects:
        slots = [s.material.name if s.material else '<none>'
                 for s in o.material_slots]
        print(f'[runner]   {o.name}: {slots}')

    # Separate head from body meshes for initial pass
    head_objects = [o for o in char_mesh_objects if re.search(r'Head', o.name, re.I)]
    arm_objects  = [o for o in char_mesh_objects if re.search(r'Arm', o.name, re.I)]
    leg_objects  = [o for o in char_mesh_objects if re.search(r'Leg', o.name, re.I)]
    body_objects = [o for o in char_mesh_objects
                    if not re.search(r'Head|Arm|Leg', o.name, re.I)]

    # Arms → always paper (review finding: orange arms failed spec)
    # Legs → always paper
    # Head → always ink
    # Accent landing decided by ladder below

    rung_fired = None
    accent_applied = False   # will be set True once accent lands somewhere

    # ── Rung 1: belt|strap|trim slot on body, face share < 15% ──────────────
    trim_pattern = re.compile(r'belt|strap|trim', re.I)
    for o in body_objects:
        for slot_idx, slot in enumerate(o.material_slots):
            slot_name = slot.material.name if slot.material else ''
            if not trim_pattern.search(slot_name):
                continue
            # Count faces assigned to this slot vs total
            mesh = o.data
            total_faces = len(mesh.polygons)
            slot_faces  = sum(1 for p in mesh.polygons if p.material_index == slot_idx)
            share = slot_faces / total_faces if total_faces else 1.0
            print(f'[runner] Rung-1 candidate: {o.name!r} slot[{slot_idx}]={slot_name!r} '
                  f'faces={slot_faces}/{total_faces} ({share:.1%})')
            if share < 0.15:
                # Per-slot retint: keep slot structure, remap colors
                print(f'[runner] Rung 1 FIRES — per-slot retint on {o.name!r}')
                rung_fired = 1
                slot_count = len(o.material_slots)
                for i, sl in enumerate(o.material_slots):
                    sn = sl.material.name if sl.material else ''
                    if trim_pattern.search(sn):
                        sl.material = mat('runnerAccent')
                        print(f'[runner]   slot[{i}] {sn!r} → runnerAccent')
                    else:
                        sl.material = mat('runnerPaper')
                        print(f'[runner]   slot[{i}] {sn!r} → runnerPaper')
                accent_applied = True
                break
        if rung_fired:
            break

    # ── Rung 2: boot|foot|shoe on any leg/foot object or slot ────────────────
    if not rung_fired:
        boot_pattern = re.compile(r'boot|foot|shoe', re.I)
        for o in leg_objects + body_objects:
            # Check object name
            if boot_pattern.search(o.name):
                print(f'[runner] Rung 2 FIRES — boot object {o.name!r} → runnerAccent')
                rung_fired = 2
                o.data.materials.clear()
                o.data.materials.append(mat('runnerAccent'))
                accent_applied = True
                break
            # Check slot names
            for slot_idx, slot in enumerate(o.material_slots):
                sn = slot.material.name if slot.material else ''
                if boot_pattern.search(sn):
                    total_faces = len(o.data.polygons)
                    slot_faces  = sum(1 for p in o.data.polygons
                                      if p.material_index == slot_idx)
                    print(f'[runner] Rung 2 FIRES — boot slot {sn!r} on {o.name!r} '
                          f'({slot_faces}/{total_faces} faces) → runnerAccent')
                    rung_fired = 2
                    # Per-slot: boot slot → accent, rest → paper
                    for i, sl in enumerate(o.material_slots):
                        s = sl.material.name if sl.material else ''
                        sl.material = mat('runnerAccent') if boot_pattern.search(s) \
                                      else mat('runnerPaper')
                    accent_applied = True
                    break
            if rung_fired:
                break

    # ── Rung 3 (fallback): waist face-band on body mesh ──────────────────────
    if not rung_fired:
        print('[runner] Rung 3 FIRES — waist face-band on body mesh')
        rung_fired = 3
        # Work on first body object (should be Rogue_Body)
        body_obj = body_objects[0] if body_objects else None
        if body_obj is None and char_mesh_objects:
            body_obj = [o for o in char_mesh_objects
                        if not re.search(r'Head', o.name, re.I)][0]

        if body_obj:
            # Clear body slots, reset to single paper slot first
            body_obj.data.materials.clear()
            body_obj.data.materials.append(mat('runnerPaper'))   # slot 0
            body_obj.data.materials.append(mat('runnerAccent'))  # slot 1

            # Compute world-space Z bounds of the body mesh
            mw = body_obj.matrix_world
            all_z = [(mw @ v.co).z for v in body_obj.data.vertices]
            z_min, z_max = min(all_z), max(all_z)
            total_h = z_max - z_min

            band_lo = z_min + 0.44 * total_h
            band_hi = z_min + 0.49 * total_h
            print(f'[runner] Rung-3 band: z=[{band_lo:.3f}, {band_hi:.3f}] '
                  f'(total_h={total_h:.3f})')

            bm = _bmesh.new()
            bm.from_mesh(body_obj.data)
            accent_count = 0
            for face in bm.faces:
                # World-space face center Z
                face_z = (mw @ face.calc_center_median()).z
                if band_lo <= face_z <= band_hi:
                    face.material_index = 1   # runnerAccent
                    accent_count += 1
                else:
                    face.material_index = 0   # runnerPaper
            bm.to_mesh(body_obj.data)
            bm.free()
            body_obj.data.update()
            total_faces = len(body_obj.data.polygons)
            print(f'[runner] Rung-3: {accent_count}/{total_faces} faces → runnerAccent '
                  f'({accent_count/total_faces:.1%} of body)')
            accent_applied = True

    # ── Assign all non-rung-managed objects ──────────────────────────────────
    # Track which objects were fully handled by the rung so we don't overwrite them
    rung_handled = set()  # object names already retinted by the rung

    if rung_fired == 1:
        # The body object that had the trim slot was handled in-place above;
        # record all body objects as handled (there is only one body mesh, Rogue_Body)
        rung_handled.update(o.name for o in body_objects)

    if rung_fired == 2:
        # The leg/body object that matched boot|foot|shoe was handled above
        # Track it by checking which objects now have runnerAccent as slot 0
        boot_handled_pattern = re.compile(r'boot|foot|shoe', re.I)
        for o in leg_objects + body_objects:
            if boot_handled_pattern.search(o.name):
                rung_handled.add(o.name)
            elif any(boot_handled_pattern.search(sl.material.name if sl.material else '')
                     for sl in o.material_slots):
                rung_handled.add(o.name)

    if rung_fired == 3:
        # body_obj (body_objects[0]) was handled in-place — mark it
        if body_objects:
            rung_handled.add(body_objects[0].name)

    # Head → ink always (never rung-managed)
    for o in head_objects:
        print(f'[runner] retint: {o.name!r} → runnerInk')
        o.data.materials.clear()
        o.data.materials.append(mat('runnerInk'))

    # Arms → paper always (brief spec: paper limbs)
    for o in arm_objects:
        print(f'[runner] retint: {o.name!r} → runnerPaper')
        o.data.materials.clear()
        o.data.materials.append(mat('runnerPaper'))

    # Legs → paper (unless rung already handled this object)
    for o in leg_objects:
        if o.name in rung_handled:
            print(f'[runner] retint: {o.name!r} → (already set by Rung {rung_fired})')
        else:
            print(f'[runner] retint: {o.name!r} → runnerPaper')
            o.data.materials.clear()
            o.data.materials.append(mat('runnerPaper'))

    # Body → paper (unless rung already handled this object)
    for o in body_objects:
        if o.name in rung_handled:
            print(f'[runner] retint: {o.name!r} → (already set by Rung {rung_fired})')
        else:
            print(f'[runner] retint: {o.name!r} → runnerPaper')
            o.data.materials.clear()
            o.data.materials.append(mat('runnerPaper'))

    print(f'[runner] retint complete — Rung {rung_fired} fired, '
          f'accent_applied={accent_applied}')
    return rung_fired


def normalize_height(char_arm):
    """Scale the rig so the SKINNED character stands 1.75m.

    Two traps live here (both shipped once, caught by verify_street_glb.py):
    - raw `v.co` heights lie for skinned meshes — measure through the
      evaluated depsgraph (the armature deform three.js will render);
    - `transform_apply(scale)` on an armature shrinks the rest skeleton but
      leaves the deformed mesh untouched (rest-pose deform is identity), so
      the factor must STAY on the armature node — glTF exports node TRS, the
      skinned mesh inherits it, and bone-local clips are unaffected.
    """
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    if not meshes:
        print('[runner] WARNING: no meshes found for height normalization')
        return

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

    current_h = skinned_height()
    print(f'[runner] skinned bbox height: {current_h:.3f}m (target 1.75m)')
    if current_h <= 0.01:
        print('[runner] WARNING: degenerate bbox, skipping height normalize')
        return
    s = 1.75 / current_h
    # bake the factor into the DATA (rest bones, verts, location keys), not
    # object transforms — the glTF exporter drops armature-object scale for
    # skinned meshes (joints export from armature data)
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
    print(f'[runner] scaled by {s:.4f} → skinned height now {skinned_height():.3f}m')


def finalize_actions(trio, char_arm):
    """Rename actions to Idle/Walk/Run, delete rest, set use_fake_user."""
    # Rename the three keepers first
    for new_name, action in trio.items():
        action.name = new_name
        action.use_fake_user = True
    keeper_names = {'Idle', 'Walk', 'Run'}
    # Delete all other actions
    for a in list(bpy.data.actions):
        if a.name not in keeper_names:
            bpy.data.actions.remove(a)
    # Assign the first action to armature so exporter can find NLA tracks
    char_arm.animation_data_create()
    char_arm.animation_data.action = bpy.data.actions.get('Idle')
    # Push all three into NLA strips so they all get exported
    bpy.ops.object.select_all(action='DESELECT')
    char_arm.select_set(True)
    bpy.context.view_layer.objects.active = char_arm
    for name in ('Idle', 'Walk', 'Run'):
        action = bpy.data.actions.get(name)
        if action is None:
            continue
        track = char_arm.animation_data.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, int(action.frame_range[0]), action)
        strip.action = action
        print(f'[runner] NLA strip created: {name}')
    print('[runner] final actions:', [a.name for a in bpy.data.actions])


def export_glb():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    kwargs = dict(
        filepath=OUT,
        export_format='GLB',
        export_yup=True,
        export_animations=True,
        export_apply=False,   # keep armature transforms intact
    )
    draco_ok = False
    try:
        bpy.ops.export_scene.gltf(**kwargs,
                                   export_draco_mesh_compression_enable=True)
        draco_ok = True
    except Exception as e:
        print(f'[runner] draco unavailable ({e}), plain export')
    if not draco_ok:
        bpy.ops.export_scene.gltf(**kwargs)
    print(f'[runner] exported (draco={draco_ok})')
    print('[runner] glb bytes:', os.path.getsize(OUT))


def render_check(char_arm):
    """Quick Workbench still to src-model/tools/out/runner_check.png."""
    scene = bpy.context.scene
    cam_data = bpy.data.cameras.new('check_cam')
    cam_data.lens = 50
    cam = bpy.data.objects.new('check_cam', cam_data)
    bpy.context.collection.objects.link(cam)
    # Place camera in front-ish ¾ position
    cam.location = (2.5, -3.5, 1.8)
    tgt = bpy.data.objects.new('check_tgt', None)
    bpy.context.collection.objects.link(tgt)
    tgt.location = (0.0, 0.0, 0.9)
    tc = cam.constraints.new('TRACK_TO')
    tc.target = tgt
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    scene.camera = cam
    scene.render.engine = 'BLENDER_WORKBENCH'
    sh = scene.display.shading
    sh.light = 'STUDIO'
    sh.color_type = 'MATERIAL'
    sh.show_cavity = True
    sh.show_shadows = True
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new('check_world')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (
        0.93, 0.87, 0.78, 1)
    out_png = os.path.join(HERE, 'out', 'runner_check.png')
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print('[runner] check render:', out_png)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

print('[runner] starting')
# Brief Step 1: factory-clean scene first (required by spec)
bpy.ops.wm.read_factory_settings(use_empty=True)

# ── Step 1: import character ───────────────────────────────────────────────────
print('[runner] importing character:', CHAR_GLB)
char_objects = import_glb(CHAR_GLB)
char_arm = get_armature(char_objects)
if char_arm is None:
    print('ERROR: no armature found in character GLB')
    sys.exit(1)
print('[runner] character armature:', char_arm.name)
print('[runner] character objects:', [o.name for o in char_objects])

# Record object names from both imports before any deletions invalidate references
char_obj_names_all = set(o.name for o in char_objects)

# ── Step 1b: strip gear ────────────────────────────────────────────────────────
kept_meshes = strip_gear(char_objects)
# Character body mesh names we know survive the strip
CHAR_BODY_NAMES = {'Rogue_ArmLeft', 'Rogue_ArmRight', 'Rogue_Body',
                   'Rogue_Head', 'Rogue_LegLeft', 'Rogue_LegRight'}

# ── Step 1c: import animation GLB for bone verification ───────────────────────
print('[runner] importing animation rig:', ANIM_GLB)
# Record what exists before import so we can identify new objects
pre_import_names = set(o.name for o in bpy.data.objects)
anim_objects = import_glb(ANIM_GLB)
anim_obj_names = set(o.name for o in bpy.data.objects) - pre_import_names
anim_arm = get_armature(anim_objects)
if anim_arm is None:
    print('[runner] WARNING: no armature in animation GLB, skipping verification')
else:
    verify_bones(char_arm, anim_arm)

# Delete all objects that arrived with the animation GLB import
bpy.ops.object.select_all(action='DESELECT')
for o in list(bpy.data.objects):
    if o.name in anim_obj_names:
        o.select_set(True)
bpy.ops.object.delete()
# Clean up orphaned data from the mannequin (meshes, armatures, materials)
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)
for arm in list(bpy.data.armatures):
    if arm.users == 0:
        bpy.data.armatures.remove(arm)
# Remove any stray non-character objects (Icospheres etc.) that may have
# been created during the import process
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name not in CHAR_BODY_NAMES:
        print(f'[runner] removing stray object: {o.name}')
        bpy.data.objects.remove(o, do_unlink=True)
# Final cleanup of zero-user meshes
for mesh in list(bpy.data.meshes):
    if mesh.users == 0:
        bpy.data.meshes.remove(mesh)

print('[runner] scene objects after anim cleanup:',
      [o.name for o in bpy.data.objects])

# ── Step 2: pick + bake locomotion trio ────────────────────────────────────────
trio = pick_locomotion_trio()
bake_in_place(trio)

# ── Step 3: re-tint and normalize height ──────────────────────────────────────
# final junk sweep: BOTH vendor files ride with template meshes (the
# animations rig ships its own 2m Icosphere); the runner is one character
# skinned to char_arm — anything else is dead wire weight
for o in list(bpy.data.objects):
    if o.type == 'MESH' and not any(
            m.type == 'ARMATURE' and m.object == char_arm for m in o.modifiers):
        print('[runner] junk sweep — deleted non-runner mesh:', o.name)
        bpy.data.objects.remove(o)
surviving_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
print('[runner] surviving mesh objects:', [o.name for o in surviving_meshes])
retint_materials(surviving_meshes)
normalize_height(char_arm)

# ── Step 3b: rename/trim/finalize actions ─────────────────────────────────────
finalize_actions(trio, char_arm)

# ── Step 4: export ────────────────────────────────────────────────────────────
export_glb()

# ── Step 6: eyeball render ────────────────────────────────────────────────────
render_check(char_arm)

print('[runner] done')
