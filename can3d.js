/* ============================================================
   TEMPO — 3D can (Three.js). ONE renderer + one full-viewport
   canvas draws the GLB model into every [data-can3d] slot on the
   page via scissor rectangles (hero, the pinned flavour stage,
   and each shop card). Falls back to a static render image per
   flavour if WebGL or the model is unavailable.
   ============================================================ */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// Slots are collected lazily: some (the shop cards) are built by app.js on
// DOMContentLoaded, after this module first runs. Re-collect on the DOM events
// so every [data-can3d] box is picked up.
let slots = [];
function collectSlots() {
  slots = Array.from(document.querySelectorAll('[data-can3d]')).map((el, i) => ({
    el, role: el.dataset.role || 'sku', flavor: el.dataset.flavor || null, phase: i * 2.1,
  }));
}

document.addEventListener('DOMContentLoaded', collectSlots);
window.addEventListener('load', collectSlots);

function fail(msg) {
  document.body.classList.remove('webgl');
  if (window.console) console.warn('[can3d] CSS/image fallback:', msg);
}

try { boot(); } catch (e) { fail(e && e.message ? e.message : e); }

function boot() {
  const canvas = document.createElement('canvas');
  canvas.id = 'canGlobal';
  Object.assign(canvas.style, {
    position: 'fixed', top: '0', left: '0', width: '100%', height: '100%',
    pointerEvents: 'none', zIndex: '40',
  });
  document.body.appendChild(canvas);

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
  renderer.autoClear = false;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.add(new THREE.HemisphereLight(0xffffff, 0x33302b, 0.5));
  const key = new THREE.DirectionalLight(0xffffff, 2.2); key.position.set(3, 6, 5); scene.add(key);
  const rim = new THREE.DirectionalLight(0xffffff, 1.1); rim.position.set(-4, 2, -3); scene.add(rim);

  const group = new THREE.Group();
  scene.add(group);

  const texLoader = new THREE.TextureLoader();
  const textures = {};
  ['citrus', 'berry', 'lime'].forEach((k) => {
    const t = texLoader.load('assets/label_' + k + '.png');
    t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.anisotropy = 8;
    t.wrapS = THREE.RepeatWrapping;   // UV wraps the full circumference; keep the seam clean
    textures[k] = t;
  });

  let labelMat = null, current = 'citrus', ready = false;
  let targetSpin = 0, spin = 0, targetTiltX = 0, targetTiltY = 0, tiltX = 0, tiltY = 0;

  new GLTFLoader().load('assets/tempo-can.glb', (gltf) => {
    gltf.scene.traverse((o) => {
      if (!o.isMesh || !o.material) return;
      const m = o.material;
      if (m.name === 'Label') { labelMat = m; m.map = textures.citrus; m.roughness = 0.42; m.metalness = 0.08; }
      else if (m.name === 'Metal') { m.metalness = 1.0; m.roughness = 0.26; m.envMapIntensity = 1.3; m.color = new THREE.Color(0xd7d9de); }
    });
    group.add(gltf.scene);
    ready = true;
    document.body.classList.add('webgl');
    register();
    resize();
    collectSlots();
    renderer.setAnimationLoop(frame);
  }, undefined, (err) => fail('glb: ' + (err && err.message ? err.message : 'load error')));

  function register() {
    window.TEMPO = window.TEMPO || {};
    window.TEMPO.can = {
      setFlavor(k) { if (textures[k]) current = k; },     // hero + stage follow the page
      setSpin(p) { targetSpin = p * Math.PI * 4; },        // two turns across the scrub
    };
    if (window.TEMPO.__pendingFlavor) current = window.TEMPO.__pendingFlavor;
  }

  if (!reduced && window.matchMedia('(pointer:fine)').matches) {
    window.addEventListener('mousemove', (e) => {
      targetTiltY = (e.clientX / window.innerWidth - 0.5) * 0.7;
      targetTiltX = (e.clientY / window.innerHeight - 0.5) * 0.4;
    });
  }

  function resize() { renderer.setSize(window.innerWidth, window.innerHeight, false); }
  window.addEventListener('resize', resize);

  const lerp = (a, b, t) => a + (b - a) * (reduced ? 1 : t);

  function frame(time) {
    if (!ready) return;
    spin = lerp(spin, targetSpin, 0.09);
    tiltX = lerp(tiltX, targetTiltX, 0.08);
    tiltY = lerp(tiltY, targetTiltY, 0.08);
    const idle = reduced ? 0 : time * 0.0004;
    const H = window.innerHeight, W = window.innerWidth;

    renderer.setScissorTest(false);
    renderer.clear(true, true, true);
    renderer.setScissorTest(true);

    for (const s of slots) {
      const r = s.el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2 || r.bottom <= 0 || r.top >= H || r.right <= 0 || r.left >= W) continue;
      const w = r.width, h = r.height, left = r.left, bottom = H - r.bottom;
      renderer.setViewport(left, bottom, w, h);
      renderer.setScissor(left, bottom, w, h);

      const dist = s.role === 'hero' ? 4.8 : s.role === 'stage' ? 5.0 : 5.6;
      camera.aspect = w / h;
      camera.position.set(0, 1, dist);
      camera.updateProjectionMatrix();
      camera.lookAt(0, 1, 0);

      let ry, rx = 0;
      if (s.role === 'stage') { ry = spin + tiltY + idle * 0.5; rx = tiltX * 0.5; }
      else if (s.role === 'hero') { ry = idle * 0.8 + tiltY * 0.4; rx = tiltX * 0.25; }
      else { ry = idle * 0.9 + s.phase; }
      group.rotation.set(rx * 0.6, ry, 0);

      const flavKey = s.flavor || current;
      if (labelMat && textures[flavKey]) { labelMat.map = textures[flavKey]; }

      renderer.render(scene, camera);
    }
    renderer.setScissorTest(false);
  }
}
