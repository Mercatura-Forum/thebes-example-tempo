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

process.exit(failures ? 1 : 0)
