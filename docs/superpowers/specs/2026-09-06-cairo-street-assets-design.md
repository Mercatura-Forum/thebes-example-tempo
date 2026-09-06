# TEMPO Cairo street — asset integration design

Approved 2026-09-06. Upgrades the street diorama (spec:
`2026-09-05-cairo-street-design.md`, deploy-held since f35acf2) from
all-procedural to license-verified external assets, per the research ledger
`../research/2026-09-05-cairo-street-assets.md`. Scope: the full ledger —
character, street fabric, props. Licensing: CC0 + CC-BY with NOTICE.md
attribution. This pass ends by un-docking section 05: portal rewired,
battery green, deployed under the standing push-live order.

## Architecture (decided)

Kitbash-into-pipeline. External assets are **inputs to `build_street.py`**,
which imports, palette-locks, decimates and joins them in Blender, exporting
the same single draco `assets/street/street.glb` as today. The one exception
is the character: a skinned, animated mesh cannot join the static kitbash, so
a new `build_runner.py` exports `assets/street/runner.glb` (mesh + Idle/Walk/
Run clips). Rejected: runtime composition of per-asset GLBs — smears the
budget across files, re-implements the palette lock in three.js, and breaks
the held-diorama feel.

Invariants that survive untouched: `street_layout.json` as single source of
truth (Blender scene, sim colliders, runtime anchors); the ≤5MB total-wire /
≤120k-tris budgets; portal laziness; the pure-sim/oracle split; the fallback
ladder (poster + flavor links).

## Acquisition & provenance

- `src-model/vendor/<source>/` per origin: kaykit-adventurers,
  kaykit-animations, kenney-fantasy-town, kenney-city-commercial,
  quaternius (pre-QAL poly.pizza), sketchfab-arab-house, sketchfab-minaret,
  sketchfab-tuktuk, sketchfab-fanous, …
- Commit ONLY the files the kitbash consumes + `RECEIPT.md` per source:
  source URL, download date, license label as captured (Sketchfab: the
  archived `api.sketchfab.com/v3/models/<uid>` JSON with license slug;
  Quaternius: the CC0-labeled page snapshot — QAL rule). Full archives are
  gitignored.
- `NOTICE.md` gains a "Cairo street" section. Every CC-BY asset: title,
  author, source URL, license URL, modifications note (decimation and draco
  recompression count). The splash entry is the template. Kenney logo never
  used; Mixamo never enters the repo (settled — do not re-litigate).
- Sketchfab downloads are account-gated: those zips may need a manual grab;
  Kenney, KayKit (official GitHub mirror) and poly.pizza fetch directly.

## Pipeline

- `street_layout.json`: each placement gains an asset ref — `proc:<builder>`
  (existing procedural) or `vendor:<source>/<file>` — plus transform, tint
  override, and per-asset tri budget.
- `build_street.py` import stage per vendor ref: load (glTF/FBX) →
  normalize scale → strip source materials → re-tint to the locked palette
  (flat materials, `diffuse_color` set alongside Principled — the Workbench
  trap) → decimate to the layout's tri budget → place → join.
- Casting: Kenney Fantasy Town = side facades (recolored sand/ochre);
  Legorook Arab House = hero back facade; decimated Samarra minaret replaces
  the procedural skyline silhouette; City Kit Commercial dresses the koshk;
  the koshk STRUCTURE stays procedural (shelf boards, fridge glow, TEMPO
  sign are brand-bespoke); Quaternius Can Fridge beside it; props table per
  the ledger (cat, crates, tuk-tuk, fanous, ahwa chair+table, scooter,
  pots). Signage uses our own baked Arabic textures (none redistributable —
  and better for authenticity). Mashrabiya (129k faces) enters ONLY if hard
  decimation reads clean; else the procedural balcony stays.
- `build_runner.py` (new): KayKit Adventurers base body, fantasy gear
  stripped, re-tinted to the brand runner (paper body, accent stripe, ink
  head — not a knight); Idle/Walk/Run retargeted from KayKit Character
  Animations (same rig family); root motion baked out (the sim owns
  position); draco `runner.glb`.
- Poster re-rendered from the upgraded scene (Workbench flat+cavity,
  ≤150KB webp). Colliders in layout.json updated where new geometry
  differs; spawn/trigger-standable checks re-run.

## Runtime

- `street.js`: primitives runner → `runner.glb` (fetched alongside
  street.glb — the lazy contract holds) + `AnimationMixer`. Sim speed
  selects Idle/Walk/Run with ~0.2s crossfades; walk/run timescale tied to
  ground speed (no foot-slide); velocity-facing kept; procedural bob
  dropped. Dispose grows mixer/skeleton/clip cleanup.
- Action selection (`animFor(speed)`: thresholds + hysteresis, no flicker
  at boundaries) lives in `street-sim.js` as a pure function.
- `TempoStreet.state.anim` exposes the current action for the battery.
- Untouched: portal, street-lock, camera state machine, shelf focus, flavor
  handoff, no-WebGL/reduced-motion fallbacks.

## Verification

- `verify_glb.py` gates: total wire (street.glb + runner.glb + poster)
  ≤5MB; ≤120k tris in view; runner.glb has exactly Idle/Walk/Run clips;
  **palette-lock check** — every exported material color ∈ the site palette
  set (a stray asset-pack material fails the build).
- Attribution gate: every `vendor:` ref from a CC-BY source in
  street_layout.json must have a matching NOTICE.md entry — machine-checked.
- `oracle/street.mjs` adds `animFor` units (thresholds, hysteresis,
  dt-independence).
- `oracle/verify-street.py`: all existing 22 checks green + runner-animates
  (poll `TempoStreet.state.anim` Idle→Walk under held keys; two-sample
  motion rule; camera-settle before any projected click — never wall-clock).
- `verify-intro.py` reruns green (shared files).

## Ship (un-dock)

Restore the `.street-portal` block + `street.js?v=` tag per the comment at
the egyptMap slot in index.html; sync dist incl. `assets/street/`; bump
`?v=`s; README file table; deploy per the standing push-live order;
md5-verify served bytes; update project memory from deploy-held → live.

## Open items (resolve during implementation)

- Verify KayKit clips retarget onto the chosen body in Blender 4.0; confirm
  in-place vs root-motion and bake accordingly.
- Check as-downloaded texture sizes on the three Sketchfab picks.
- String lights: inspect Kenney downloads; else keep procedural catenaries.

## Out of scope

Ambient audio, shadows, runtime-rendered poster, real-device joystick pass,
NPCs/traffic, day/night — unchanged from the original spec's exclusions and
the polish backlog.

## Files

| file | change |
|---|---|
| `src-model/vendor/` (new) | consumed asset files + RECEIPT.md per source |
| `src-model/tools/build_street.py` | vendor import/palette/decimate stage |
| `src-model/tools/build_runner.py` (new) | character + animation pipeline |
| `src-model/tools/street_layout.json` | asset refs, tint/tri budgets, colliders |
| `src-model/tools/verify_glb.py` | palette-lock, clip, wire gates |
| `street.js` | runner.glb + AnimationMixer, dispose additions |
| `street-sim.js` | pure `animFor` (thresholds + hysteresis) |
| `oracle/street.mjs`, `oracle/verify-street.py` | animFor units, runner battery |
| `NOTICE.md` | Cairo street CC-BY section |
| `index.html`, dist | portal rewire + ship |
