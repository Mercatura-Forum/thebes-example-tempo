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
const { T_LOAD, T_ZOOM, T_REDUCED, LOGO_LOAD, LOGO_REVEAL } = I.CONST

// ── load phase ──
let s = I.timeline(0, false)
check(s.phase === 'load' && s.progress === 0 && s.zoom === LOGO_LOAD, 't=0 is load/0/LOGO_LOAD')
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
check(zMid > LOGO_LOAD && zMid < LOGO_REVEAL, 'zoom grows from loader to native through the phase')
prev = 0; mono = true
for (let i = 0; i <= 100; i++) {
  const z = I.timeline(T_LOAD + (T_ZOOM * i) / 100, false).zoom
  if (z < prev - 1e-9) mono = false
  prev = z
}
check(mono, 'zoom is monotonic')

// ── reveal ──
s = I.timeline(T_LOAD + T_ZOOM, false)
check(s.phase === 'reveal' && s.zoom === LOGO_REVEAL, 'reveal holds native scale')
check(I.timeline(T_LOAD + T_ZOOM + 60000, false).phase === 'reveal', 'reveal is unbounded')

// ── reduced motion ──
s = I.timeline(0, true)
check(s.phase === 'load' && s.progress === 100 && s.zoom === LOGO_REVEAL, 'reduced shows the filled logo at once')
check(I.timeline(T_REDUCED - 1, true).phase === 'load', 'reduced holds through T_REDUCED')
check(I.timeline(T_REDUCED, true).phase === 'done', 'reduced skips straight to done')

// ── counter is an integer 0..100 ──
let ints = true
for (let i = 0; i <= 50; i++) {
  const n = Math.round(I.timeline((T_LOAD * i) / 50, false).progress)
  if (!Number.isInteger(n) || n < 0 || n > 100) ints = false
}
check(ints, 'rounded counter stays in 0..100')

// ── liquid fill rises with progress (the wordmark fills bottom→top) ──
check(typeof I.fillPath === 'function', 'fillPath exposed')
let rises = true, prevY = Infinity
for (let p = 0; p <= 100; p += 5) {
  const y = I.fillPath(p, 0).lineY   // phase 0 → no wave offset, pure level
  if (y > prevY + 1e-9) rises = false // smaller y = higher liquid; must not drop
  prevY = y
}
check(rises, 'fill line rises monotonically as progress climbs')
check(I.fillPath(0, 0).lineY > I.fillPath(100, 0).lineY, 'empty sits below full')
check(I.fillPath(100, 0).d.indexOf('NaN') === -1, 'path is well-formed (no NaN)')

// ── the chase easing is framerate-independent exponential smoothing ──
check(typeof I.followK === 'function', 'followK exposed')
const stepTo = (x, dt, tau) => x + (100 - x) * I.followK(dt, tau)
let two = stepTo(stepTo(0, 16, 500), 16, 500)
check(Math.abs(two - stepTo(0, 32, 500)) < 1e-9, 'two 16ms steps land where one 32ms step does')
check(I.followK(16, 500) > 0 && I.followK(16, 500) < 1, 'k stays in (0,1) — the chase never overshoots')
check(I.followK(16, I.CONST.CAN_TAU) < I.followK(16, I.CONST.LENS_TAU), 'the can (slow tau) trails the lens (fast tau)')

// ── the hole is a pupil: full while the cursor moves, resting when it stills ──
check(typeof I.lensTarget === 'function', 'lensTarget exposed')
check(I.lensTarget(0, 300, 150) === 300 && I.lensTarget(I.CONST.IDLE_AFTER - 1, 300, 150) === 300,
  'hole holds full size while the cursor moves')
check(I.lensTarget(I.CONST.IDLE_AFTER, 300, 150) === 150, 'hole rests to the pupil once the cursor stills')

// ── the exit curtain: rate-capped down, instant up, never past the scroll ──
check(typeof I.slideStep === 'function', 'slideStep exposed')
check(I.slideStep(0, 5000, I.CONST.EXIT_MIN, 1000) === 1000, 'a full lift takes EXIT_MIN however hard the flick')
check(Math.abs(I.slideStep(I.slideStep(0, 800, 16, 1000), 800, 16, 1000) - I.slideStep(0, 800, 32, 1000)) < 1e-9,
  'curtain rate is framerate-independent')
check(I.slideStep(500, 200, 16, 1000) === 200, 'scrolling back up is followed instantly')
check(I.slideStep(100, 120, 500, 1000) === 120, 'curtain never lifts past the real scroll')

process.exit(failures ? 1 : 0)
