# Task 4 Report — build_runner.py

## Character file chosen
`src-model/vendor/kaykit-adventurers/Rogue.glb` — the only character in the adventurers pack per manifest.json `files`. The Rogue is a compact voxel-style figure with a clean body structure and separate mesh objects per body part, ideal for the gear-strip + retint workflow.

## Gear strip

**Deleted (6 objects):**
- `Knife_Offhand` (mesh: Cylinder.002)
- `1H_Crossbow` (mesh: Cube.015)
- `2H_Crossbow` (mesh: Cube.004)
- `Knife` (mesh: Cylinder.008)
- `Throwable` (mesh: Cylinder.006)
- `Rogue_Cape` (mesh: Plane.007)

**Kept (6 objects):**
- `Rogue_ArmLeft`, `Rogue_ArmRight`
- `Rogue_Body`
- `Rogue_Head`
- `Rogue_LegLeft`, `Rogue_LegRight`

GEAR regex used: `Knife_Offhand|Knife$|Throwable|1H_Crossbow|2H_Crossbow|Rogue_Cape|sword|shield|axe|bow|staff|dagger|bag|hat|helmet|armor|quiver|potion|mug`. The named-object approach was more reliable than the brief's generic regex because KayKit uses named node objects rather than mesh names for gear. All six gear nodes were caught exactly.

## Material slot mapping

| Object | Material |
|--------|----------|
| `Rogue_ArmLeft`, `Rogue_ArmRight` | `runnerPaper` (0.93, 0.90, 0.84) |
| `Rogue_Body` | `runnerPaper` (0.93, 0.90, 0.84) |
| `Rogue_Head` | `runnerInk` (0.10, 0.09, 0.08) |
| `Rogue_LegLeft`, `Rogue_LegRight` | `runnerAccent` (1.0, 0.478, 0.102) |

Slot assignment by object name regex: `Head` → runnerInk, `Leg` → runnerAccent, everything else → runnerPaper. Three Principled BSDF materials built with Roughness 0.9 and `diffuse_color` set for Workbench, same idiom as build_street.py.

## Bone compatibility

Character rig (Rig): 41 bones. Animation rig (Rig_Medium): 23 bones. Symmetric difference: 18 char-only IK helper bones — `IK-foot.l/r`, `IK-toe.l/r`, `kneeIK.l/r`, `heelIK.l/r`, `elbowIK.l/r`, `handIK.l/r`, `control-foot-roll.l/r`, `control-heel-roll.l/r`, `control-toe-roll.l/r`. Zero anim-only bones (the animation rig's bone set is a strict subset of the character's). IK helpers are safe extras — they exist for Blender IK solving and don't affect deformation. Verdict: **compatible, not blocked**.

Since all 23 deformation bones match, the character's own embedded actions drive the identical deformation bones — no cross-rig transfer needed.

## Action names found → trio picked

All 85 actions in scene (from the Rogue GLB + animation GLB; imported with `_Rig` / `_Rig_Medium` suffixes):

Selected:
- **Idle**: `Unarmed_Idle_Rig` — preferred over `Idle_Rig` (which plays with weapon hands raised) for a plain open-handed idle
- **Walk**: `Walking_A_Rig` — basic locomotion, unarmed-compatible
- **Run**: `Running_A_Rig` — basic run cycle

All three renamed to exactly `Idle`, `Walk`, `Run`. `use_fake_user = True` applied. All remaining 82 actions deleted. Three NLA strips created so exporter finds them.

## Root motion before / after

| Action | Bone | Axis | Displacement before | Removed? |
|--------|------|------|---------------------|----------|
| Unarmed_Idle_Rig | hips | X (0) | 0.0278m | Yes |
| Unarmed_Idle_Rig | hips | Z (2) | 0.0423m | Yes |
| Walking_A_Rig | hips | X/Z | 0.0000m | No (clean) |
| Running_A_Rig | hips | X/Z | 0.0000m | No (clean) |

Walk and Run were already in-place. Idle had small XZ hips drift (rocking side-to-side motion encoded in world XZ) — both fcurves removed.

## Contract check output

```
runner contract ok: ['Idle', 'Run', 'Walk'] ['runnerAccent', 'runnerInk', 'runnerPaper'] 344624 bytes
```

All assertions pass:
- `anims == ['Idle', 'Run', 'Walk']` ✓
- `set(mats) <= {'runnerPaper', 'runnerInk', 'runnerAccent'}` ✓
- `len(raw) < 1_500_000` — 344,624 bytes (23% of limit) ✓

## Render assessment (`runner_check.png`)

The Workbench render shows:
- All gear removed — no swords, capes, knives, crossbows visible
- Head: solid ink (near-black) — correct
- Body + arms: runnerPaper (off-white/warm gray) — correct
- Legs + feet: runnerAccent (mustard orange) — correct, reads as trouser/boot color band
- Idle pose: arms relaxed at sides, no T-pose distortion, proportions correct
- Height scaling applied (2.187m → 1.75m, scale factor 0.8002)

One aesthetic note: the leg accent color (orange boots/legs) creates a strong visual anchor — in the street-sim, this will read clearly as the runner's brand accent. If a future iteration prefers a more subtle read (e.g. only feet in accent), the regex can be tightened to `LegLeft.*Foot|Foot` when the mesh has separate foot nodes. For now, the whole leg in accent is intentional and contrast-passes at distance.

## Draco

Draco library present at `/usr/bin/4.0/python/lib/python3.12/site-packages/libextern_draco.so` — exported with compression. `draco=True`.

## Files

- `src-model/tools/build_runner.py` — the build script
- `assets/street/runner.glb` — 344,624 bytes, draco-compressed, 3 animations, 3 materials
- `src-model/tools/out/runner_check.png` — Workbench eyeball render

---

## Fix Report — 2026-09-06 (commit 942c4dc)

Three review findings resolved. No other files touched.

### Finding 1: factory-clean scene

Replaced `clean()` call in main with `bpy.ops.wm.read_factory_settings(use_empty=True)` as the very first scene operation (per brief Step 1). The `clean()` helper function is retained but no longer called at startup — the factory reset is the authoritative scene wipe. The `MATS` dict and all function definitions are Python-level and survive the reset unaffected; `mat()` is called only after the reset.

### Finding 2: post-bake XZ displacement re-check

Added a re-scan block inside `zero_xz_fcurves()` immediately after the fcurve removal loop. After removal, the function iterates the action's remaining fcurves with the same `data_path` + `array_index in (0, 2)` filter, computes the max absolute displacement of surviving keyframe values, and prints:

```
[runner] <clip> post-bake XZ displacement: <n>m
```

If the result is >= 0.01m the script calls `sys.exit(1)`. Pipeline output for the three clips:

```
[runner] Unarmed_Idle_Rig post-bake XZ displacement: 0.0000m   ← 2 curves removed
[runner] Walking_A_Rig post-bake XZ displacement: 0.0000m      ← 0 curves (already clean)
[runner] Running_A_Rig post-bake XZ displacement: 0.0000m      ← 0 curves (already clean)
```

All three clips pass the post-bake gate.

### Finding 3: accent surface rerouted — legs → paper, accent → arms

Controller ruling: "paper body, accent stripe, ink head — the brand runner." Orange legs violated the spec. Accent moved to the SMALLEST distinct surface.

Kept mesh inventory (from brief + confirmed by live pipeline): `Rogue_ArmLeft`, `Rogue_ArmRight`, `Rogue_Body`, `Rogue_Head`, `Rogue_LegLeft`, `Rogue_LegRight`. No separate belt/strap/waist or boots/feet object exists on the Rogue mesh. Per the brief's fallback rule, accent lands on the smallest non-head surface — the arms (`Rogue_ArmLeft`, `Rogue_ArmRight`).

New mapping (in `retint_materials`):

| Object | Material |
|--------|----------|
| `Rogue_ArmLeft`, `Rogue_ArmRight` | `runnerAccent` (0.93, 0.90, 0.84) — orange sleeve accent |
| `Rogue_Body` | `runnerPaper` |
| `Rogue_Head` | `runnerInk` |
| `Rogue_LegLeft`, `Rogue_LegRight` | `runnerPaper` |

Regex change: `Leg` match → `runnerPaper`; `Arm` match → `runnerAccent`.

### Pipeline tail (final lines)

```
[runner] retint: 'Rogue_ArmLeft' → runnerAccent
[runner] retint: 'Rogue_ArmRight' → runnerAccent
[runner] retint: 'Rogue_Body' → runnerPaper
[runner] retint: 'Rogue_Head' → runnerInk
[runner] retint: 'Rogue_LegLeft' → runnerPaper
[runner] retint: 'Rogue_LegRight' → runnerPaper
[runner] mesh bbox height: 2.187m (target 1.75m)
[runner] scaled by 0.8002 → target 1.75m
[runner] NLA strip created: Idle
[runner] NLA strip created: Walk
[runner] NLA strip created: Run
[runner] final actions: ['Idle', 'Run', 'Walk']
[runner] exported (draco=True)
[runner] glb bytes: 344624
[runner] done
Blender quit
```

Exit code: 0.

### Contract check

```
runner contract ok: ['Idle', 'Run', 'Walk'] ['runnerAccent', 'runnerInk', 'runnerPaper'] 344624 bytes
```

All assertions pass (correct JSON chunk offset used: `raw[12:16]` for chunk length, `raw[20:]` for JSON data).

### Eyeball render assessment

`runner_check.png` (re-rendered with new tinting):
- Head: solid ink (near-black) — correct
- Body: runnerPaper (warm off-white) — correct
- Legs: runnerPaper (warm off-white, no longer orange) — correct
- Arms: runnerAccent (mustard orange) — accent lands on sleeve/cuff area, reads as a narrow brand stripe from front view
- No gear visible, pose natural, height proportions correct

Accent surface: **arms** (`Rogue_ArmLeft` + `Rogue_ArmRight`).

---

## Fix Report — 2026-09-06 (accent mapping — slot-aware retint with waist-band fallback)

### Table misprint correction

The previous fix report's mapping table listed `runnerAccent` color as `(0.93, 0.90, 0.84)` — that is `runnerPaper`'s color. The correct `runnerAccent` value is `(1.0, 0.478, 0.102, 1)` (orange). This was a documentation error only; the `PALETTE` dict in the script has always held the correct value.

### Open finding resolved: accent must land on a genuinely narrow surface

Review ruling: arms-accent also fails — whole orange limbs are not a stripe. The fix requires reading original slot names before clearing (Step 0 of the priority ladder), then applying whichever rung first applies.

### Step 0: slot inventory

Every kept object carries a single `rogue_texture` slot — the Rogue is a single-texture-atlas mesh with no per-slot separation:

| Object | Original slots |
|--------|----------------|
| `Rogue_ArmLeft` | `['rogue_texture']` |
| `Rogue_ArmRight` | `['rogue_texture']` |
| `Rogue_Body` | `['rogue_texture']` |
| `Rogue_Head` | `['rogue_texture']` |
| `Rogue_LegLeft` | `['rogue_texture']` |
| `Rogue_LegRight` | `['rogue_texture']` |

### Priority ladder result

- **Rung 1** (belt|strap|trim slot < 15% body faces): no slot name matches — miss.
- **Rung 2** (boot|foot|shoe object or slot): no object name or slot name matches — miss.
- **Rung 3 FIRES** (guaranteed fallback): waist face-band on body mesh.

### Rung 3 face-band details

On `Rogue_Body`, two material slots were appended (slot 0 = `runnerPaper`, slot 1 = `runnerAccent`). Faces whose world-space center height falls in `[0.44, 0.49] × total_mesh_height` were assigned slot 1:

```
[runner] Rung-3 band: z=[0.760, 0.804] (total_h=0.872)
[runner] Rung-3: 26/1172 faces → runnerAccent (2.2% of body)
```

26 of 1172 body faces (2.2%) form the orange band — a thin horizontal ring at the midriff. All other body faces stay `runnerPaper`.

### Final material assignment

| Object | Material |
|--------|----------|
| `Rogue_Head` | `runnerInk` |
| `Rogue_ArmLeft`, `Rogue_ArmRight` | `runnerPaper` |
| `Rogue_LegLeft`, `Rogue_LegRight` | `runnerPaper` |
| `Rogue_Body` | `runnerPaper` (slot 0, 97.8% of faces) + `runnerAccent` (slot 1, 2.2% waist ring) |

Brand spec satisfied: paper body, accent STRIPE (waist band), ink head. Arms paper. Legs paper.

### Pipeline tail

```
[runner] material slot inventory (before retint):
[runner]   Rogue_ArmLeft: ['rogue_texture']
[runner]   Rogue_ArmRight: ['rogue_texture']
[runner]   Rogue_Body: ['rogue_texture']
[runner]   Rogue_Head: ['rogue_texture']
[runner]   Rogue_LegLeft: ['rogue_texture']
[runner]   Rogue_LegRight: ['rogue_texture']
[runner] Rung 3 FIRES — waist face-band on body mesh
[runner] Rung-3 band: z=[0.760, 0.804] (total_h=0.872)
[runner] Rung-3: 26/1172 faces → runnerAccent (2.2% of body)
[runner] retint: 'Rogue_Head' → runnerInk
[runner] retint: 'Rogue_ArmLeft' → runnerPaper
[runner] retint: 'Rogue_ArmRight' → runnerPaper
[runner] retint: 'Rogue_LegLeft' → runnerPaper
[runner] retint: 'Rogue_LegRight' → runnerPaper
[runner] retint: 'Rogue_Body' → (already set by Rung 3)
[runner] retint complete — Rung 3 fired, accent_applied=True
[runner] exported (draco=True)
[runner] glb bytes: 347896
Blender quit
```

Exit code: 0.

### Contract check

```
runner contract ok: ['Idle', 'Run', 'Walk'] ['runnerAccent', 'runnerInk', 'runnerPaper'] 347896 bytes
```

All assertions pass: clips correct, materials ⊆ {runnerPaper, runnerInk, runnerAccent}, 347,896 bytes (23% of 1.5MB limit).

### Eyeball render assessment

`runner_check.png` (re-rendered):
- Head: solid ink (near-black) — correct
- Body: runnerPaper (warm off-white), with a narrow horizontal orange stripe at the waist/midriff — the accent STRIPE
- Arms: runnerPaper (warm off-white) — paper limbs, not orange
- Legs: runnerPaper (warm off-white) — paper limbs, not orange
- No gear visible, idle pose natural

Rung fired: **3 (waist face-band)**. Visual: a clean paper figure with a thin orange belt-ring at midriff and an ink head.
