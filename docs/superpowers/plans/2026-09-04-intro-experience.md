# TEMPO Intro Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A choreographed intro layered over the existing page: loader (logo fill + 0→100 counter + electrolyte pills) → logo zoom → cursor-reveal of the 3D can through a masked white sheet → scroll exit.

**Architecture:** One new plain script (`intro.js`) owns a pure timeline function (`t → {phase, progress, zoom}`, exposed as `window.TempoIntro` for the node oracle) plus the DOM choreography. The overlay is static markup shown pre-paint via an inline `<head>` class; the 3D can reuses the existing one-global-canvas `[data-can3d]` slot system (rects are read per frame, so a cursor-following slot needs no scissor changes). A one-line filter in `can3d.js` draws only the intro slot while `body.intro` is set.

**Tech Stack:** Plain browser JS (no build, no deps), SVG wordmark, CSS mask for the reveal hole. Node for the oracle; Playwright Chromium (SwiftShader) for the headless battery.

**Spec:** `docs/superpowers/specs/2026-09-04-intro-experience-design.md`

## Global Constraints

- No build step, no new dependencies in the page. `intro.js` is a plain script like `app.js` (only `can3d.js` is a module).
- Art is CSS/SVG-drawn; no third-party assets (styles.css header rule).
- All intro styles appended AFTER the last `@media (max-width: 940px)` block in `styles.css` — same-specificity blocks resolve by file order.
- The intro must never brick the page: `<noscript>` hides it; a watchdog un-bricks if `intro.js` fails to load; `prefers-reduced-motion` gets the short path.
- `.intro` and `.intro__sheet` use `overflow: clip` — the zoomed logo must not introduce horizontal overflow (the `.hero__glow` lesson).
- Timing/geometry values live in `CONST` at the top of `intro.js`; CSS twins (exit duration `.7s`, mask radius via `--mr`) carry a `/* == CONST.X */` comment.
- Commits: lowercase descriptive sentences, no personal names, no AI attribution (repo convention).
- Existing suites must stay green after every task: `node oracle/api.mjs` and the moc interpreter units.

---

### Task 1: Pure timeline + oracle

**Files:**
- Create: `intro.js`
- Test: `oracle/intro.mjs`

**Interfaces:**
- Consumes: nothing.
- Produces: `window.TempoIntro = { CONST, timeline }`. `CONST = { T_LOAD: 2600, T_ZOOM: 600, T_EXIT: 700, T_REDUCED: 400, ZOOM_SCALE: 7, MASK_R: 180, FILL_W: 600, PILL_EVERY: 280, PILL_MAX: 9, PILL_MAX_NARROW: 5, CAN_W: 240, CAN_H: 420, EASE_FOLLOW: 0.12 }`. `timeline(t, reduced)` returns `{ phase: 'load'|'zoom'|'reveal'|'done', progress: 0..100, zoom: 1..ZOOM_SCALE }`. Task 2 fills in `boot()`; Task 1 leaves it a guarded no-op.

- [ ] **Step 1: Write the failing test**

Create `oracle/intro.mjs` (same harness idiom as `oracle/api.mjs` — stub globals, load the plain script with `new Function`, exit nonzero on any failure):

```js
// oracle/intro.mjs — unit-tests the pure intro timeline.
// Run: node oracle/intro.mjs   (exits nonzero on any failure)
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
let failures = 0
const check = (ok, name) => { console.log((ok ? 'ok ' : 'FAIL ') + name); if (!ok) failures++ }

// Browser-enough globals: boot() must bail cleanly when #intro is absent.
globalThis.window = globalThis
globalThis.document = {
  getElementById: () => null,
  addEventListener: () => {},
  documentElement: { classList: { add() {}, remove() {} }, dataset: {} },
}
globalThis.matchMedia = () => ({ matches: false })

new Function(readFileSync(join(root, 'intro.js'), 'utf8'))()
const I = globalThis.TempoIntro
check(!!I && typeof I.timeline === 'function', 'TempoIntro.timeline exposed')
const { T_LOAD, T_ZOOM, T_REDUCED, ZOOM_SCALE } = I.CONST

// ── load phase ──
let s = I.timeline(0, false)
check(s.phase === 'load' && s.progress === 0 && s.zoom === 1, 't=0 is load/0/1')
let prev = -1, mono = true, sawEnd = false
for (let i = 0; i <= 200; i++) {
  const p = I.timeline((T_LOAD * i) / 200, false).progress
  if (p < prev - 1e-9) mono = false
  prev = p
  if (p >= 99.999) sawEnd = true
}
check(mono, 'progress is monotonic over the load phase')
check(sawEnd, 'progress reaches 100')
check(I.timeline(T_LOAD - 1, false).phase === 'load', 'still load just before T_LOAD')

// ── zoom phase ──
s = I.timeline(T_LOAD, false)
check(s.phase === 'zoom' && s.progress === 100, 'T_LOAD flips to zoom at full fill')
const zMid = I.timeline(T_LOAD + T_ZOOM / 2, false).zoom
check(zMid > 1 && zMid < ZOOM_SCALE, 'zoom rises through the phase')
prev = 0; mono = true
for (let i = 0; i <= 100; i++) {
  const z = I.timeline(T_LOAD + (T_ZOOM * i) / 100, false).zoom
  if (z < prev - 1e-9) mono = false
  prev = z
}
check(mono, 'zoom is monotonic')

// ── reveal ──
s = I.timeline(T_LOAD + T_ZOOM, false)
check(s.phase === 'reveal' && s.zoom === ZOOM_SCALE, 'reveal holds ZOOM_SCALE')
check(I.timeline(T_LOAD + T_ZOOM + 60000, false).phase === 'reveal', 'reveal is unbounded')

// ── reduced motion ──
s = I.timeline(0, true)
check(s.phase === 'load' && s.progress === 100 && s.zoom === 1, 'reduced shows the filled logo at once')
check(I.timeline(T_REDUCED - 1, true).phase === 'load', 'reduced holds through T_REDUCED')
check(I.timeline(T_REDUCED, true).phase === 'done', 'reduced skips straight to done')

// ── counter is an integer 0..100 ──
let ints = true
for (let i = 0; i <= 50; i++) {
  const n = Math.round(I.timeline((T_LOAD * i) / 50, false).progress)
  if (!Number.isInteger(n) || n < 0 || n > 100) ints = false
}
check(ints, 'rounded counter stays in 0..100')

process.exit(failures ? 1 : 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node oracle/intro.mjs`
Expected: throws `ENOENT` reading `intro.js` (file does not exist yet) — nonzero exit.

- [ ] **Step 3: Write minimal implementation**

Create `intro.js`:

```js
/* ============================================================
   TEMPO — intro experience. Loader (choreographed logo fill +
   0→100 counter + electrolyte pills) → logo zoom → cursor
   reveal of the 3D can through the masked sheet → scroll exit.
   The timeline is pure and exposed for the node oracle.
   ============================================================ */
(function () {
  'use strict';

  const CONST = {
    T_LOAD: 2600,        // loader choreography ms
    T_ZOOM: 600,         // logo zoom ms
    T_EXIT: 700,         // exit slide ms (== .intro--exit transition)
    T_REDUCED: 400,      // reduced-motion logo hold ms
    ZOOM_SCALE: 7,       // final logo scale
    MASK_R: 180,         // reveal hole radius px (== --mr)
    FILL_W: 600,         // SVG viewBox width the fill rect grows across
    PILL_EVERY: 280,     // ms between pill spawns
    PILL_MAX: 9,
    PILL_MAX_NARROW: 5,  // ≤940px spawns fewer
    CAN_W: 240,          // intro can slot px
    CAN_H: 420,
    EASE_FOLLOW: 0.12,   // cursor lerp per frame
  };
  const ELECTROLYTES = ['Sodium', 'Potassium', 'Magnesium', 'Chloride'];

  const easeInOutCubic = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const easeOutCubic = (u) => 1 - Math.pow(1 - u, 3);

  // Pure: elapsed ms (+ reduced-motion flag) → what the screen shows.
  // 'done' only occurs on the reduced path; the normal reveal waits for
  // the user's scroll, which is an event, not a time.
  function timeline(t, reduced) {
    if (reduced) {
      return t < CONST.T_REDUCED
        ? { phase: 'load', progress: 100, zoom: 1 }
        : { phase: 'done', progress: 100, zoom: 1 };
    }
    if (t < CONST.T_LOAD) {
      return { phase: 'load', progress: 100 * easeInOutCubic(t / CONST.T_LOAD), zoom: 1 };
    }
    if (t < CONST.T_LOAD + CONST.T_ZOOM) {
      const u = (t - CONST.T_LOAD) / CONST.T_ZOOM;
      return { phase: 'zoom', progress: 100, zoom: 1 + (CONST.ZOOM_SCALE - 1) * easeOutCubic(u) };
    }
    return { phase: 'reveal', progress: 100, zoom: CONST.ZOOM_SCALE };
  }

  window.TempoIntro = { CONST, timeline };

  function boot() {
    // Task 2 fills this in. Guarded so the oracle (and a stripped page)
    // loads the script with no side effects.
  }

  if (typeof document !== 'undefined' && document.getElementById('intro')) boot();
})();
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node oracle/intro.mjs`
Expected: every line `ok …`, exit 0. Also run `node oracle/api.mjs` — still exit 0.

- [ ] **Step 5: Commit**

```bash
git add intro.js oracle/intro.mjs
git commit -m "the intro timeline: pure phases under oracle test"
```

---

### Task 2: Overlay markup, styles, loader choreography

**Files:**
- Modify: `index.html` (head inline script + noscript, overlay markup before the scripts, `<script src="intro.js?v=1">` first among the body scripts)
- Modify: `styles.css` (one appended block at end of file)
- Modify: `intro.js` (fill in `boot()`)

**Interfaces:**
- Consumes: `TempoIntro.CONST`, `timeline` from Task 1.
- Produces: DOM ids `#intro #introUnder #introSheet #introFillRect #introCount #introPills #introScroll #introCan`; state classes `html.intro` (pre-paint, locks scroll), `body.intro` (set by boot; Task 3's canvas filter reads it), `.intro--zoom`, `.intro--reveal`, `.intro--exit`; events `tempo:slots-changed` + `tempo:intro-done` dispatched after exit. Task 3 extends `boot()`'s reveal branch.

- [ ] **Step 1: Add the head inline script + noscript**

In `index.html` `<head>`, immediately BEFORE the stylesheet link. The watchdog un-bricks the page if `intro.js` never boots (network failure): boot proves itself by setting `body.intro`.

```html
<script>
  document.documentElement.classList.add('intro');
  setTimeout(function () {
    if (!document.body || !document.body.classList.contains('intro')) {
      document.documentElement.classList.remove('intro');
      var n = document.getElementById('intro'); if (n) n.remove();
      n = document.getElementById('introUnder'); if (n) n.remove();
    }
  }, 6000);
</script>
<noscript><style>#intro, #introUnder { display: none !important; }</style></noscript>
```

- [ ] **Step 2: Add the overlay markup**

In `index.html`, right after `<body>`'s opening content begins (before `<header>`; exact anchor: make it the first children of `<body>`). `#introUnder` is a sibling because it must sit BELOW the global can canvas (z 40) while `.intro` sits above it — a child could never escape its parent's stacking context.

```html
<!-- ── Intro: loader → zoom → cursor reveal (intro.js) ── -->
<div class="intro__under" id="introUnder" aria-hidden="true"></div>
<div class="intro" id="intro">
  <div class="intro__can can-slot" id="introCan" data-can3d data-role="intro" aria-hidden="true">
    <img class="can-fallback" alt="" />
  </div>
  <div class="intro__sheet" id="introSheet" aria-hidden="true">
    <svg class="intro__logo" viewBox="0 0 600 140">
      <defs>
        <clipPath id="introFillClip"><rect id="introFillRect" x="0" y="0" width="0" height="140" /></clipPath>
      </defs>
      <text class="intro__logo-ghost" x="300" y="76">TEMPO</text>
      <text class="intro__logo-fill" x="300" y="76" clip-path="url(#introFillClip)">TEMPO</text>
    </svg>
    <div class="intro__count" id="introCount" aria-hidden="true">0</div>
    <div class="intro__pills" id="introPills" aria-hidden="true"></div>
  </div>
  <button class="intro__scroll" id="introScroll" type="button">
    <span>scroll</span><span class="intro__chev" aria-hidden="true"></span>
  </button>
</div>
```

Add `<script src="intro.js?v=1"></script>` as the FIRST script tag at the end of `<body>` (before `sdk/boundary.js`).

- [ ] **Step 3: Append the intro styles**

At the very END of `styles.css` (after the last existing `≤940px` block — file order decides same-specificity winners). The `.7s`/`.3s` exit durations mirror `CONST.T_EXIT`; `--mr` is set from `CONST.MASK_R` by boot.

```css
/* ============================================================
   Intro experience (intro.js) — appended last on purpose: the
   ≤940px block below must outrank the earlier mobile blocks.
   ============================================================ */
html.intro { overflow: hidden; }
.intro__under { position: fixed; inset: 0; z-index: 35; background: var(--accent-tint); display: none; }
html.intro .intro__under { display: block; }
.intro { position: fixed; inset: 0; z-index: 60; overflow: clip; display: none; }
html.intro .intro { display: block; }
.intro__sheet {
  position: absolute; inset: 0; background: var(--surface); overflow: clip;
  display: grid; place-items: center;
  --mx: 50vw; --my: 60vh; --mr: 180px; /* == CONST.MASK_R */
}
.intro--reveal .intro__sheet {
  -webkit-mask-image: radial-gradient(circle var(--mr) at var(--mx) var(--my), transparent calc(var(--mr) - 2px), #000 var(--mr));
  mask-image: radial-gradient(circle var(--mr) at var(--mx) var(--my), transparent calc(var(--mr) - 2px), #000 var(--mr));
}
.intro__logo { width: min(72vw, 680px); height: auto; transform-origin: center; will-change: transform; }
.intro__logo text {
  font-family: var(--font-display); font-size: 118px; letter-spacing: .04em;
  text-anchor: middle;
}
.intro__logo-ghost { fill: var(--line); }
.intro__logo-fill { fill: var(--accent); }
.intro__count {
  position: absolute; left: clamp(16px, 4vw, 48px); bottom: clamp(14px, 3.5vw, 40px);
  font-family: var(--font-display); font-size: clamp(48px, 9vw, 110px); line-height: 1;
  color: var(--ink); font-variant-numeric: tabular-nums;
}
.intro__pills { position: absolute; inset: 0; pointer-events: none; }
.intro__pill {
  position: absolute; padding: .55em 1.25em; border: 1.5px solid var(--ink);
  border-radius: 999px; background: var(--surface);
  font-size: 14px; letter-spacing: .14em; text-transform: uppercase;
  rotate: var(--rot, 0deg); opacity: 0;
  animation: introPill 2.2s ease-out forwards;
}
@keyframes introPill {
  0% { opacity: 0; translate: 0 26px; }
  18% { opacity: 1; }
  100% { opacity: 0; translate: 0 -80px; }
}
.intro--zoom .intro__count, .intro--reveal .intro__count,
.intro--zoom .intro__pills, .intro--reveal .intro__pills { opacity: 0; transition: opacity .25s; }
.intro__can { position: absolute; left: 0; top: 0; width: 240px; height: 420px; pointer-events: none; } /* == CONST.CAN_W/H */
.intro__ring { position: absolute; left: 0; top: 0; border: 1.5px solid var(--ink); border-radius: 50%; opacity: 0; pointer-events: none; }
.intro--reveal .intro__ring { opacity: .35; }
.intro__scroll {
  position: absolute; left: 50%; bottom: 26px; translate: -50%;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  background: none; border: 0; cursor: pointer; font: inherit;
  font-size: 12px; letter-spacing: .22em; text-transform: uppercase; color: var(--ink-soft);
  opacity: 0; pointer-events: none;
}
.intro--reveal .intro__scroll { opacity: 1; pointer-events: auto; transition: opacity .4s .2s; }
.intro__chev { width: 1.5px; height: 34px; background: var(--ink); animation: introChev 1.6s ease-in-out infinite; }
@keyframes introChev {
  0%, 100% { scale: 1 1; translate: 0 0; opacity: 1; }
  50% { scale: 1 .55; translate: 0 10px; opacity: .5; }
}
.intro--exit { transform: translateY(-100%); transition: transform .7s cubic-bezier(.6, 0, .18, 1); } /* == CONST.T_EXIT */
body:not(.webgl) .intro__can .can-fallback { display: block; width: 100%; height: 100%; object-fit: contain; }
@media (prefers-reduced-motion: reduce) {
  .intro__pills, .intro__chev { display: none; }
  .intro--exit { transition-duration: .3s; }
}
@media (max-width: 940px) {
  .intro__logo { width: 86vw; }
  .intro__count { font-size: 64px; }
  .intro__can { width: 190px; height: 340px; }
}
```

- [ ] **Step 4: Fill in boot() — loader, zoom, reduced path, exit**

Replace the empty `boot()` in `intro.js` with (the reveal branch stays a stub comment until Task 3):

```js
  function boot() {
    const root = document.getElementById('intro');
    const under = document.getElementById('introUnder');
    const sheet = document.getElementById('introSheet');
    const fillRect = document.getElementById('introFillRect');
    const count = document.getElementById('introCount');
    const pillBox = document.getElementById('introPills');
    const logo = root.querySelector('.intro__logo');
    const scrollBtn = document.getElementById('introScroll');
    const canSlot = document.getElementById('introCan');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const narrow = window.matchMedia('(max-width: 940px)').matches;

    document.body.classList.add('intro'); // proves boot to the head watchdog
    window.scrollTo(0, 0);
    sheet.style.setProperty('--mr', CONST.MASK_R + 'px');

    // the same static render the shop cards fall back to
    const fb = canSlot.querySelector('.can-fallback');
    if (fb) fb.src = 'assets/can_' + (document.documentElement.dataset.flavor || 'citrus') + '.png';

    let exited = false, phaseSeen = 'load', pills = 0, lastPill = 0;

    function spawnPill(now) {
      const max = narrow ? CONST.PILL_MAX_NARROW : CONST.PILL_MAX;
      if (pills >= max || now - lastPill < CONST.PILL_EVERY) return;
      lastPill = now;
      const el = document.createElement('span');
      el.className = 'intro__pill';
      el.textContent = ELECTROLYTES[pills % ELECTROLYTES.length];
      el.style.left = (6 + Math.random() * 82) + 'vw';
      el.style.top = (12 + Math.random() * 70) + 'vh';
      el.style.setProperty('--rot', (Math.random() * 36 - 18).toFixed(1) + 'deg');
      el.addEventListener('animationend', function () { el.remove(); });
      pillBox.appendChild(el);
      pills++;
    }

    function exit() {
      if (exited) return; exited = true;
      root.classList.add('intro--exit');
      window.scrollTo(0, 0);
      setTimeout(function () {
        document.documentElement.classList.remove('intro');
        document.body.classList.remove('intro');
        root.remove();
        under.remove();
        document.dispatchEvent(new CustomEvent('tempo:slots-changed'));
        document.dispatchEvent(new CustomEvent('tempo:intro-done'));
      }, CONST.T_EXIT);
    }

    // impatient users may leave from ANY phase, not just the reveal
    window.addEventListener('wheel', function () { exit(); }, { passive: true });
    window.addEventListener('keydown', function (e) {
      if (e.code === 'Space' || e.code === 'ArrowDown' || e.code === 'PageDown') exit();
    });
    let touchY = null;
    window.addEventListener('touchstart', function (e) { touchY = e.touches[0].clientY; }, { passive: true });
    window.addEventListener('touchmove', function (e) {
      if (touchY !== null && touchY - e.touches[0].clientY > 24) exit();
    }, { passive: true });
    scrollBtn.addEventListener('click', exit);

    const t0 = performance.now();
    function frame(now) {
      if (exited) return;
      const s = timeline(now - t0, reduced);
      fillRect.setAttribute('width', String(CONST.FILL_W * s.progress / 100));
      count.textContent = String(Math.round(s.progress));
      logo.style.transform = 'scale(' + s.zoom + ')';
      if (s.phase === 'load' && !reduced) spawnPill(now);
      if (s.phase !== phaseSeen) {
        phaseSeen = s.phase;
        if (s.phase === 'zoom') root.classList.add('intro--zoom');
        if (s.phase === 'reveal') root.classList.add('intro--reveal');
        if (s.phase === 'done') { exit(); return; }
      }
      // reveal branch: Task 3 (mask + ring + can follow the cursor)
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }
```

- [ ] **Step 5: Verify structure and suites**

Run: `node oracle/intro.mjs && node oracle/api.mjs`
Expected: both exit 0 (the oracle's null `getElementById('intro')` still skips boot).

Run the ordering gate — the intro block must start after the last pre-existing `≤940px` block:
```bash
awk '/max-width: 940px/{last=NR} /Intro experience \(intro\.js\)/{intro=NR} END{exit !(intro && last>intro)}' styles.css && echo "ORDER OK"
```
Expected: `ORDER OK` (the only `940px` match after the marker is the intro's own).

Serve and eyeball once: `python3 -m http.server 8000` → open `http://localhost:8000` — loader plays, zoom lands, white screen with huge logo + indicator, wheel exits to the hero.

- [ ] **Step 6: Commit**

```bash
git add index.html styles.css intro.js
git commit -m "the intro loader: filling wordmark, counter, electrolyte pills, zoom and the scroll exit"
```

---

### Task 3: Cursor reveal — mask, ring, the can under the sheet

**Files:**
- Modify: `intro.js` (reveal branch of `frame()`, cursor/drift state, ring element)
- Modify: `can3d.js` (intro-only slot filter in the per-slot render loop)

**Interfaces:**
- Consumes: Task 2's DOM ids and classes; `CONST.MASK_R/CAN_W/CAN_H/EASE_FOLLOW`; `body.intro` lifecycle.
- Produces: `--mx/--my` px vars on `#introSheet` each reveal frame; `.intro__ring` element appended to `#intro` at boot; the `can3d.js` guard `if (introOnly && s.role !== 'intro') continue`.

- [ ] **Step 1: Add cursor state + ring to boot()**

In `boot()` after the `canSlot` fallback block, add:

```js
    const ring = document.createElement('div');
    ring.className = 'intro__ring';
    ring.style.width = ring.style.height = (CONST.MASK_R * 2) + 'px';
    root.appendChild(ring);

    let hasMouse = false, driftT = 0, prevFrame = 0;
    let mx = window.innerWidth / 2, my = window.innerHeight * 0.6, tx = mx, ty = my;
    window.addEventListener('mousemove', function (e) {
      hasMouse = true; tx = e.clientX; ty = e.clientY;
    }, { passive: true });
```

- [ ] **Step 2: Fill the reveal branch of frame()**

Replace the `// reveal branch: Task 3` comment with (before `requestAnimationFrame(frame)`; also set `prevFrame = now` at the top of `frame` after the `exited` check, reading `const dt = prevFrame ? now - prevFrame : 16` first):

```js
      if (s.phase === 'reveal') {
        if (!hasMouse) { // touch and not-yet-moved desktop: gentle wander
          driftT += dt;
          tx = window.innerWidth / 2 + window.innerWidth * 0.28 * Math.sin(driftT * 0.00045);
          ty = window.innerHeight * 0.55 + window.innerHeight * 0.20 * Math.sin(driftT * 0.00032 + 1.7);
        }
        mx += (tx - mx) * CONST.EASE_FOLLOW;
        my += (ty - my) * CONST.EASE_FOLLOW;
        sheet.style.setProperty('--mx', mx.toFixed(1) + 'px');
        sheet.style.setProperty('--my', my.toFixed(1) + 'px');
        ring.style.transform = 'translate(' + (mx - CONST.MASK_R).toFixed(1) + 'px,' + (my - CONST.MASK_R).toFixed(1) + 'px)';
        canSlot.style.transform = 'translate(' + (mx - CONST.CAN_W / 2).toFixed(1) + 'px,' + (my - CONST.CAN_H / 2).toFixed(1) + 'px)';
      }
```

- [ ] **Step 3: The can3d intro filter**

In `can3d.js`, in the render function, immediately before the per-slot loop that starts with `const r = s.el.getBoundingClientRect();` (~line 206), compute once per frame:

```js
  const introOnly = document.body.classList.contains('intro');
```

and as the FIRST line inside the slot loop:

```js
    if (introOnly && s.role !== 'intro') continue;
```

Then check how roles pick camera framing (`grep -n "role" can3d.js`). If framing switches on `'hero'`/`'stage'`/`'sku'` with no default that fits, map `'intro'` to the same framing as `'sku'` (a contained product shot). Bump the cache-buster: `can3d.js?v=19` in `index.html`.

- [ ] **Step 4: Verify**

Run: `node oracle/intro.mjs && node oracle/api.mjs` — both exit 0.
Serve `python3 -m http.server 8000`: on the reveal screen the cursor circle uncovers the accent-tinted underlayer with the 3D can centered in it and following with lag; the hero can does NOT appear through the hole; after wheel-exit the hero can renders normally again (the `tempo:slots-changed` recollect).

- [ ] **Step 5: Commit**

```bash
git add intro.js can3d.js index.html
git commit -m "the reveal: a masked circle chases the cursor and the can rides under it"
```

---

### Task 4: Headless battery, docs, full gate

**Files:**
- Create: `oracle/verify-intro.mjs`
- Modify: `README.md` (intro paragraph in "What this example proves", tests section line)

**Interfaces:**
- Consumes: everything above; the battery drives the real page.
- Produces: the repeatable gate `node oracle/verify-intro.mjs` (requires playwright + a server on :8000).

- [ ] **Step 1: Resolve a Playwright runtime**

```bash
node -e "import('playwright').then(()=>console.log('playwright OK'))" 2>/dev/null \
  || npm i -g playwright && npx playwright install chromium
```
(A prior session ran Playwright Chromium on this box — SwiftShader flags below are proven. Keep installs global/home-cache; nothing enters the tree — the repo deliberately keeps package state out.)

- [ ] **Step 2: Write the battery**

Create `oracle/verify-intro.mjs` — bounded checks, exits nonzero on any failure:

```js
// oracle/verify-intro.mjs — drives the intro in headless Chromium.
// Run: python3 -m http.server 8000 &  then  node oracle/verify-intro.mjs
import { chromium } from 'playwright'

let failures = 0
const check = (ok, name) => { console.log((ok ? 'ok ' : 'FAIL ') + name); if (!ok) failures++ }
const URL = 'http://localhost:8000/'
const ARGS = ['--use-gl=angle', '--enable-unsafe-swiftshader']

const browser = await chromium.launch({ args: ARGS })

// ── desktop run ──
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.goto(URL)
  const C = await page.evaluate(() => TempoIntro.CONST)

  // loader mid-flight: counter and fill agree (both derive from progress)
  await page.waitForTimeout(C.T_LOAD * 0.5)
  const mid = await page.evaluate(() => ({
    n: parseInt(document.getElementById('introCount').textContent, 10),
    w: parseFloat(document.getElementById('introFillRect').getAttribute('width')),
    pills: document.querySelectorAll('.intro__pill').length,
  }))
  check(mid.n >= 20 && mid.n <= 90, `mid-load counter in 20..90 (got ${mid.n})`)
  check(Math.abs((mid.w / C.FILL_W) * 100 - mid.n) <= 3, `fill width tracks the counter (±3)`)
  check(mid.pills >= 1, `pills are spawning (got ${mid.pills})`)

  // reveal reached, canvas live
  await page.waitForSelector('.intro--reveal', { timeout: C.T_LOAD + C.T_ZOOM + 3000 })
  await page.waitForSelector('body.webgl', { timeout: 15000 })
  check(true, 'reveal phase + webgl reached')

  // the mask follows the cursor; the can slot rides with it
  await page.mouse.move(430, 450)
  await page.waitForTimeout(600)
  const a = await page.evaluate(() => ({
    mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
    can: document.getElementById('introCan').getBoundingClientRect().left,
  }))
  await page.mouse.move(1000, 450)
  await page.waitForTimeout(600)
  const b = await page.evaluate(() => ({
    mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
    can: document.getElementById('introCan').getBoundingClientRect().left,
  }))
  check(Math.abs(a.mx - 430) < 60 && Math.abs(b.mx - 1000) < 60, `mask x eases to the cursor (${a.mx} → ${b.mx})`)
  check(b.can - a.can > 400, `can slot follows the cursor (${a.can} → ${b.can})`)

  // exit on wheel: intro gone, page unlocked, no horizontal overflow
  await page.mouse.wheel(0, 120)
  await page.waitForTimeout(C.T_EXIT + 300)
  const post = await page.evaluate(() => ({
    intro: !!document.getElementById('intro'),
    htmlClass: document.documentElement.classList.contains('intro'),
    scrollY: window.scrollY,
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    hero: document.querySelector('.hero__title').getBoundingClientRect().top,
  }))
  check(!post.intro && !post.htmlClass, 'intro removed after wheel exit')
  check(post.scrollY === 0, 'page rests at the top')
  check(post.overflow === 0, `no horizontal overflow (delta ${post.overflow})`)
  check(post.hero >= 0 && post.hero < 900, 'hero title on screen')
  await page.close()
}

// ── reduced motion: exits by itself, no interaction ──
{
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto(URL)
  const C = await page.evaluate(() => TempoIntro.CONST)
  await page.waitForTimeout(C.T_REDUCED + C.T_EXIT + 600)
  check(await page.evaluate(() => !document.getElementById('intro')), 'reduced motion self-dismisses')
  await page.close()
}

// ── mobile: shrink-to-fit gate, auto-drift, overflow ──
{
  const page = await browser.newPage({
    viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true,
  })
  await page.goto(URL)
  const C = await page.evaluate(() => TempoIntro.CONST)
  const iw = await page.evaluate(() => window.innerWidth)
  check(iw === 390, `innerWidth == viewport (${iw}) — no shrink-to-fit zoom`)
  await page.waitForSelector('.intro--reveal', { timeout: C.T_LOAD + C.T_ZOOM + 3000 })
  await page.waitForTimeout(500)
  const d1 = await page.evaluate(() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')))
  await page.waitForTimeout(900)
  const d2 = await page.evaluate(() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')))
  check(Math.abs(d2 - d1) > 8, `auto-drift moves the mask (${d1.toFixed(0)} → ${d2.toFixed(0)})`)
  const ow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
  check(ow === 0, `no mobile horizontal overflow (delta ${ow})`)
  await page.close()
}

await browser.close()
process.exit(failures ? 1 : 0)
```

- [ ] **Step 3: Run the battery**

```bash
python3 -m http.server 8000 >/dev/null 2>&1 &
node oracle/verify-intro.mjs; kill %1
```
Expected: every line `ok …`, exit 0. If the framing of the intro can looks wrong in a debug screenshot (`page.screenshot`), adjust the `'intro'` role mapping from Task 3 and re-run.

- [ ] **Step 4: README**

In "What this example proves", add a third bolded paragraph after "Honest hydration":

```markdown
**A choreographed intro that can't brick the page.** The loader, logo zoom and
cursor-reveal are pure theatre on a pure timeline (`window.TempoIntro`,
oracle-tested) layered over the same one-canvas 3D pipeline as the rest of the
site. No JS, a failed script, or `prefers-reduced-motion` all land on the plain
page — the overlay only exists between a pre-paint class and its watchdog.
```

In the Tests section, add: `node oracle/intro.mjs` (timeline units) and `node oracle/verify-intro.mjs` (headless battery, needs playwright + `python3 -m http.server 8000`).

- [ ] **Step 5: Full gate + commit**

```bash
node oracle/intro.mjs && node oracle/api.mjs
cd motoko && "$HOME/.cache/mops/moc/1.4.1/moc" -r $(mops sources) test/units.test.mo && cd ..
git add oracle/verify-intro.mjs README.md
git commit -m "the intro battery: counter-fill agreement, cursor chase, drift, exits and overflow under headless chromium"
```
