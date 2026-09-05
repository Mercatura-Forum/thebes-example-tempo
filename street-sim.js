/* ============================================================
   TEMPO — Cairo street, the pure simulation. No DOM, no three:
   movement, collision, joystick math and the focus state machine,
   shared verbatim by the browser runtime (street.js) and the node
   oracle (oracle/street.mjs). Layout comes in as data — the sim
   knows nothing about any particular street.
   ============================================================ */

export const CONST = {
  SPEED: 3.4,        // m/s — a runner's easy pace
  ACCEL_TAU: 120,    // ms — velocity approach to the input direction
  RADIUS: 0.38,      // player capsule radius on the ground plane
  CAM_TAU: 240,      // ms — camera follow smoothing (runtime uses this)
  DEADZONE: 0.16,    // joystick: fraction of max throw that counts as rest
  FOCUS_EXIT: 1.25,  // hysteresis — leave focus only past trigger.r * this
  SUB_H: 8,          // ms — fixed integration quantum (no tunneling, exact dt-splits)
};

export const followK = (dt, tau) => 1 - Math.exp(-dt / tau);

const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);

// Raw joystick offset (px) → unit-clamped direction with a deadzone.
export function joyVec(dx, dy, max) {
  const len = Math.hypot(dx, dy);
  if (len < CONST.DEADZONE * max) return { x: 0, z: 0 };
  const s = Math.min(1, len / max) / (len || 1);
  return { x: dx * s, z: dy * s };
}

// Circle-vs-AABB push-out on the ground plane. Boxes: {x:[x0,x1], z:[z0,z1]}.
export function resolveCollision(p, r, boxes) {
  let x = p.x, z = p.z;
  for (const b of boxes) {
    const cx = clamp(x, b.x[0], b.x[1]);
    const cz = clamp(z, b.z[0], b.z[1]);
    const dx = x - cx, dz = z - cz;
    const d2 = dx * dx + dz * dz;
    if (d2 >= r * r) continue;
    if (d2 > 1e-12) {
      const d = Math.sqrt(d2);
      x = cx + (dx / d) * r;
      z = cz + (dz / d) * r;
    } else {
      // centre inside the box — escape through the shallowest face
      const pen = [
        { d: x - b.x[0] + r, x: b.x[0] - r, z: z },
        { d: b.x[1] - x + r, x: b.x[1] + r, z: z },
        { d: z - b.z[0] + r, x: x, z: b.z[0] - r },
        { d: b.z[1] - z + r, x: x, z: b.z[1] + r },
      ].sort((a, b2) => a.d - b2.d)[0];
      x = pen.x; z = pen.z;
    }
  }
  return { x, z };
}

// One frame of movement. Input is the desired unit direction (camera-mapped
// by the runtime). Integration runs in fixed SUB_H quanta so a huge dt can
// never tunnel through a wall, and any split of dt lands identically.
export function stepMover(pos, vel, input, dt, colliders, bounds) {
  let p = { x: pos.x, z: pos.z };
  let v = { x: vel.x, z: vel.z };
  let remaining = dt;
  while (remaining > 1e-9) {
    const h = Math.min(CONST.SUB_H, remaining);
    remaining -= h;
    const k = followK(h, CONST.ACCEL_TAU);
    v.x += (input.x * CONST.SPEED - v.x) * k;
    v.z += (input.z * CONST.SPEED - v.z) * k;
    p.x += (v.x * h) / 1000;
    p.z += (v.z * h) / 1000;
    p = resolveCollision(p, CONST.RADIUS, colliders);
    p.x = clamp(p.x, bounds.x[0] + CONST.RADIUS, bounds.x[1] - CONST.RADIUS);
    p.z = clamp(p.z, bounds.z[0] + CONST.RADIUS, bounds.z[1] - CONST.RADIUS);
  }
  return { pos: p, vel: v };
}

// roam → focus when inside the koshk trigger; focus → roam only on an
// explicit leave or past the hysteresis ring (no flicker at the boundary).
export function nextMode(mode, p, trigger, wantLeave) {
  const d = Math.hypot(p.x - trigger.x, p.z - trigger.z);
  if (mode === 'focus') return wantLeave || d > trigger.r * CONST.FOCUS_EXIT ? 'roam' : 'focus';
  return d < trigger.r ? 'focus' : 'roam';
}
