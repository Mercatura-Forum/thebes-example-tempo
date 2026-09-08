// oracle/street.mjs — unit-tests the pure Cairo-street simulation.
// Run: node oracle/street.mjs   (exits nonzero on any failure)
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { CONST, followK, joyVec, resolveCollision, stepMover, nextMode, animFor, turnStep, swoopTau } from '../street-sim.js'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
let failures = 0
const check = (ok, name) => { console.log((ok ? 'ok ' : 'FAIL ') + name); if (!ok) failures++ }

const LAYOUT = JSON.parse(readFileSync(join(root, 'src-model', 'tools', 'street_layout.json'), 'utf8'))
const BOUNDS = LAYOUT.bounds

// ── joystick ──
check(joyVec(0, 0, 100).x === 0 && joyVec(0, 0, 100).z === 0, 'joystick at rest is zero')
check(joyVec(10, 0, 100).x === 0, 'inside the deadzone is zero')
const jv = joyVec(300, 0, 100)
check(Math.abs(jv.x - 1) < 1e-9 && jv.z === 0, 'past full throw clamps to unit')
const jd = joyVec(60, 60, 100)
check(Math.abs(Math.hypot(jd.x, jd.z) - Math.min(1, Math.hypot(60, 60) / 100)) < 1e-9, 'diagonal keeps its magnitude')

// ── integrator ──
const still = { x: 0, z: 0 }
const run = (dts) => {
  let p = { x: 0, z: 0 }, v = { x: 0, z: 0 }
  for (const dt of dts) ({ pos: p, vel: v } = stepMover(p, v, { x: 1, z: 0 }, dt, [], BOUNDS))
  return { p, v }
}
const a = run([16, 16]), b = run([32])
check(Math.abs(a.p.x - b.p.x) < 1e-9, 'dt split is exact: 16+16 lands where 32 does')
const long = run([4000])
check(Math.abs(long.v.x - CONST.SPEED) < 0.01, 'velocity converges to SPEED and never beyond')
check(long.p.x <= BOUNDS.x[1] - CONST.RADIUS + 1e-9, 'bounds clamp holds at full run')

// ── collision ──
const wall = [{ x: [2, 2.1], z: [-5, 5] }]   // a thin wall
let p1 = { x: 0, z: 0 }, v1 = { x: 0, z: 0 }
;({ pos: p1 } = stepMover(p1, v1, { x: 1, z: 0 }, 1000, wall, BOUNDS))
check(p1.x <= 2 - CONST.RADIUS + 1e-6, `a 1000ms frame cannot tunnel a thin wall (stopped at ${p1.x.toFixed(2)})`)
let p2 = { x: 1.4, z: 0 }, v2 = { x: 0, z: 0 }
;({ pos: p2 } = stepMover(p2, v2, { x: 0.7071, z: 0.7071 }, 800, wall, BOUNDS))
check(p2.x <= 2 - CONST.RADIUS + 1e-6 && p2.z > 0.8, 'the wall blocks x but the player slides along z')
const inside = resolveCollision({ x: 2.05, z: 0 }, CONST.RADIUS, wall)
check(inside.x <= 2 - CONST.RADIUS + 1e-6 || inside.x >= 2.1 + CONST.RADIUS - 1e-6, 'a centre inside the box is pushed out')

// ── the real street: spawn is clear, koshk is reachable ──
const spawnHit = resolveCollision({ x: LAYOUT.spawn.x, z: LAYOUT.spawn.z }, CONST.RADIUS, LAYOUT.colliders)
check(Math.abs(spawnHit.x - LAYOUT.spawn.x) < 1e-9 && Math.abs(spawnHit.z - LAYOUT.spawn.z) < 1e-9, 'spawn point stands clear of every collider')
const trigHit = resolveCollision({ x: LAYOUT.koshk.trigger.x, z: LAYOUT.koshk.trigger.z }, CONST.RADIUS, LAYOUT.colliders)
check(Math.abs(trigHit.x - LAYOUT.koshk.trigger.x) < 1e-9 && Math.abs(trigHit.z - LAYOUT.koshk.trigger.z) < 1e-9, 'the koshk trigger spot is standable')

// ── focus state machine ──
const T = { x: 0, z: 0, r: 2 }
check(nextMode('roam', { x: 3, z: 0 }, T, false) === 'roam', 'far away stays roam')
check(nextMode('roam', { x: 1.5, z: 0 }, T, false) === 'focus', 'inside the trigger engages focus')
check(nextMode('focus', { x: 2.2, z: 0 }, T, false) === 'focus', 'hysteresis: just outside the ring holds focus')
check(nextMode('focus', { x: 2.6, z: 0 }, T, false) === 'roam', 'past the hysteresis ring releases to roam')
check(nextMode('focus', { x: 0.5, z: 0 }, T, true) === 'roam', 'an explicit leave always releases')

// ── followK sanity (shared discipline with the intro) ──
check(followK(16, 120) > 0 && followK(16, 120) < 1, 'followK stays in (0,1)')

// ── animFor: action selection never flickers at a boundary ──
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


// ── turnStep: the runner banks, never snaps ──
const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a))
check(Math.abs(turnStep(0, 0, 16, 90)) < 1e-12, 'no turn needed is no turn')
const t1 = turnStep(0, 1, 16, 90)
check(t1 > 0 && t1 < 1, 'a step moves toward the target without overshooting')
let th = 0
for (let i = 0; i < 200; i++) th = turnStep(th, 2.5, 16, 90)
check(Math.abs(th - 2.5) < 1e-6, 'repeated steps converge on the target')
const split = turnStep(turnStep(0.4, -2.9, 16, 90), -2.9, 16, 90)
const whole = turnStep(0.4, -2.9, 32, 90)
check(Math.abs(wrap(split - whole)) < 1e-9, 'dt split is exact: 16+16 lands where 32 does (turn)')
const acrossPi = turnStep(3.0, -3.0, 40, 90)
check(acrossPi > 3.0 || acrossPi < -3.0, 'crossing ±π takes the short arc through π, not the long way round')
check(Math.abs(wrap(turnStep(-3.1, 3.1, 4000, 90) - 3.1)) < 1e-6, 'a long dt settles exactly on a wrapped target')

// ── swoopTau: the entrance camera eases from establishing shot to follow ──
check(swoopTau(0) === CONST.SWOOP.TAU, 'at entry the camera follows on the swoop tau')
check(swoopTau(CONST.SWOOP.MS) === CONST.CAM_TAU, 'after the swoop the camera follows on the roam tau')
check(swoopTau(CONST.SWOOP.MS * 9) === CONST.CAM_TAU, 'long after entry nothing drifts')
let mono = true
for (let e = 0; e < CONST.SWOOP.MS; e += 100) if (swoopTau(e + 100) > swoopTau(e)) mono = false
check(mono, 'the swoop tau only ever tightens')
check(swoopTau(CONST.SWOOP.MS / 2) > CONST.CAM_TAU, 'mid-swoop the camera is still easing')

// ── placement: the spawn has breathing room, not just standing room ──
const clearance = LAYOUT.colliders.reduce((min, b) => {
  const cx = Math.max(b.x[0], Math.min(LAYOUT.spawn.x, b.x[1]))
  const cz = Math.max(b.z[0], Math.min(LAYOUT.spawn.z, b.z[1]))
  return Math.min(min, Math.hypot(LAYOUT.spawn.x - cx, LAYOUT.spawn.z - cz))
}, Infinity)
check(clearance >= 1.0, `spawn stands >= 1m clear of every collider (${clearance.toFixed(2)}m)`)

process.exit(failures ? 1 : 0)
