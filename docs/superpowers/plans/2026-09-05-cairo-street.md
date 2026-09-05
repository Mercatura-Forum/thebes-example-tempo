# Cairo street — oracle-gated implementation plan

Spec: `../specs/2026-09-05-cairo-street-design.md`. Free-roam koshk-corner
diorama behind an opt-in portal in section 05. One adjustment vs the spec:
the dotted Egypt map stays (it earns its place); the portal is its sibling
card in the stockists head.

## Task 1 — the world on disk (pipeline)

`src-model/tools/street_layout.json` — single source of truth: playable
bounds, spawn, koshk anchor + shelf/camera anchors, collider AABBs, prop
placements. `src-model/tools/build_street.py` (Blender 4.0 headless) reads
it and builds the block: ground + sidewalk, three back facades with inset
windows/AC units/parapets, a mashrabiya balcony, striped awnings, the koshk
(open front, three shelf boards, emissive fridge glow, TEMPO sign), crate
stacks, two lamp posts + sagging string lights, minaret silhouette, the cat.
Palette-locked flat materials; emissives for bulbs/fridge/sign. Exports
`assets/street/street.glb` (gate: ≤ 5MB, verified by `verify_glb.py`) and
renders `assets/street/poster.webp` (Workbench flat+cavity, gate: ≤ 150KB).

## Task 2 — the pure simulation (oracle-gated)

`street-sim.js` — real ES module, no DOM/three: `joyVec` (deadzone+clamp),
`stepMover` (exponential velocity approach, substepped so displacement per
substep < radius — no tunneling at any dt), `resolveCollision`
(circle-vs-AABB push-out on xz), `nextMode` (roam → focus near the koshk
with hysteresis → leave), `followK`. `oracle/street.mjs` gates: dt-invariance
of the integrator, no tunneling through a thin wall at dt=1000ms, deadzone
edges, mode hysteresis (no flicker at the trigger radius), collision slide
along walls.

## Task 3 — the runtime

`street.js` (module): portal click → `street-lock` on html, full-bleed stage
(fixed, z 450 — under the intro's 500), own renderer (DPR ≤ 1.5), fetch
street.glb + layout.json (first street bytes only now — the lazy contract),
shelf cans from the existing `tempo-can.glb` + label textures, golden-hour
hemisphere+directional + fog, CSS vignette. Runner from primitives (paper
body, accent stripe, ink head), velocity-facing + bob. Keys WASD/arrows;
touch joystick div → `joyVec`. Camera: eased follow (roam) / shelf anchor
(focus). Can click → `TEMPO.setFlavor(k)` (exported from app.js) → leave →
smooth-scroll to `#shop`. Leave/ESC → full dispose (geometries, materials,
textures, renderer, listeners, stage node) + `street-lock` off.
`window.TempoStreet = { CONST, state, warp }` for the battery. Fallbacks:
no-WebGL / reduced-motion → poster panel with the three flavors as links.
`scroll.js` learns to stand down under `street-lock` (one line).

## Task 4 — the battery

`oracle/verify-street.py`: portal laziness (zero `assets/street/*` resource
entries pre-tap); enter → keys walk (player pos progresses between samples —
SwiftShader stall rule); `warp` near koshk → focus engages → click a can →
lands at `#shop` with `data-flavor` applied; leave → canvas gone, scroll
restored, no overflow (1440 + 390); enter-to-first-frame < 3s; walking
rAF ≥ 20fps average over 2s. `verify-intro.py` reruns green (shared files
changed).

## Task 5 — ship

Bump `?v=`s, README file table, dist sync (incl. `assets/street/`), deploy
per the standing order, md5-verify served bytes.
