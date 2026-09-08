// oracle/scroll.mjs — unit-tests the pure glide math of the damped scroll.
// Run: node oracle/scroll.mjs   (exits nonzero on any failure)
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
let failures = 0
const check = (ok, name) => { console.log((ok ? 'ok ' : 'FAIL ') + name); if (!ok) failures++ }

// Browser-enough globals: boot() must bail cleanly without a document body.
globalThis.window = globalThis
globalThis.document = { documentElement: { classList: { contains: () => false } }, body: undefined }
globalThis.matchMedia = () => ({ matches: false })

new Function(readFileSync(join(root, 'scroll.js'), 'utf8'))()
const S = globalThis.TempoScroll
check(!!S && typeof S.glideStep === 'function', 'TempoScroll.glideStep exposed')
const { MAX_V, TAU, SETTLE } = S.CONST

// a huge flick is velocity-capped: one full second moves at most MAX_V viewports
check(S.glideStep(0, 1e6, 1000, 900) === MAX_V * 900, 'glide is velocity-capped at MAX_V viewports/second')
// the cap is framerate-independent while it binds
check(Math.abs(S.glideStep(S.glideStep(0, 1e6, 16, 900), 1e6, 16, 900) - S.glideStep(0, 1e6, 32, 900)) < 1e-9,
  'capped glide: two 16ms steps land where one 32ms step does')
// never overshoots, however large the step
check(S.glideStep(0, 10, 60000, 900) === 10, 'glide never overshoots the target')
// the exponential tail snaps instead of creeping forever
check(S.glideStep(0, SETTLE - 0.1, 16, 900) === SETTLE - 0.1, 'tail inside SETTLE snaps to the target')
// gliding back up obeys the same cap
check(S.glideStep(5000, 0, 1000, 900) === 5000 - MAX_V * 900, 'upward glide is capped identically')
// short frames move less than the cap when the target is near
const near = S.glideStep(0, 100, 16, 900)
check(near > 0 && near < 100 && near < (MAX_V * 900 * 16) / 1000 + 1e-9, 'near targets ease in under the cap')


// ── retarget: wheel input feeds the target under a lead bound ──
const R = S.retarget, LEAD = S.CONST.MAX_LEAD
check(typeof R === 'function' && typeof LEAD === 'number', 'TempoScroll.retarget + MAX_LEAD exposed')
// a single notch is pure damped gain — the bound never touches it
check(R(800, 800, 120, 900) === 800 + 120 * S.CONST.WHEEL_GAIN, 'one notch adds its damped distance')
// pile on notches: the target can never owe more than MAX_LEAD viewports
let tgt = 800
for (let i = 0; i < 60; i++) tgt = R(tgt, 800, 160, 900)
check(tgt === 800 + LEAD * 900, `a burst is bounded at MAX_LEAD viewports of backlog (${tgt - 800}px)`)
check(LEAD * 900 < 900 + 1e-9, 'the backlog bound is under one viewport')
// the page catching up re-opens headroom — sustained scrolling still flows
check(R(1500, 1400, 160, 900) > 1500, 'headroom re-opens as the page catches up')
// reversal drops the backlog: one up-notch acts NOW, not after the queue
const rev = R(3000, 900, -120, 900)
check(rev <= 900, `an opposing notch collapses the backlog (target ${rev} <= current 900)`)
check(rev === 900 - 120 * S.CONST.WHEEL_GAIN, 'the opposing notch keeps its own damped distance')
// same direction keeps the queue
check(R(1000, 900, 120, 900) === 1000 + 120 * S.CONST.WHEEL_GAIN, 'same-direction input extends the queue')
// upward glide is bounded identically
let up = 5000
for (let i = 0; i < 60; i++) up = R(up, 5000, -160, 900)
check(up === 5000 - LEAD * 900, 'the bound holds symmetrically going up')

process.exit(failures ? 1 : 0)
