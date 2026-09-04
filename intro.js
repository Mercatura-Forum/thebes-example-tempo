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

    document.body.classList.add('intro-lock'); // proves boot to the head watchdog
    window.scrollTo(0, 0);
    sheet.style.setProperty('--mr', CONST.MASK_R + 'px');

    // the same static render the shop cards fall back to
    const fb = canSlot.querySelector('.can-fallback');
    if (fb) fb.src = 'assets/can_' + (document.documentElement.dataset.flavor || 'citrus') + '.png';

    const ring = document.createElement('div');
    ring.className = 'intro__ring';
    ring.style.width = ring.style.height = (CONST.MASK_R * 2) + 'px';
    root.appendChild(ring);

    let hasMouse = false, driftT = 0, prevFrame = 0;
    let mx = window.innerWidth / 2, my = window.innerHeight * 0.6, tx = mx, ty = my;
    window.addEventListener('mousemove', function (e) {
      hasMouse = true; tx = e.clientX; ty = e.clientY;
    }, { passive: true });

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
        document.documentElement.classList.remove('intro-lock');
        document.body.classList.remove('intro-lock');
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
      const dt = prevFrame ? now - prevFrame : 16;
      prevFrame = now;
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
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  if (typeof document !== 'undefined' && document.getElementById('intro')) boot();
})();
