/* ============================================================
   TEMPO — the Cairo street (section 05 made literal). An opt-in
   walkable koshk-corner diorama: portal click → full-bleed stage,
   WASD/arrows (touch joystick) steer a runner to the koshk, the
   camera eases into the fridge shelf, and tapping a can carries
   its flavor into the on-chain shop. Nothing beyond this module's
   few KB loads until the portal is tapped — the GLB, layout and
   draco decoder fetch on entry only, and EVERYTHING is disposed
   on leave. Pure sim lives in street-sim.js (oracle-shared).
   ============================================================ */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { CONST, followK, joyVec, stepMover, nextMode, animFor } from './street-sim.js';

const DRACO_PATH = 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/libs/draco/gltf/';
const FLAVOR_BY_SHELF = ['lime', 'berry', 'citrus']; // bottom → top
const state = { entered: false, ready: false, disposed: false, mode: 'roam', player: { x: 0, z: 0 }, anim: 'Idle' };
window.TempoStreet = { CONST, state, warp: null, canScreenPoints: null };

function el(tag, cls, parent, html) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (html) n.innerHTML = html;
  if (parent) parent.appendChild(n);
  return n;
}

/* ── fallback: no WebGL or reduced motion — the shelf as a flat panel ── */
function enterFlat(stage) {
  const p = el('div', 'street-flat', stage);
  el('img', 'street-flat__poster', p).src = 'assets/street/poster.webp';
  el('p', 'street-flat__title', p, 'The koshk shelf — take a flavor to the shop');
  const row = el('div', 'street-flat__row', p);
  ['citrus', 'berry', 'lime'].forEach((k) => {
    const b = el('button', 'btn btn--ghost', row, k);
    b.type = 'button';
    b.addEventListener('click', () => { pickFlavor(k); });
  });
}

function pickFlavor(k) {
  state.lastPick = k;
  if (window.TEMPO && window.TEMPO.setFlavor) window.TEMPO.setFlavor(k);
  leave();
  const shop = document.getElementById('shop');
  if (shop) shop.scrollIntoView({ behavior: 'smooth' });
}

/* ── stage lifecycle ── */
let stage = null, cleanup = [], savedY = 0;
function leave() {
  if (!stage) return;
  for (const fn of cleanup.splice(0)) { try { fn(); } catch (e) { /* dispose best-effort */ } }
  stage.remove();
  stage = null;
  document.documentElement.classList.remove('street-lock');
  // overflow:hidden clamped the scroll to 0 behind the stage — put the page
  // back where the visitor left it before anything else scrolls anywhere
  window.scrollTo({ top: savedY, behavior: 'instant' });
  state.entered = false;
  state.ready = false;
  state.disposed = true;
}

function enter() {
  if (stage) return;
  state.disposed = false;
  savedY = window.scrollY;
  document.documentElement.classList.add('street-lock');
  stage = el('div', 'street-stage', document.body);
  stage.id = 'streetStage';
  const leaveBtn = el('button', 'btn btn--ghost street-leave', stage, 'Leave the street');
  leaveBtn.type = 'button';
  leaveBtn.addEventListener('click', leave);
  const onKey = (e) => { if (e.code === 'Escape') leave(); };
  window.addEventListener('keydown', onKey);
  cleanup.push(() => window.removeEventListener('keydown', onKey));
  state.entered = true;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reduced || !document.body.classList.contains('webgl')) { enterFlat(stage); return; }
  boot3d().catch((err) => {
    if (window.console) console.warn('[street]', err);
    if (stage) { stage.querySelectorAll('canvas,.street-hint,.street-joy').forEach((n) => n.remove()); enterFlat(stage); }
  });
}

/* ── the world ── */
async function boot3d() {
  const hint = el('div', 'street-hint', stage, 'WASD / arrows — find the koshk');
  const canvas = el('canvas', 'street-canvas', stage);
  const joyBase = el('div', 'street-joy', stage);
  const joyThumb = el('div', 'street-joy__thumb', joyBase);

  const [layout, streetGlb, canGlb, runnerGlb] = await Promise.all([
    fetch('assets/street/layout.json?v=2').then((r) => r.json()),
    loadGlb('assets/street/street.glb?v=2', true),
    loadGlb('assets/tempo-can.glb?v=4', false),
    loadGlb('assets/street/runner.glb?v=1', true),
  ]);
  if (!stage) return; // left while loading

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xead7b7);
  scene.fog = new THREE.Fog(0xead7b7, 20, 44);

  const camera = new THREE.PerspectiveCamera(layout.camera.fov, 1, 0.1, 120);
  const resize = () => {
    renderer.setSize(window.innerWidth, window.innerHeight, false);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
  };
  resize();
  window.addEventListener('resize', resize);
  cleanup.push(() => window.removeEventListener('resize', resize));

  // golden hour: warm sky bounce + a low sun; the GLB's emissives (bulbs,
  // fridge glow, sign) carry the sparkle
  scene.add(new THREE.HemisphereLight(0xffdfa8, 0x8a7360, 0.85));
  const sun = new THREE.DirectionalLight(0xffc287, 1.5);
  sun.position.set(-7, 10, 5);
  scene.add(sun);
  scene.add(streetGlb.scene);

  // the shelf: three cans per shelf, one flavor per row, real label art
  const texLoader = new THREE.TextureLoader();
  const labels = {};
  ['citrus', 'berry', 'lime'].forEach((k) => {
    const t = texLoader.load('assets/label_' + k + '.png?v=5');
    t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.wrapS = THREE.RepeatWrapping;
    labels[k] = t;
  });
  const K = layout.koshk;
  const cans = new THREE.Group();
  const c = Math.cos(K.ry), s = Math.sin(K.ry);
  K.shelves.ys.forEach((y, row) => {
    const key = FLAVOR_BY_SHELF[row];
    K.shelves.slotsX.forEach((lx) => {
      const can = canGlb.scene.clone(true);
      can.traverse((o) => {
        if (!o.isMesh) return;
        if (o.material.name === 'Label') {
          o.material = new THREE.MeshStandardMaterial({ map: labels[key], roughness: 0.38, metalness: 0.15, side: o.material.side });
        } else {
          o.material = o.material.clone();
          o.material.metalness = 0.9; o.material.roughness = 0.3;
        }
      });
      const sc = K.shelves.canScale;
      can.scale.setScalar(sc);
      const lz = K.shelves.slotZ;
      can.position.set(K.x + lx * c + lz * s, y + 0.41, K.z - lx * s + lz * c);
      can.rotation.y = K.ry + Math.PI;
      can.userData.flavor = key;
      // a fat invisible hit proxy so taps are forgiving (the can itself is
      // ~9px wide on a phone); opacity 0 + no depth write renders nothing
      const proxy = new THREE.Mesh(
        new THREE.CylinderGeometry(0.09 / sc, 0.09 / sc, 2.6, 8),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
      );
      proxy.position.y = 1.0;
      can.add(proxy);
      cans.add(can);
    });
  });
  scene.add(cans);

  // the runner — the KayKit body in TEMPO paper and ink, three gaits
  const runner = runnerGlb.scene;
  scene.add(runner);
  const mixer = new THREE.AnimationMixer(runner);
  const actions = {};
  for (const clip of runnerGlb.animations) actions[clip.name] = mixer.clipAction(clip);
  if (!actions.Idle || !actions.Walk || !actions.Run) throw new Error('runner.glb missing a gait clip: ' + Object.keys(actions).join(','));
  actions.Idle.play();
  state.anim = 'Idle';

  // input: keys + touch joystick, mapped through the fixed camera basis
  const off = layout.camera.roamOffset;
  const fLen = Math.hypot(off[0], off[2]);
  const fwd = { x: -off[0] / fLen, z: -off[2] / fLen };
  const rgt = { x: -fwd.z, z: fwd.x };
  const keys = {};
  const onDown = (e) => {
    if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) {
      keys[e.code] = true; e.preventDefault();
    }
  };
  const onUp = (e) => { keys[e.code] = false; };
  window.addEventListener('keydown', onDown);
  window.addEventListener('keyup', onUp);
  cleanup.push(() => { window.removeEventListener('keydown', onDown); window.removeEventListener('keyup', onUp); });

  let joy = null; // {id, ox, oy, vx, vy}
  const onPD = (e) => {
    if (e.target.closest('.street-leave')) return;
    joy = { id: e.pointerId, ox: e.clientX, oy: e.clientY, vx: 0, vy: 0, moved: 0 };
    if (e.pointerType !== 'mouse') {
      joyBase.style.left = e.clientX + 'px'; joyBase.style.top = e.clientY + 'px';
      joyBase.classList.add('on');
    }
  };
  const onPM = (e) => {
    if (!joy || e.pointerId !== joy.id) return;
    joy.vx = e.clientX - joy.ox; joy.vy = e.clientY - joy.oy;
    joy.moved = Math.max(joy.moved, Math.hypot(joy.vx, joy.vy));
    joyThumb.style.transform = 'translate(' + Math.max(-40, Math.min(40, joy.vx)) + 'px,' + Math.max(-40, Math.min(40, joy.vy)) + 'px)';
  };
  const onPU = (e) => {
    if (!joy || e.pointerId !== joy.id) return;
    state.lastTap = { x: e.clientX, y: e.clientY, moved: joy.moved, mode: state.mode };
    if (joy.moved < 6 && state.mode === 'focus') pickAt(e.clientX, e.clientY);
    joy = null;
    joyBase.classList.remove('on');
    joyThumb.style.transform = '';
  };
  stage.addEventListener('pointerdown', onPD);
  window.addEventListener('pointermove', onPM);
  window.addEventListener('pointerup', onPU);
  cleanup.push(() => { window.removeEventListener('pointermove', onPM); window.removeEventListener('pointerup', onPU); });

  const raycaster = new THREE.Raycaster();
  function castFlavor(cx, cy) {
    raycaster.setFromCamera(new THREE.Vector2((cx / window.innerWidth) * 2 - 1, -(cy / window.innerHeight) * 2 + 1), camera);
    const hit = raycaster.intersectObjects(cans.children, true)[0];
    if (!hit) return null;
    let o = hit.object;
    while (o && !o.userData.flavor) o = o.parent;
    return o ? o.userData.flavor : null;
  }
  function pickAt(cx, cy) {
    const k = castFlavor(cx, cy);
    if (k) pickFlavor(k);
  }
  window.TempoStreet.__probe = (cx, cy) => {
    raycaster.setFromCamera(new THREE.Vector2((cx / window.innerWidth) * 2 - 1, -(cy / window.innerHeight) * 2 + 1), camera);
    return raycaster.intersectObjects(cans.children, true).slice(0, 6).map((h) => {
      let o = h.object;
      while (o && !o.userData.flavor) o = o.parent;
      return { obj: h.object.name || h.object.type, d: Number(h.distance.toFixed(3)), flavor: o ? o.userData.flavor : null };
    });
  };

  // sim state
  let pos = { x: layout.spawn.x, z: layout.spawn.z };
  let vel = { x: 0, z: 0 };
  let camPos = new THREE.Vector3(pos.x + off[0], off[1], pos.z + off[2]);
  let camLook = new THREE.Vector3(pos.x, 1.0, pos.z);
  let prev = 0;
  window.TempoStreet.warp = (x, z) => { pos.x = x; pos.z = z; };
  window.TempoStreet.canScreenPoints = () => cans.children.map((can) => {
    const v = can.position.clone(); v.y += 0.08;
    v.project(camera);
    return { key: can.userData.flavor, x: (v.x + 1) / 2 * window.innerWidth, y: (1 - v.y) / 2 * window.innerHeight };
  });

  renderer.setAnimationLoop((now) => {
    const dt = Math.min(prev ? now - prev : 16, 100);
    prev = now;

    let ix = 0, iz = 0;
    if (keys.KeyW || keys.ArrowUp) iz += 1;
    if (keys.KeyS || keys.ArrowDown) iz -= 1;
    if (keys.KeyA || keys.ArrowLeft) ix -= 1;
    if (keys.KeyD || keys.ArrowRight) ix += 1;
    if (joy && (joy.vx || joy.vy)) {
      const jv = joyVec(joy.vx, joy.vy, 56);
      ix += jv.x; iz -= jv.z;
    }
    let input = { x: fwd.x * iz + rgt.x * ix, z: fwd.z * iz + rgt.z * ix };
    const il = Math.hypot(input.x, input.z);
    if (il > 1) { input.x /= il; input.z /= il; }

    ({ pos, vel } = stepMover(pos, vel, input, dt, layout.colliders, layout.bounds));
    state.player.x = pos.x; state.player.z = pos.z;
    const speed = Math.hypot(vel.x, vel.z);
    runner.position.set(pos.x, 0, pos.z);
    if (speed > 0.3) runner.rotation.y = Math.atan2(vel.x, vel.z);
    const want = animFor(state.anim, speed);
    if (want !== state.anim) {
      actions[state.anim].fadeOut(0.2);
      actions[want].reset().fadeIn(0.2).play();
      state.anim = want;
    }
    // tie the stride to the ground speed so feet don't slide
    if (want !== 'Idle') actions[want].timeScale = Math.max(0.6, Math.min(1.6, speed / (want === 'Run' ? 3.4 : 1.4)));
    mixer.update(dt / 1000);

    const wasMode = state.mode;
    state.mode = nextMode(state.mode, pos, K.trigger, false);
    if (state.mode !== wasMode) {
      hint.textContent = state.mode === 'focus'
        ? 'Take a can — tap it to carry the flavor into the shop'
        : 'WASD / arrows — find the koshk';
      stage.classList.toggle('street-stage--focus', state.mode === 'focus');
    }

    const k = followK(dt, CONST.CAM_TAU);
    const camTarget = state.mode === 'focus'
      ? new THREE.Vector3(...K.focusCam.pos)
      : new THREE.Vector3(pos.x + off[0], off[1], pos.z + off[2]);
    camPos.lerp(camTarget, k);
    camLook.lerp(state.mode === 'focus' ? new THREE.Vector3(...K.focusCam.look) : new THREE.Vector3(pos.x, 1.0, pos.z), k);
    camera.position.copy(camPos);
    camera.lookAt(camLook);
    state.camDist = camPos.distanceTo(camTarget); // 0 ≈ settled (battery waits on this, not wall-clock)

    renderer.render(scene, camera);
    if (!state.ready) state.ready = true;
  });

  cleanup.push(() => {
    renderer.setAnimationLoop(null);
    mixer.stopAllAction(); mixer.uncacheRoot(runner);
    scene.traverse((o) => {
      if (o.isMesh) {
        o.geometry.dispose();
        (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => {
          for (const key of Object.keys(m)) { if (m[key] && m[key].isTexture) m[key].dispose(); }
          m.dispose();
        });
      }
    });
    Object.values(labels).forEach((t) => t.dispose());
    renderer.dispose();
  });
}

function loadGlb(url, draco) {
  return new Promise((resolve, reject) => {
    const loader = new GLTFLoader();
    if (draco) {
      const d = new DRACOLoader();
      d.setDecoderPath(DRACO_PATH);
      loader.setDRACOLoader(d);
    }
    loader.load(url, resolve, undefined, reject);
  });
}

/* ── the portal ── */
const btn = document.getElementById('streetEnter');
if (btn) btn.addEventListener('click', enter);
