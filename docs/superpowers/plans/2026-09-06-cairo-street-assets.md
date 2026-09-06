# Cairo Street Asset Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the procedural Cairo street's fabric, props and runner with the license-verified external assets from the research ledger, then un-dock section 05 and ship.

**Architecture:** External assets become inputs to the Blender pipeline: `build_street.py` imports, palette-locks, decimates and joins them into the same single draco `street.glb`; a new `build_runner.py` exports a skinned `runner.glb` (Idle/Walk/Run). `street.js` swaps its primitives runner for the animated one; pure action selection lives in `street-sim.js`. Machine gates: wire/tri budgets, palette lock, clip names, attribution.

**Tech Stack:** Blender 4.0.2 headless (`blender -b -P`), three.js 0.169 (importmap, GLTFLoader+DRACOLoader already wired), node 20 (`oracle/street.mjs`), Playwright headless Chromium (`oracle/verify-street.py`), Python 3 + Pillow.

**Spec:** `docs/superpowers/specs/2026-09-06-cairo-street-assets-design.md` (and the ledger it argues from: `docs/superpowers/research/2026-09-05-cairo-street-assets.md`).

## Global Constraints

- Budgets (hard): street.glb + runner.glb + poster.webp total wire ≤ 5MB; street ≤ 120k tris in view; poster.webp ≤ 150KB.
- Palette lock: every exported material color ∈ the `PALETTE`/`EMISSIVE` sets in `build_street.py` (+ the three runner materials). No asset-pack material survives import.
- `street_layout.json` is the single source of truth — Blender build, sim colliders, runtime anchors all read it; `build_street.py` copies it to `assets/street/layout.json`.
- Licensing: CC0 and CC-BY only. Every CC-BY asset needs a NOTICE.md entry (title, author, source URL, license URL, modifications note — decimation and draco recompression count). Mixamo files NEVER enter the repo. No NEW Quaternius packs (post-2026-08-28 = QAL); pre-QAL poly.pizza pages govern. Keep receipts.
- Blender Workbench renders viewport colors: set `mat.diffuse_color` alongside Principled inputs (the `mat()` helper already does — route ALL materials through it).
- Battery discipline: poll settle state (`TempoStreet.state.camDist`, two-sample motion), never wall-clock waits before 3D-projected clicks. Browser launches on this box may need `TMPDIR=$HOME/tmp` (ENOSPC trap).
- CSS: append street styles at the end of `styles.css` (≤940px media blocks override by file order).
- Commits: author is the repo default (Menese DeFi Team); never add personal names or AI attribution.
- Deploy (Task 9 only): `cp <changed> dist/` + `thebes-deploy deploy --skip-install --no-facts`; bump `?v=N` on everything changed in the same commit; keep pinned `cid`s.

---

### Task 1: Vendor tree, gitignore exception, manifest + CC0 fetches

**Files:**
- Modify: `.gitignore` (the `src-model/*` block)
- Create: `src-model/vendor/manifest.json`
- Create: `src-model/vendor/<source>/RECEIPT.md` + asset files (kaykit-adventurers, kaykit-animations, kenney-fantasy-town, kenney-city-commercial, quaternius, kaykit-props, ipoly3d)
- Create: `src-model/tools/check_vendor.py`
- Test: `python3 src-model/tools/check_vendor.py`

**Interfaces:**
- Produces: `manifest.json` — `{ "sources": { "<dir>": { "license": "CC0"|"CC-BY-4.0"|"CC-BY-3.0", "title": str, "author": str, "url": str, "licenseUrl": str, "files": [str] } } }`. Later tasks resolve `vendor:<dir>/<file>` refs against it; the Task 7 attribution gate cross-references it with NOTICE.md.

- [ ] **Step 1: Write the failing check**

```python
# src-model/tools/check_vendor.py — manifest ↔ disk consistency for vendored assets.
# Run: python3 src-model/tools/check_vendor.py   (exit 1 on any failure)
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, '..', 'vendor')
ALLOWED = {'CC0', 'CC-BY-4.0', 'CC-BY-3.0'}

fails = 0
def check(ok, name):
    global fails
    print(('ok   ' if ok else 'FAIL ') + name)
    if not ok: fails += 1

man = json.load(open(os.path.join(VENDOR, 'manifest.json')))
for src, meta in man['sources'].items():
    d = os.path.join(VENDOR, src)
    check(os.path.isdir(d), f'{src}: directory exists')
    check(os.path.isfile(os.path.join(d, 'RECEIPT.md')), f'{src}: RECEIPT.md present')
    check(meta.get('license') in ALLOWED, f"{src}: license {meta.get('license')} allowed")
    if meta.get('license') != 'CC0':
        check(all(meta.get(k) for k in ('title', 'author', 'url', 'licenseUrl')),
              f'{src}: CC-BY attribution fields complete')
    for f in meta['files']:
        check(os.path.isfile(os.path.join(d, f)), f'{src}/{f}: file present')
        check('mixamo' not in f.lower(), f'{src}/{f}: not a mixamo file')
sys.exit(1 if fails else 0)
```

- [ ] **Step 2: Run it to verify it fails** — `python3 src-model/tools/check_vendor.py` → FileNotFoundError (no manifest.json yet).

- [ ] **Step 3: Un-ignore the vendor tree.** In `.gitignore`, the block currently reads `src-model/*` / `!src-model/tools/` / `src-model/tools/out/`. Add after `!src-model/tools/`:

```
!src-model/vendor/
src-model/vendor/**/*.zip
```

- [ ] **Step 4: Fetch the CC0 sources.** For each, download, extract ONLY the files we consume into `src-model/vendor/<dir>/`, and write `RECEIPT.md` (source URL, today's date, the license label exactly as shown on the page, and how it was fetched). Archives stay out of git (ignored) — delete after extraction.
  - `kaykit-adventurers`: `git clone --depth 1 https://github.com/KayLousberg/KayKit-Adventurers /tmp/kaykit-adv` (official CC0 mirror per the ledger; if the repo name differs, find it via the itch.io page https://kaylousberg.itch.io/kaykit-adventurers). Copy ONE character GLB — prefer the least-armored body (gltf/glb export dir; a Rogue/base adventurer over Knight) — plus the pack's LICENSE file.
  - `kaykit-animations`: same route — KayKit Character Animations (https://kaylousberg.com/game-assets/character-animations, free tier is the full CC0 set; check for a GitHub mirror first). Copy the glTF/GLB containing Idle/Walk/Run clips. If only browser-gated downloads exist, flag the user with the exact URL and the drop path `src-model/vendor/kaykit-animations/`.
  - `kenney-fantasy-town`: fetch https://kenney.nl/assets/fantasy-town-kit, follow the download link in the page HTML (`curl -sL <page> | grep -o 'href="[^"]*\.zip"'`). Extract only the GLB/GLTF `Models` we cast (walls, arched windows/doors, awnings) — the exact subset is chosen in Task 6; for now keep the full model folder locally and commit only after Task 6 prunes it. RECEIPT notes "CC0" from the page.
  - `kenney-city-commercial`: same, from https://kenney.nl/assets/city-kit-commercial (storefronts/awnings/signs subset).
  - `quaternius`: from poly.pizza (per-model label governs — save each page's license line into RECEIPT.md): Can Fridge https://poly.pizza/m/8OHbykvREu, Cat https://poly.pizza/m/2f54vbV0In, Crate https://poly.pizza/m/3OEFd1AWfa, AC unit https://poly.pizza/m/amFuyE3IF6, clay pots https://poly.pizza/m/Olu4b0aiiY, market stall https://poly.pizza/m/PUZZ5F91OE. poly.pizza serves direct GLB downloads via the Download button URL in each page.
  - `kaykit-props`: Crate of Potatoes https://poly.pizza/m/L0Qt7KT6AD (CC0).
  - `ipoly3d`: Wooden Sign https://poly.pizza/m/AsEgIQcQfw (CC0).

- [ ] **Step 5: Write `manifest.json`** listing every source above with its license, url, and the exact files copied. CC0 entries still record `title`/`url` (courtesy + receipts); CC-BY fields complete is only enforced for CC-BY.

- [ ] **Step 6: Run the check to verify it passes** — `python3 src-model/tools/check_vendor.py` → all `ok`, exit 0.

- [ ] **Step 7: Commit** — `git add .gitignore src-model/vendor src-model/tools/check_vendor.py && git commit -m "the street's supply run: cc0 sources vendored with receipts, a manifest, and a gate that reads it"`

---

### Task 2: Sketchfab CC-BY picks — API receipts + account-gated downloads

**Files:**
- Create: `src-model/vendor/sketchfab-arab-house/`, `sketchfab-minaret/`, `sketchfab-tuktuk/`, `sketchfab-fanous/` (+ optional: `sketchfab-scooter/`, `sketchfab-chair/`, `sketchfab-mashrabiya/`) — each: `api.json`, `RECEIPT.md`, model files
- Modify: `src-model/vendor/manifest.json`
- Test: `python3 src-model/tools/check_vendor.py`

**Interfaces:**
- Produces: vendored CC-BY sources consumed by Task 6 casting. UIDs from the ledger: arab-house `a49323aa1e0f450db9ff8b813864379f`, minaret `d8ebe7c756f2414bb70768d936f2d137`, tuktuk `2124df89…`, fanous `ba9aa258…`, scooter `16a3330e…`, chair `898f2dc1…` (short UIDs: resolve the full uid from the model page URL before the API call).

- [ ] **Step 1: Archive license receipts via the public API** (no auth needed): for each pick, `curl -s https://api.sketchfab.com/v3/models/<uid> > src-model/vendor/sketchfab-<name>/api.json`, then assert the slug: `python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['license']['slug']=='by', d['license']; print(d['name'], '—', d['user']['displayName'])" <api.json>`. Any slug ≠ `by` disqualifies that pick — fall back per the ledger (minaret → Minaret V2 by 1shxxn; others → keep procedural).

- [ ] **Step 2: Ask the user for the downloads** (Sketchfab downloads are account-gated — this is the one blocking step). Present the model page URLs (`https://sketchfab.com/3d-models/<slug>-<uid>` from each api.json's `viewerUrl`) and ask for the autoconverted glTF zips dropped anywhere accessible; core picks: arab house, minaret, tuk-tuk, fanous; optional (skip = procedural stays): scooter, chair, mashrabiya, string lights.

- [ ] **Step 3: Extract into vendor dirs**, keep only the glTF/GLB + textures actually needed, write each `RECEIPT.md` (page URL, date, license from api.json, downloader account note), update `manifest.json` with full CC-BY attribution fields (title/author/url/licenseUrl from api.json).

- [ ] **Step 4: Run the gate** — `python3 src-model/tools/check_vendor.py` → pass.

- [ ] **Step 5: Commit** — `git commit -m "the hero pieces arrive with their papers: arab house, minaret, tuk-tuk and fanous, cc-by receipts archived from the api"`

---

### Task 3: `animFor` — pure action selection with hysteresis (TDD)

**Files:**
- Modify: `street-sim.js` (add to `CONST`, new export after `nextMode`)
- Test: `oracle/street.mjs` (append units before the `process.exit` line)

**Interfaces:**
- Produces: `CONST.ANIM = { WALK_IN: 0.25, WALK_OUT: 0.15, RUN_IN: 2.4, RUN_OUT: 2.0 }` (m/s) and `animFor(prev, speed) → 'Idle'|'Walk'|'Run'`. Task 8's runtime calls it every frame with the previous action and `Math.hypot(vel.x, vel.z)`.

- [ ] **Step 1: Write the failing units** — append to `oracle/street.mjs` (before `process.exit`):

```js
// ── animFor: action selection never flickers at a boundary ──
import('../street-sim.js').then(() => {}) // (animFor imported at top with the rest)
check(animFor('Idle', 0) === 'Idle', 'standing still is Idle')
check(animFor('Idle', 0.2) === 'Idle', 'below WALK_IN stays Idle')
check(animFor('Idle', 0.3) === 'Walk', 'past WALK_IN engages Walk')
check(animFor('Walk', 0.2) === 'Walk', 'hysteresis: Walk holds between WALK_OUT and WALK_IN')
check(animFor('Walk', 0.1) === 'Idle', 'below WALK_OUT releases to Idle')
check(animFor('Walk', 2.5) === 'Run', 'past RUN_IN engages Run')
check(animFor('Run', 2.2) === 'Run', 'hysteresis: Run holds between RUN_OUT and RUN_IN')
check(animFor('Run', 1.8) === 'Walk', 'below RUN_OUT releases to Walk')
check(animFor('Idle', CONST.SPEED) === 'Run', 'full pace from rest is Run in one call')
check(animFor('Run', 0) === 'Idle', 'a dead stop from Run is Idle in one call')
```

(Adjust the import at the top of the file: `import { CONST, followK, joyVec, resolveCollision, stepMover, nextMode, animFor } from '../street-sim.js'` — delete the stray `import(...)` line above; it is not needed.)

- [ ] **Step 2: Run to verify it fails** — `node oracle/street.mjs` → SyntaxError/undefined `animFor`.

- [ ] **Step 3: Implement** — in `street-sim.js`, add to `CONST`: `ANIM: { WALK_IN: 0.25, WALK_OUT: 0.15, RUN_IN: 2.4, RUN_OUT: 2.0 },` and after `nextMode`:

```js
// Speed (m/s) → animation action, with hysteresis bands at both boundaries
// so the mixer never flickers when the runner hovers at a threshold.
export function animFor(prev, speed) {
  const A = CONST.ANIM;
  if (speed >= A.RUN_IN) return 'Run';
  if (prev === 'Run' && speed >= A.RUN_OUT) return 'Run';
  if (speed >= A.WALK_IN) return 'Walk';
  if (prev !== 'Idle' && speed >= A.WALK_OUT) return 'Walk';
  return 'Idle';
}
```

- [ ] **Step 4: Run to verify it passes** — `node oracle/street.mjs` → all `ok`, exit 0.

- [ ] **Step 5: Commit** — `git commit -m "the runner learns its gaits on paper first: animFor with hysteresis at both thresholds, oracle-gated"`

---

### Task 4: `build_runner.py` — the KayKit character becomes the brand runner

**Files:**
- Create: `src-model/tools/build_runner.py`
- Output: `assets/street/runner.glb`
- Test: inline GLB JSON-chunk check (below) + `blender -b -P src-model/tools/build_runner.py` exits 0

**Interfaces:**
- Consumes: `src-model/vendor/kaykit-adventurers/<character>.glb`, `src-model/vendor/kaykit-animations/<clips>.glb` (exact filenames from Task 1 — resolve via `manifest.json` `files`).
- Produces: `assets/street/runner.glb` — one skinned mesh, materials exactly `runnerPaper`/`runnerInk`/`runnerAccent`, animations exactly `Idle`/`Walk`/`Run`, in-place (root XZ zeroed), height ≈ 1.75m, +Y up. Task 8 loads it by this contract.

- [ ] **Step 1: Write the script.** Follow `build_street.py`'s idiom (same header comment style, `HERE`/`ROOT` paths). Skeleton:

```python
# build_runner.py — the KayKit adventurer becomes the TEMPO runner.
# Run: blender -b -P src-model/tools/build_runner.py
# Imports the vendored character + animation clips, strips the fantasy gear,
# re-tints to the brand (paper body / ink head / accent band), bakes the
# clips in place (the sim owns position) and exports assets/street/runner.glb.
import bpy, json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')
OUT = os.path.join(ROOT, 'assets', 'street', 'runner.glb')
MAN = json.load(open(os.path.join(VENDOR, 'manifest.json')))

GEAR = re.compile(r'sword|shield|axe|bow|staff|dagger|bag|hat|helmet|armor|cape|quiver|potion|mug|barbarian|knight_extra', re.I)
PALETTE = {'runnerPaper': (0.93, 0.90, 0.84, 1), 'runnerInk': (0.10, 0.09, 0.08, 1), 'runnerAccent': (1.0, 0.478, 0.102, 1)}
```

Then, in order: `read_factory_settings(use_empty=True)`; import the character GLB; delete every mesh object whose name matches `GEAR` (print what was kept/deleted — the executor eyeballs this list against the actual pack names and tightens the regex if a sword survives); import the animations GLB; copy its actions onto the character's armature (KayKit animations target the same rig — verify identical bone names, `set(a.data.bones.keys())`, and abort loudly if not); keep only the three actions whose names match `idle|walk|run` (case-insensitive, e.g. `Walking_A` → pick the plain locomotion variants), rename them exactly `Idle`, `Walk`, `Run`, and push each onto the armature via `action.use_fake_user = True` so the exporter keeps all three.

- [ ] **Step 2: In-place bake.** For each kept action, inspect the root/hips bone's location F-curves: if XZ displacement over the clip exceeds 0.01m, zero those curves (`for fc in act.fcurves: if fc.data_path.endswith('.location') and fc.array_index in (0, 1): act.fcurves.remove(fc)` — array indices per the armature's axis convention; verify by re-checking displacement after removal). Print before/after displacement.

- [ ] **Step 3: Re-tint.** Replace every remaining material with the three flat ones (build them like `build_street.py`'s `mat()` — Principled Base Color + Roughness 0.9 + `diffuse_color` set). Slot mapping by original material name: skin/body → `runnerPaper`, hair/head/eye → `runnerInk`, cloth/belt/trim → `runnerAccent`, anything else → `runnerPaper`. Print the mapping. Normalize height: uniform-scale the armature so the mesh bbox height is 1.75m, apply transforms.

- [ ] **Step 4: Export** — draco GLB with animations:

```python
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_yup=True,
    export_animations=True, export_draco_mesh_compression_enable=True)
print('[runner] glb bytes:', os.path.getsize(OUT))
```

(Same try/except draco fallback as `build_street.py`'s `export_glb`.)

- [ ] **Step 5: Run + machine-check the contract.** `blender -b -P src-model/tools/build_runner.py`, then parse the GLB's JSON chunk with plain python (draco leaves it readable):

```python
python3 - <<'EOF'
import json, struct
raw = open('assets/street/runner.glb', 'rb').read()
assert raw[:4] == b'glTF'
ln = struct.unpack('<I', raw[16:20])[0]
doc = json.loads(raw[20:20 + ln])
anims = sorted(a['name'] for a in doc.get('animations', []))
mats = sorted(m['name'] for m in doc.get('materials', []))
assert anims == ['Idle', 'Run', 'Walk'], anims
assert set(mats) <= {'runnerPaper', 'runnerInk', 'runnerAccent'}, mats
assert len(raw) < 1_500_000, len(raw)
print('runner contract ok:', anims, mats, len(raw), 'bytes')
EOF
```

Expected: `runner contract ok: …`. (This check graduates into `verify_street_glb.py` in Task 7.)

- [ ] **Step 6: Eyeball render.** Reuse the poster idiom: a quick Workbench still of the runner (front + ¾) to `src-model/tools/out/runner_check.png` — confirm gear gone, tint mapping right, no T-pose distortion. Read the image.

- [ ] **Step 7: Commit** — `git add src-model/tools/build_runner.py assets/street/runner.glb && git commit -m "the runner steps out of the asset pack: kaykit body in tempo paper and ink, three gaits baked in place"`

---

### Task 5: Vendor import machinery in `build_street.py` + first vendored prop (the Can Fridge)

**Files:**
- Modify: `src-model/tools/build_street.py` (new helpers after `join()`, ~line 89; new build fn before `export_glb`)
- Modify: `src-model/tools/street_layout.json` (new top-level `vendorProps` array; one new collider)
- Test: `blender -b -P src-model/tools/build_street.py` + GLB JSON-chunk check + `node oracle/street.mjs`

**Interfaces:**
- Produces: layout schema `vendorProps: [{ "name": str, "ref": "vendor:<dir>/<file>", "x": n, "y": n, "z": n, "ry": n, "height": n, "tints": { "<origMatPrefix>"|"*": "<palette key>" }, "tris": n }]` and helpers `import_vendor(ref) -> [objects]`, `palette_strip(objs, tints)`, `normalize_height(objs, name, height) -> obj` (joins, renames, returns one), `decimate_to(obj, tris)`. Task 6 casts everything through these.

- [ ] **Step 1: Add the helpers.** In `build_street.py`:

```python
VENDOR = os.path.join(ROOT, 'src-model', 'vendor')

def import_vendor(ref):
    # ref: "vendor:<dir>/<relpath>" — resolves under src-model/vendor/
    path = os.path.join(VENDOR, ref.split(':', 1)[1])
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in ('.glb', '.gltf'): bpy.ops.import_scene.gltf(filepath=path)
    elif ext == '.fbx': bpy.ops.import_scene.fbx(filepath=path)
    elif ext == '.obj': bpy.ops.wm.obj_import(filepath=path)
    else: raise ValueError('unsupported vendor format: ' + path)
    new = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
    for o in set(bpy.data.objects) - before:      # imported empties/armatures: flatten
        if o.type != 'MESH':
            for c in list(o.children): c.parent = None
            bpy.data.objects.remove(o)
    return new

def palette_strip(objs, tints):
    # every source material dies here; the palette is the only survivor
    for o in objs:
        names = [s.material.name.split('.')[0] if s.material else '' for s in o.material_slots]
        o.data.materials.clear()
        keys = [next((v for k, v in tints.items() if k != '*' and k.lower() in n.lower()),
                     tints.get('*', 'paper')) for n in names] or [tints.get('*', 'paper')]
        for key in keys: o.data.materials.append(mat(key))
        if len(keys) > 1:   # faces keep their slot index; reindex clamp
            for p in o.data.polygons: p.material_index = min(p.material_index, len(keys) - 1)

def normalize_height(objs, name, height):
    obj = join(objs, name) if len(objs) > 1 else objs[0]
    obj.name = name
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    lo = min((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    hi = max((obj.matrix_world @ v.co).z for v in obj.data.vertices)
    s = height / max(1e-6, hi - lo)
    obj.scale = (s, s, s)
    bpy.ops.object.transform_apply(scale=True)
    obj.location.z -= min((obj.matrix_world @ v.co).z for v in obj.data.vertices)  # feet on the ground
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
        objs = import_vendor(vp['ref'])
        palette_strip(objs, vp.get('tints', {'*': 'paper'}))
        obj = normalize_height(objs, vp['name'], vp['height'])
        decimate_to(obj, vp.get('tris', 3000))
        obj.location = P(vp['x'], vp.get('y', 0), vp['z'])
        obj.rotation_euler = (obj.rotation_euler.x, obj.rotation_euler.y, vp.get('ry', 0))
        print('[street] vendor prop', vp['name'],
              sum(len(p.vertices) - 2 for p in obj.data.polygons), 'tris')
```

Note on `normalize_height`: the world is modeled in Blender Z-up via `P()`, so height is measured on Blender-Z. `location.z` adjustment grounds the feet at site y=0; `vp['y']` then offsets via `P()`. Executor: verify one prop visually before trusting the math (Step 4).

- [ ] **Step 2: Register + cast the fridge.** Add `build_vendor_props()` to the build sequence after `build_props()`. In `street_layout.json` add:

```json
"vendorProps": [
  { "name": "canFridge", "ref": "vendor:quaternius/CanFridge.glb",
    "x": 9.55, "z": -1.05, "ry": 2.62, "height": 1.9,
    "tints": { "glass": "paper", "*": "metal" }, "tris": 2800 }
]
```

(Exact filename from `manifest.json`; position = beside the koshk's right flank, facing the street — nudge against the poster render in Step 4.) Add its collider to `colliders`: `{ "x": [9.2, 9.9], "z": [-1.4, -0.7] }` — adjust to the placed footprint.

- [ ] **Step 3: Run the sim gates first** — `node oracle/street.mjs` → the existing "spawn is clear" / "trigger standable" checks must still pass with the new collider (they read layout.json directly). If the trigger check fails, the fridge collider overlaps the trigger spot — move the fridge, not the trigger.

- [ ] **Step 4: Rebuild + verify** — `blender -b -P src-model/tools/build_street.py`, then: GLB JSON-chunk check (same struct/json parse as Task 4 Step 5, against `assets/street/street.glb`): material names all ∈ `PALETTE ∪ EMISSIVE` keys, a node named `canFridge` exists, bytes < 4,000,000. Convert + read `out/street_poster.png` — the fridge stands beside the koshk, tinted metal/paper, feet on the ground, right size against the counter.

- [ ] **Step 5: Commit** — `git commit -m "the pipeline learns to borrow: vendor import, palette strip, normalize and decimate — and the ahwa can fridge proves it"`

---

### Task 6: Full casting — facades, minaret, koshk dressing, props table, signage, poster

**Files:**
- Modify: `src-model/tools/street_layout.json` (vendorProps entries, building `ref`s, colliders)
- Modify: `src-model/tools/build_street.py` (`build_buildings` vendor branch, `build_minaret` swap, signage textures)
- Create: `src-model/tools/gen_signs.py` (baked Arabic sign textures)
- Modify: `src-model/vendor/` (prune Kenney kits to the consumed subset; update manifest `files`)
- Test: rebuild + GLB gates + `node oracle/street.mjs` + poster eyeball

**Interfaces:**
- Consumes: Task 5 helpers, Task 1/2 vendor files.
- Produces: the final cast `street.glb` + `assets/street/poster.webp`. Building schema gains optional `"ref"` + `"tints"` + `"tris"` — with `ref`, `build_buildings` imports instead of boxing (parapet/windows skipped; the asset brings its own detail).

- [ ] **Step 1: Hero facade.** `buildings[1]` (`b2`, the rose center) gains `"ref": "vendor:sketchfab-arab-house/scene.gltf"`, `"tints": {"*": "plasterRose", "wood": "wood", "dark": "shutter"}`, `"tris": 9000`. In `build_buildings`, branch: if `ref`, `import_vendor` → `palette_strip` → `normalize_height(objs, 'bld_' + name, h)` → `decimate_to` → scale X/footprint to `(x1 - x0)` width (non-uniform X scale after height normalize is fine for a facade) → position at the building's center. Colliders unchanged (same AABBs).
- [ ] **Step 2: Kenney flanks.** `b1`/`b3` get refs to chosen Fantasy Town / City Kit Commercial facade pieces (executor lists the extracted models, picks wall+window+awning segments, tiles them across the building width — a small `tile_facade` loop placing segment instances every segment-width). Tints: plasterSand/plasterOchre + shutter accents. If tiling reads worse than the procedural boxes in the poster, keep procedural for flanks (record the call in the commit message) — the hero facade carries the upgrade.
- [ ] **Step 3: Minaret.** `build_minaret` → vendor branch: import `sketchfab-minaret`, tint `plasterSand`, `decimate_to` 6000, normalize to `mn.h`, place at `(mn.x, mn.z)`. The spiral silhouette against the sky is the whole point — check the poster.
- [ ] **Step 4: Koshk dressing + props table.** vendorProps entries (positions start from the current procedural anchors in `props`; colliders only for the tuk-tuk and anything ≥0.5m footprint): cat (Quaternius, replaces `build_props` procedural cat — delete that block; static: apply the armature at rest pose on import, tint `ink`, on its crate), tuk-tuk (parked on the left curb ~`x -8.5, z 3.2`, tints awningA/ink/metal, collider), fanous (hung from the first string-light span mid-point, tint `sign` emissive? No — fanous glass reads via `bulb` emissive, body `metal`), ahwa chair ×2 + Kenney round table (near the left sidewalk, `wood`/`woodLight`), scooter (leaning by b3, `metal`/`ink`, only if downloaded), clay pots + market stall (koshk flank), Crate of Potatoes (on the crate stack). AC unit: replace the procedural `ac` box in `build_buildings` with the Quaternius unit only if it survives palette_strip cleanly at ≤400 tris; else keep the box.
- [ ] **Step 5: Signage.** `gen_signs.py`: PIL renders Arabic shop lettering — `pip install arabic-reshaper python-bidi` + a vendored OFL Arabic font (Amiri from https://github.com/aliftype/amiri/releases, vendor dir `amiri-font` with RECEIPT + manifest entry, license `OFL` — extend `check_vendor.py` ALLOWED with `'OFL'`). Text: `مشروبات باردة` ("cold drinks") + `كشك` — reshape → bidi → draw ink-on-paper PNG 512×128 into `src-model/tools/out/signs/`. `build_street.py` maps them onto the iPoly3D wooden sign (vendorProp near the koshk) and the koshk signboard face via a textured material (image texture node + `diffuse_color` mean color for Workbench).
- [ ] **Step 6: Mashrabiya decision.** Import `sketchfab-mashrabiya` (if downloaded), decimate to 3000, render a closeup: lattice holes must still read as a lattice. Muddy → keep procedural (default; delete the vendor dir and manifest entry if unused). String lights: default keep procedural catenaries (they're palette-perfect already); only swap if a Kenney kit piece genuinely reads better.
- [ ] **Step 7: Prune + receipts.** Delete unconsumed vendor files (Kenney kits especially — keep only cast pieces), update `manifest.json` `files`, `python3 src-model/tools/check_vendor.py` green.
- [ ] **Step 8: Full rebuild + gates.** `blender -b -P src-model/tools/build_street.py`; GLB JSON-chunk check: palette-only materials, all vendorProp node names present, bytes < 4,000,000; `node oracle/street.mjs` all green (standable checks against final colliders). Poster: convert `out/street_poster.png` → `assets/street/poster.webp` via Pillow (`python3 -c "from PIL import Image; Image.open('src-model/tools/out/street_poster.png').save('assets/street/poster.webp', quality=82)"`), assert ≤150KB, and READ it — golden hour, palette-locked, minaret silhouette, no floating/clipping props.
- [ ] **Step 9: Commit** — `git commit -m "the street gets its cast: arab house and spiral minaret, a parked tuk-tuk, fanous light, ahwa corner and arabic signs — all in tempo paper and ink"`

---

### Task 7: Machine gates — `verify_street_glb.py`, attribution gate, NOTICE.md

**Files:**
- Create: `src-model/tools/verify_street_glb.py` (Blender script, `verify_glb.py` idiom)
- Create: `src-model/tools/check_attribution.py`
- Modify: `NOTICE.md` (Cairo street section)
- Test: both scripts exit 0; attribution gate FAILS first (before NOTICE.md is written), then passes

**Interfaces:**
- Consumes: `assets/street/street.glb`, `runner.glb`, `poster.webp`, `street_layout.json`, `manifest.json`.
- Produces: the pre-ship gate pair Task 9 runs. `check_attribution.py` exits 1 for any CC-BY manifest source referenced by a layout `ref` that lacks a NOTICE.md line containing its title AND author AND url.

- [ ] **Step 1: Write `verify_street_glb.py`** — `blender -b -P`, imports both GLBs into an empty scene (draco decodes on import), `check()`/exit idiom copied from `verify_glb.py:15-17`. Gates: total bytes (street.glb + runner.glb + poster.webp) ≤ 5,242,880; street tris (`sum(len(p.vertices)-2 ...)` across street objects) ≤ 120,000; runner action names == {Idle, Walk, Run}; every material's name ∈ `PALETTE ∪ EMISSIVE ∪ {runnerPaper, runnerInk, runnerAccent} ∪ {sign textures}` (import the dicts by parsing build_street.py? No — duplicate the allowed-name SET as a literal with a comment pointing at build_street.py; the palette changes rarely and the gate failing loudly on drift is the point); poster.webp ≤ 153,600 bytes; runner height 1.6–1.9m.
- [ ] **Step 2: Write `check_attribution.py`** — plain python: load manifest + layout; collect every `vendor:<dir>/…` ref (vendorProps + buildings); for each dir with license startswith `CC-BY`: assert NOTICE.md contains `meta['title']`, `meta['author']`, `meta['url']`. Print per-source ok/FAIL, exit accordingly. Run it now → expected: FAIL for every CC-BY source (NOTICE not yet written).
- [ ] **Step 3: Write the NOTICE.md section** — after the Splash entry, `## Cairo street (section 05)` block: one entry per CC-BY asset with title (linked to source URL), author (linked), CC-BY license link, and modifications ("palette re-tint, decimation, kitbash placement, draco recompression"); a courtesy line for CC0 sources (KayKit, Kenney, Quaternius, iPoly3D — no logo use); Amiri font under OFL.
- [ ] **Step 4: Run both gates** — `blender -b -P src-model/tools/verify_street_glb.py` and `python3 src-model/tools/check_attribution.py` → exit 0.
- [ ] **Step 5: Commit** — `git commit -m "the gates before the gate: wire and tri budgets, palette lock, clip names, and attribution that fails the build when a credit is missing"`

---

### Task 8: Runtime — the animated runner, portal rewired, battery extended

**Files:**
- Modify: `street.js` (runner block `171-183`, fetch block `96-100`, anim in the rAF loop `283-286`, dispose `311-324`, `state` line 18)
- Modify: `index.html` (restore the portal block + script tag — exact markup in the f35acf2 diff, reproduced below)
- Modify: `oracle/verify-street.py` (anim checks after the walk block, line ~89)
- Test: `node oracle/street.mjs`, then `python3 -m http.server 8000 &` + `TMPDIR=$HOME/tmp python3 oracle/verify-street.py`, `python3 oracle/verify-intro.py`

**Interfaces:**
- Consumes: `runner.glb` contract (Task 4), `animFor` (Task 3).
- Produces: `TempoStreet.state.anim` ∈ {Idle, Walk, Run} for the battery.

- [ ] **Step 1: Restore the portal** in `index.html` — replace the two deploy-held comment lines (at the egyptMap slot) with:

```html
<div class="street-portal reveal" id="streetPortal">
  <img class="street-portal__poster" src="assets/street/poster.webp" alt="A little Cairo street corner with a koshk" loading="lazy" />
  <div class="street-portal__meta">
    <h3>Or walk there yourself</h3>
    <p>A little Cairo corner — find the koshk, browse the shelf, take a flavor home.</p>
    <button class="btn btn--solid" id="streetEnter" type="button">Step into the street</button>
  </div>
</div>
```

and re-add `<script type="module" src="street.js?v=2"></script>` after the can3d.js tag (v=2 — the module changed).

- [ ] **Step 2: Swap the runner.** In `street.js`: import `animFor` from `./street-sim.js`; add `'assets/street/runner.glb?v=1'` to the `Promise.all` (draco loadGlb; destructure becomes `const [layout, streetGlb, canGlb, runnerGlb] = await Promise.all([...])`; bump street.glb/layout.json to `?v=2`); replace lines 171–183 with:

```js
// the runner — the KayKit body in TEMPO paper and ink, three gaits
const runner = runnerGlb.scene;
scene.add(runner);
const mixer = new THREE.AnimationMixer(runner);
const actions = {};
for (const clip of runnerGlb.animations) actions[clip.name] = mixer.clipAction(clip);
actions.Idle.play();
state.anim = 'Idle';
```

- [ ] **Step 3: Drive it.** Replace the bob block (lines 283–286) with:

```js
const speed = Math.hypot(vel.x, vel.z);
runner.position.set(pos.x, 0, pos.z);
if (speed > 0.3) runner.rotation.y = Math.atan2(vel.x, vel.z);
const want = animFor(state.anim, speed);
if (want !== state.anim) {
  actions[state.anim].fadeOut(0.2);
  actions[want].reset().fadeIn(0.2).play();
  state.anim = want;
}
// tie the stride to the ground speed so feet don't slide
if (want !== 'Idle') actions[want].timeScale = Math.max(0.6, Math.min(1.6, speed / (want === 'Run' ? 3.4 : 1.4)));
mixer.update(dt / 1000);
```

Dispose additions (inside the cleanup pushed at line 311): `mixer.stopAllAction(); mixer.uncacheRoot(runner);` before the traverse (the traverse already disposes skinned geometry/materials); `phase` variable and its line die.

- [ ] **Step 4: Extend the battery.** In `verify-street.py`, inside the walk block (while `KeyW` is down, after the `pmid` sample): `check(page.evaluate("() => ['Walk','Run'].includes(window.TempoStreet.state.anim)"), 'the runner strides while W is held')`; after `keyboard.up` + the `p1` sample: `check(wait_for(page, \"() => window.TempoStreet.state.anim === 'Idle'\", 4000), 'the runner settles to Idle at rest')`.
- [ ] **Step 5: Run everything** — `node oracle/street.mjs`; serve + `TMPDIR=$HOME/tmp python3 oracle/verify-street.py` (portal now wired: the full 22+2 checks run, no skip); `python3 oracle/verify-intro.py` (shared files touched). All green. If a projected-click check gets flaky, re-read the camera-settle rule — poll `state.camDist`, never add sleeps.
- [ ] **Step 6: Commit** — `git commit -m "the street un-docks and the runner earns its name: real strides from the kaykit clips, idle to run and back, battery riding along"`

---

### Task 9: Ship

**Files:**
- Modify: `README.md` (file table: `assets/street/` line gains runner.glb + vendored provenance pointer; `src-model/` line mentions vendor/)
- Modify: `dist/` (sync)
- Test: full gate suite + served-bytes md5

- [ ] **Step 1: Full gate suite, in order** — `python3 src-model/tools/check_vendor.py` && `python3 src-model/tools/check_attribution.py` && `blender -b -P src-model/tools/verify_street_glb.py` && `node oracle/street.mjs` && verify-street + verify-intro (as Task 8 Step 5). Every one green — no partial ship.
- [ ] **Step 2: Sync dist** — `cp index.html street.js street-sim.js NOTICE.md README.md dist/ && mkdir -p dist/assets/street && cp assets/street/* dist/assets/street/`. Diff-check nothing else drifted: `diff -rq dist . --exclude=... ` scoped to the site files (the README's "dist mirrors the site files" contract).
- [ ] **Step 3: Deploy** — `thebes-deploy deploy --skip-install --no-facts` (pinned cids stay). Standing push-live order covers this; the deploy-hold was lifted by the user for this pass ("ship when green", 2026-09-06).
- [ ] **Step 4: Verify served bytes** — `curl -s https://memphis.mercaturaforum.com/... | md5sum` vs local dist md5 for index.html, street.js, street.glb, runner.glb, poster.webp. Open the live site headless: portal present, enter works (one smoke pass of verify-street.py against the live URL if practical).
- [ ] **Step 5: Update memory + brain** — rewrite the tempo-cairo-street-project memory: DEPLOY-HELD → LIVE (date, commit), runner/asset upgrade noted, polish backlog trimmed of what shipped.
- [ ] **Step 6: Commit** — `git commit -m "section 05 opens to the street: the cast is licensed, the gates are green, the koshk is live"`

---

## Deviation from spec (recorded)

Two deliberate deviations:

1. The spec placed the GLB gates in `verify_glb.py`; that file is the CAN's verifier (hardcoded to `out/tempo-can.glb`, can-specific polycounts). The street gates get their own `verify_street_glb.py` instead — same idiom, clean boundary.
2. The spec put the portal rewire in the ship step; the plan does it in Task 8, because `verify-street.py` self-skips while the portal is unwired — the battery can only prove the runtime with the portal live in the local tree. Deploy itself stays in Task 9.

Everything else implements the spec as written.

