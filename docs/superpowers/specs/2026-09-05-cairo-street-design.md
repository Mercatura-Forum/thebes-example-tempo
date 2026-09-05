# TEMPO Cairo street — design

Approved 2026-09-05 (direction: free-roam diorama behind an opt-in portal).
Section `05 — Find us cold` becomes literal: a hand-crafted, walkable Cairo
street-corner diorama ending at a koshk (street kiosk) whose lit fridge shelf
holds the real TEMPO cans — tap one and you are in the on-chain shop. This is
the "On the shelf near you" promise made spatial, and the flagship set-piece
of the demo. NOT an open world: one block, one destination, built like a
diorama you could hold.

## Concept

- The stockists map graduates into a portal: the `#egyptMap` slot shows a
  styled poster still of the street with **"Step into the street"**. Nothing
  3D loads until it is tapped (the page keeps its lightness; the world's
  megabytes are on the user's terms).
- On enter, the section expands to a full-bleed stage. A runner (the brand is
  hydration that keeps up) is steered with WASD/arrows — touch gets a
  thumb joystick — through one stylized Cairo block at golden hour.
- Reaching the koshk eases the camera into the fridge shelf: free-roam
  yields, the cans (existing GLB + flavor labels) sit lit on the racks,
  each clickable → leave the street at the shop section with that flavor
  selected. ESC / "leave the street" exits anytime; the world is disposed.

## Art direction

- One street corner: mud-brick and plaster facades, mashrabiya balconies,
  striped awnings, hanging string lights, dusty ground, a minaret silhouette
  against the sky, the koshk dense with crates and its humming fridge. A cat
  on a crate. Nothing enterable except the koshk's face.
- Palette locked to the site: paper/ink surfaces, the accent orange reserved
  for TEMPO cans, signage and the koshk fridge glow — the diorama must read
  as this site's design language, not a game asset pack.
- Stylized low-poly with flat/gradient materials and baked AO; tilt-shift
  framing (slight top-down, soft vignette) so it reads as a diorama.

## Assets — built in this repo's pipeline

- Modeled procedurally in Blender via `src-model/tools` (same pipeline as the
  can and splash), exported draco-compressed GLB into `assets/street/`.
- Budgets (hard): street GLB set ≤ 5MB total wire, ≤ 120k tris in view,
  poster still ≤ 150KB webp. The cans on the shelf reuse the existing can
  GLB — no duplicate model.
- The poster is a render from the same scene, produced by the pipeline.

## Architecture

- `street.js` — portal, loader, renderer, input, camera; lazy ES module
  dynamically imported on portal tap (three already in the importmap).
- `street-sim.js` — PURE simulation, no DOM/three: movement integrator
  (dt-based, same `followK` discipline as the intro), capsule-vs-AABB
  collision resolve, camera follow/focus state machine, joystick vector
  math, koshk proximity trigger. Imported by `street.js` in the browser and
  by the node oracle directly (real ESM — no `new Function` loader needed).
- Own `<canvas>` + renderer inside the section stage (the global can3d
  canvas keeps its job); DPR capped at 1.5 (1 on low-power), disposed fully
  on leave — geometries, materials, textures, renderer, listeners.
- While the street is open: page scroll parks (the damped scroll already
  adopts external state); `tempo:street-open/closed` events for app.js.
- Failure/perf ladder: no WebGL or load failure → the portal falls back to
  the poster + a static shelf render with the same clickable flavor links
  (a11y parity). `prefers-reduced-motion` → the same fallback, no free-roam.

## Verification

- `oracle/street.mjs` — units on the pure sim: integrator dt-invariance,
  collision never tunnels at any dt, camera state machine transitions
  (roam → approach → shelf-focus → leave), joystick clamp/deadzone.
- Battery additions (same SwiftShader harness):
  - portal laziness — zero `assets/street/*` network entries before tap;
  - enter → joystick/keys walk to the koshk → focus engages → a can click
    lands at `#shop` with the flavor applied;
  - dispose — after leave, renderer count back to baseline, no listener
    leaks, scroll works, no horizontal overflow at 1440 and 390;
  - motion asserted as progress-between-samples (SwiftShader stall rule).
- Perf gates: enter-to-first-frame < 3s on the battery box; steady walk
  ≥ 20fps headless SwiftShader (proxy for 60 on real GPUs).

## Out of scope (explicitly)

Multiple blocks or wandering beyond the corner, koshk interior, NPCs and
traffic, day/night cycle, audio, save state. Each is a separate decision
later — the diorama must feel complete without them.

## Files

| file | change |
|---|---|
| `street.js` (new) | portal + world driver, lazy-imported |
| `street-sim.js` (new) | pure simulation module, oracle-shared |
| `assets/street/` (new) | draco GLBs + poster webp from the pipeline |
| `src-model/tools/` | street build script alongside the can pipeline |
| `index.html` | portal markup in section 05, script wiring |
| `styles.css` | stage, portal, joystick, focus UI — appended per the ≤940px ordering trap |
| `app.js` | flavor handoff on shelf-can click; street open/close events |
| `oracle/street.mjs`, `oracle/verify-intro.py` | sim units + battery additions |
