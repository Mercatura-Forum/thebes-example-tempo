# TEMPO intro experience — design

Approved 2026-09-04. A choreographed intro layered over the existing page:
loader → logo zoom → cursor-reveal screen → scroll exit. Pure choreography
(the counter is theatre), plays on every page load. The "05 — find us"
expansion is explicitly out of scope (separate future project).

## Phase 1 — Loader (~2.6s)

- Full-viewport overlay, `var(--surface)` white, static markup in
  `index.html`. A one-line inline `<head>` script adds `html.intro` before
  first paint so the page never flashes beneath; a `<noscript>` rule hides
  the overlay entirely so a no-JS visitor gets the normal page.
- Center: TEMPO wordmark as two stacked SVG `<text>` layers in the display
  font (`Tanker`): a ghost outline copy, and a `var(--accent)`-filled copy
  clipped by a `<clipPath>` rect whose width tracks the eased progress
  value. Left-to-right fill.
- The same eased 0→100 value renders as a large numeric counter.
- Pill-shaped chips labeled with the four electrolytes (Sodium, Potassium,
  Magnesium, Chloride) spawn at random positions with slow drift and
  rotation, staggered, ~6–10 over the phase, fading before the zoom.
- Real asset loading (GLB, fonts, chain) proceeds in parallel and does not
  drive the counter.

## Phase 2 — Zoom (~0.6s)

Pills and counter clear; the filled wordmark scales up around center until
oversized. The same DOM element becomes the reveal screen's logo — no seam.

## Phase 3 — Reveal screen (interactive, unbounded)

- White overlay with the huge filled logo. A circular hole (~180px radius)
  follows the cursor with eased lag — a CSS `mask-image` radial-gradient
  (hard stop) on the overlay, punched through everything including the logo.
- Beneath the hole: the 3D can, drawn by the existing global canvas into a
  new intro `[data-can3d]` slot whose position tracks the cursor (the
  canvas already reads slot rects per frame; no scissor changes needed).
- One-line filter in `can3d.js`: while `body.intro` is set, render only the
  intro slot, so the hero can does not appear through the hole.
- WebGL/model failure: the intro slot shows the existing static can PNG
  fallback, still cursor-following.
- Touch devices (no cursor): mask + can auto-drift together on a gentle
  scripted wander; vertical swipes stay free for the exit.
- Bottom-center: an animated scroll indicator ("scroll" + chevron) that is
  a real `<button>`.

## Phase 4 — Exit

- Scroll locked during phases 1–3 (overlay intercepts; page pinned at top).
- First wheel tick, touch swipe, Space/arrow/PageDown, or indicator click
  slides the overlay up (~0.7s) and unlocks scroll at the hero. No replay
  until the next load.
- `prefers-reduced-motion`: no pills, no zoom, no reveal screen — the logo
  appears filled for ~0.4s, then fades straight to the page.

## Files

| file | change |
|---|---|
| `intro.js` (new) | timeline driver (rAF + eased t), pill spawner, counter, cursor/auto-drift tracking, exit handling, scroll lock. Timing values are named constants at the top. The timeline is a pure function `t → {phase, progress, zoom}` exported for testing. |
| `index.html` | inline head class-adder, overlay markup (loader + reveal in one fixed element), intro can slot, scroll-indicator button, `<script src="intro.js">` |
| `styles.css` | intro styles appended AFTER the last `≤940px` media block (same-specificity ordering trap) |
| `can3d.js` | the `body.intro` slot filter (one line) |

## Verification

- Existing suites stay green: `node oracle/api.mjs`, moc interpreter units.
- New `oracle/intro.mjs`: unit-tests the pure timeline (monotonic 0→100,
  phase boundaries at the named constants, reduced-motion path collapses to
  the short fade).
- Headless battery (Playwright Chromium, `--use-gl=angle
  --enable-unsafe-swiftshader`, wait for `body.webgl`): frames at
  loader-mid (fill ≈ counter), zoom-end, reveal with the mask at two cursor
  positions (can visible in the hole, hero can NOT), post-exit hero landing.
- Mobile emulation gated on `innerWidth === viewport.width` before any rect
  math; assert the intro introduces no horizontal overflow.
