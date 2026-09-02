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
    clip: el.closest('[data-can-clip]'),
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

  // rig carries the hero lean for the WHOLE composition (can + splash together),
  // pivoted at the can's mid-height so it leans in place instead of sweeping
  // sideways. With rig z at 0 the pair of offsets cancels exactly, so the
  // stage and the shop cards render precisely as before.
  const rig = new THREE.Group();
  rig.position.set(0, 1, 0);
  scene.add(rig);
  const group = new THREE.Group();
  group.position.set(0, -1, 0);
  rig.add(group);
  // the splash rides the rig (leans with the can) but NOT the group: group.y
  // revolves continuously in the hero, and a revolving splash sweeps its long
  // arms through the slot edges — the scissor slices them into hard flat cuts
  const splashHolder = new THREE.Group();
  splashHolder.position.set(0, -1, 0);
  rig.add(splashHolder);

  const texLoader = new THREE.TextureLoader();
  const textures = {};
  ['citrus', 'berry', 'lime'].forEach((k) => {
    const t = texLoader.load('assets/label_' + k + '.png?v=5');
    t.colorSpace = THREE.SRGBColorSpace; t.flipY = false; t.anisotropy = 8;
    t.wrapS = THREE.RepeatWrapping;   // UV wraps the full circumference; keep the seam clean
    textures[k] = t;
  });

  let labelMat = null, current = 'citrus', ready = false;
  let targetSpin = 0, spin = 0, targetTiltX = 0, targetTiltY = 0, tiltX = 0, tiltY = 0;
  let targetRoll = 0, roll = 0;   // story rail: rotation tied to scroll travel
  let splash = null, splashMat = null;
  // hero slot rect in DEVICE pixels (gl_FragCoord space) for the edge feather
  const uSlot = { value: new THREE.Vector4(0, 0, 1, 1) };

  function tintSplash(k) {
    if (!splashMat) return;
    const f = window.TEMPO && window.TEMPO.flavors && window.TEMPO.flavors[k];
    const c = splashMat.color.set(f ? f.color : '#ff7a1a');
    const hsl = {};
    c.getHSL(hsl);
    // lighten but KEEP saturation — lerping to white desaturates, and
    // desaturated orange reads as mud, desaturated anything as smoke
    c.setHSL(hsl.h, hsl.s, Math.min(0.78, hsl.l + 0.24));
    // self-lit lift: sheets facing away from the key light otherwise pick up
    // the hemisphere's dark ground color and turn muddy
    splashMat.emissive.copy(c).multiplyScalar(0.35);
  }

  // Frozen fluid splash, hero slot only ("Water Splash" by Asfandyar Hesami,
  // CC-BY-4.0 — see NOTICE.md). The hero just shows the bare can if it fails.
  new GLTFLoader().load('assets/splash.glb?v=4', (g) => {
    splashMat = new THREE.MeshPhysicalMaterial({
      transparent: true, opacity: 0.5, roughness: 0.2, metalness: 0,
      envMapIntensity: 0.9, specularIntensity: 0.35, ior: 1.15,
      depthWrite: false, side: THREE.DoubleSide,
    });
    // screen-space edge feather: the splash arms are longer than any sane
    // framing can contain, so instead of letting the scissor slice them into
    // hard flat cuts, fade them out over the outer 12% of the hero slot —
    // every tail then ENDS the way the in-frame ones do, on any viewport
    splashMat.onBeforeCompile = (sh) => {
      sh.uniforms.uSlot = uSlot;
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <clipping_planes_pars_fragment>',
          '#include <clipping_planes_pars_fragment>\nuniform vec4 uSlot;')
        .replace('#include <dithering_fragment>', `#include <dithering_fragment>
          vec2 relF = (gl_FragCoord.xy - uSlot.xy) / uSlot.zw;
          vec2 dpxF = min(relF, 1.0 - relF) * uSlot.zw;
          float featherF = 0.12 * min(uSlot.z, uSlot.w);
          gl_FragColor.a *= smoothstep(0.0, featherF, min(dpxF.x, dpxF.y));`);
    };
    g.scene.traverse((o) => { if (o.isMesh) o.material = splashMat; });
    splash = g.scene;
    splash.visible = false;
    splash.scale.setScalar(1.22);      // reads bigger than the can
    // no local tilt: the splash leans with the whole rig so the can and the
    // water read as one tilted composition, not a straight can in a tilted splash
    splash.rotation.y = 1.1;           // base pose — keeps the wordmark clear, even under reduced motion
    splashHolder.add(splash);
    tintSplash(current);
  }, undefined, () => { if (window.console) console.warn('[can3d] splash unavailable'); });

  new GLTFLoader().load('assets/tempo-can.glb?v=4', (gltf) => {
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
      setFlavor(k) { if (textures[k]) { current = k; tintSplash(k); } },  // hero + stage follow the page
      setSpin(p) { targetSpin = p * Math.PI * 4; },        // two turns across the scrub
      setRoll(p) { targetRoll = p * Math.PI * 6; },        // three turns down the page
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
    roll = lerp(roll, targetRoll, 0.12);
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
      if (s.clip) {
        // clamp the scissor to the clip ancestor: the can slides out of view
        // at its edge (the story roller rolling off) instead of painting on
        const cr = s.clip.getBoundingClientRect();
        const x0 = Math.max(r.left, cr.left), x1 = Math.min(r.right, cr.right);
        const y0 = Math.max(r.top, cr.top), y1 = Math.min(r.bottom, cr.bottom);
        if (x1 - x0 < 1 || y1 - y0 < 1) continue;
        renderer.setScissor(x0, H - y1, x1 - x0, y1 - y0);
      } else {
        renderer.setScissor(left, bottom, w, h);
      }

      // hero: camera rides higher so the composition sits low in the slot —
      // the splash tails must END inside the frame (top included), never get
      // sliced by the scissor edge into a hard straight cut
      const dist = s.role === 'hero' ? 6.3 : s.role === 'stage' ? 5.0 : s.role === 'roll' ? 3.2 : 5.6;
      const cy = s.role === 'hero' ? 1.35 : 1;
      const cx = s.role === 'hero' ? 0.2 : 0;    // leaned mass sits up-right; recenter in the slot
      camera.fov = s.role === 'roll' ? 14 : 30;  // long lens: the lying can fills the slot without distortion
      camera.aspect = w / h;
      camera.position.set(cx, cy, dist);
      camera.updateProjectionMatrix();
      camera.lookAt(cx, cy, 0);

      let ry, rx = 0;
      if (s.role === 'stage') { ry = spin + tiltY + idle * 0.5; rx = tiltX * 0.5; }
      else if (s.role === 'hero') { ry = idle * 0.8 + tiltY * 0.4; rx = tiltX * 0.25; }
      else if (s.role === 'roll') { ry = roll; }         // rolling = spin about the lying axis
      else { ry = idle * 0.9 + s.phase; }
      group.rotation.set(rx * 0.6, ry, 0);
      // hero: lift the can so it sits centered in the swirl (splash stays put)
      group.position.y = s.role === 'hero' ? -0.7 : -1;
      // hero leans 26°; the story can lies fully on its side (90°) and rolls
      rig.rotation.z = s.role === 'hero' ? -0.45 : s.role === 'roll' ? Math.PI / 2 : 0;

      if (splash) {
        splash.visible = s.role === 'hero';
        if (splash.visible) {
          const pr = renderer.getPixelRatio();
          uSlot.value.set(left * pr, bottom * pr, w * pr, h * pr);
        }
        if (splash.visible && !reduced) {
          // oscillate around the vetted pose instead of a full orbit — a
          // continuous turn drags every thick tail through the slot edge
          // where the scissor slices it into a hard straight cut
          splash.rotation.y = 1.1 + Math.sin(time * 0.00035) * 0.2;
          splash.position.y = Math.sin(time * 0.0011) * 0.04;
          for (let i = 0; i < splash.children.length; i++)
            splash.children[i].rotation.y = Math.sin(time * 0.0007 + i * 2.1) * 0.06;
        }
      }

      const flavKey = s.flavor || current;
      if (labelMat && textures[flavKey]) { labelMat.map = textures[flavKey]; }

      renderer.render(scene, camera);
    }
    renderer.setScissorTest(false);
  }
}
