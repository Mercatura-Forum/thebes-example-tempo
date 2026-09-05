/* ============================================================
   TEMPO — intro experience. Loader (liquid wordmark fill +
   0→100 counter + electrolyte pills) → logo zoom (clamped to
   the viewport so the whole word shows) → a black-hole lens
   that rides the cursor while the can chases it, a lazy beat
   behind, through the dark recess → a scroll that
   slides the intro up and the landing page rises in beneath.
   The timeline is pure and exposed for the node oracle.
   ============================================================ */
(function () {
  'use strict';

  const CONST = {
    T_LOAD: 4600,        // loader choreography ms (slow, liquid)
    T_ZOOM: 700,         // logo zoom ms
    T_REDUCED: 400,      // reduced-motion logo hold ms
    T_REDUCED_EXIT: 300, // reduced-motion fade-out ms
    // the wordmark is rendered at its REVEAL size and only ever scaled DOWN,
    // so the vector never upscales into a blurry raster. Loader shows it small
    // (LOGO_LOAD); the zoom grows it to native (LOGO_REVEAL), where the
    // transform is dropped entirely so it sits pixel-crisp.
    LOGO_LOAD: 0.54,
    LOGO_REVEAL: 1.0,
    MASK_R: 300,         // reveal lens radius px, desktop (scaled on narrow)
    CAN_W: 300,          // the can that chases the cursor behind the wall
    CAN_H: 560,
    LENS_TAU: 95,        // ms time constant — the hole snaps to the cursor
    CAN_TAU: 500,        // ms time constant — the can arrives a lazy beat later
    REST_R: 0.5,         // idle pupil — fraction of the full lens radius
    IDLE_AFTER: 400,     // ms of cursor stillness before the hole relaxes
    REST_TAU: 320,       // ms time constant — contraction is lazier than the dilate
    EXIT_MIN: 900,       // ms — the fastest the exit curtain may complete, however hard the flick
    PILL_EVERY: 360,     // ms between pill spawns
    PILL_MAX: 11,
    PILL_MAX_NARROW: 6,  // ≤940px spawns fewer
  };
  const ELECTROLYTES = ['Sodium', 'Potassium', 'Magnesium', 'Chloride'];

  // Wordmark fill geometry, in the SVG's own viewBox units (0 0 620 180).
  // The liquid line rises from the glyph baseline (TEXT_BOT) to its cap top
  // (TEXT_TOP) as progress goes 0→100, with a travelling sine meniscus.
  const VB_W = 620, VB_H = 180, TEXT_TOP = 44, TEXT_BOT = 134;
  const WAVE_A = 5.5, WAVE_N = 28, WAVE_CYCLES = 2.6;

  const easeInOutCubic = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
  const easeOutCubic = (u) => 1 - Math.pow(1 - u, 3);
  // Pure: exponential-smoothing gain for a dt-ms step toward a target.
  // Framerate independent — two 16ms steps land where one 32ms step does —
  // and always in (0,1), so the chase can never overshoot the cursor.
  const followK = (dt, tau) => 1 - Math.exp(-dt / tau);
  // Pure: the hole is a pupil — full radius while the cursor moves, resting
  // to a smaller one once the cursor has been still for IDLE_AFTER ms.
  const lensTarget = (sinceMove, full, rest) => (sinceMove < CONST.IDLE_AFTER ? full : rest);
  // Pure: the exit curtain's lift for one frame — follows the scroll DOWN at a
  // capped rate (the full lift takes at least EXIT_MIN however hard the flick),
  // follows it UP instantly (no gap ever opens), never lifts past the scroll.
  const slideStep = (shown, y, dt, vh) => (y < shown ? y : Math.min(y, shown + (vh * dt) / CONST.EXIT_MIN));

  // Pure: elapsed ms (+ reduced-motion flag) → what the screen shows.
  // 'done' only occurs on the reduced path; the normal reveal waits for
  // the user's scroll, which is an event, not a time.
  function timeline(t, reduced) {
    if (reduced) {
      return t < CONST.T_REDUCED
        ? { phase: 'load', progress: 100, zoom: CONST.LOGO_REVEAL }
        : { phase: 'done', progress: 100, zoom: CONST.LOGO_REVEAL };
    }
    if (t < CONST.T_LOAD) {
      return { phase: 'load', progress: 100 * easeInOutCubic(t / CONST.T_LOAD), zoom: CONST.LOGO_LOAD };
    }
    if (t < CONST.T_LOAD + CONST.T_ZOOM) {
      const u = (t - CONST.T_LOAD) / CONST.T_ZOOM;
      return { phase: 'zoom', progress: 100, zoom: CONST.LOGO_LOAD + (CONST.LOGO_REVEAL - CONST.LOGO_LOAD) * easeOutCubic(u) };
    }
    return { phase: 'reveal', progress: 100, zoom: CONST.LOGO_REVEAL };
  }

  // The liquid clip path for a given fill fraction + wave phase. Returns the
  // path 'd' and the current line height (exposed for the headless battery,
  // which asserts the liquid RISES rather than trusting the counter).
  function fillPath(progress, phase) {
    const p = Math.max(0, Math.min(100, progress)) / 100;
    const lineY = TEXT_BOT - (TEXT_BOT - TEXT_TOP) * p;
    const k = (Math.PI * 2 * WAVE_CYCLES) / VB_W;
    let d = 'M 0 ' + (lineY + WAVE_A * Math.sin(phase)).toFixed(2);
    for (let i = 1; i <= WAVE_N; i++) {
      const x = (VB_W * i) / WAVE_N;
      d += ' L ' + x.toFixed(1) + ' ' + (lineY + WAVE_A * Math.sin(k * x + phase)).toFixed(2);
    }
    d += ' L ' + VB_W + ' ' + VB_H + ' L 0 ' + VB_H + ' Z';
    return { d: d, lineY: lineY };
  }

  const state = { progress: 0, fillY: TEXT_BOT, phase: 'load' };
  window.TempoIntro = { CONST, timeline, fillPath, followK, lensTarget, slideStep, state };

  function boot() {
    const root = document.getElementById('intro');
    const under = document.getElementById('introUnder');
    const fillEl = document.getElementById('introFillPath');
    const count = document.getElementById('introCount');
    const pillBox = document.getElementById('introPills');
    const logo = root.querySelector('.intro__logo');
    const scrollBtn = document.getElementById('introScroll');
    const canSlot = document.getElementById('introCan');
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const narrow = window.matchMedia('(max-width: 940px)').matches;

    // a big porthole (drinkstill-style) that never eats the whole screen
    const maskR = narrow ? Math.round(window.innerWidth * 0.36)
                         : Math.min(CONST.MASK_R, Math.round(window.innerWidth * 0.24));
    const sf = narrow ? 0.62 : 1;
    const canW = Math.round(CONST.CAN_W * sf), canH = Math.round(CONST.CAN_H * sf);

    // intro-veil hides the chrome + shows the overlay (until finalize);
    // intro-canlock keeps the 3D canvas drawing ONLY the intro can (until the
    // slide starts and the hero can must render in beneath)
    document.body.classList.add('intro-veil', 'intro-canlock');
    window.scrollTo(0, 0);
    // the lens vars live on <html> — the sheet mask, the black-hole shadow
    // ring and the dark recess beneath all read the same hole
    const lensVars = document.documentElement.style;
    lensVars.setProperty('--mr', maskR + 'px');
    canSlot.style.width = canW + 'px';
    canSlot.style.height = canH + 'px';

    // the same static render the shop cards fall back to
    const fb = canSlot.querySelector('.can-fallback');
    if (fb) fb.src = 'assets/can_' + (document.documentElement.dataset.flavor || 'citrus') + '.png';

    let hasMouse = false, wavePhase = 0, prevFrame = 0;
    let mx = window.innerWidth / 2, my = window.innerHeight * 0.55, tx = mx, ty = my;
    let canX = window.innerWidth / 2, canY = window.innerHeight / 2;
    let lensR = maskR, lastMove = 0;
    window.addEventListener('mousemove', function (e) {
      hasMouse = true; tx = e.clientX; ty = e.clientY;
      lastMove = performance.now();
    }, { passive: true });

    let done = false, transitioning = false, revealed = false;
    let phaseSeen = 'load', pills = 0, lastPill = 0, spacer = null, shown = 0;
    let t0 = performance.now();

    function spawnPill(now) {
      const max = narrow ? CONST.PILL_MAX_NARROW : CONST.PILL_MAX;
      if (pills >= max || now - lastPill < CONST.PILL_EVERY) return;
      lastPill = now;
      const el = document.createElement('span');
      el.className = 'intro__pill';
      el.textContent = ELECTROLYTES[pills % ELECTROLYTES.length];
      el.style.left = (6 + Math.random() * 80) + 'vw';
      el.style.top = (14 + Math.random() * 66) + 'vh';
      el.style.setProperty('--rot', (Math.random() * 34 - 17).toFixed(1) + 'deg');
      el.addEventListener('animationend', function () { el.remove(); });
      pillBox.appendChild(el);
      pills++;
    }

    // Once the reveal lands, the intro becomes the top screen of a scrollable
    // page: a full-height spacer holds the landing page down, scroll is
    // unlocked, and the user's scroll slides the intro up while the hero
    // rises in beneath. No curtain, no separate page.
    function enterReveal() {
      if (revealed) return; revealed = true;
      spacer = document.createElement('div');
      spacer.className = 'intro__spacer';
      spacer.style.height = window.innerHeight + 'px';
      document.body.insertBefore(spacer, document.body.firstChild);
      document.documentElement.classList.remove('intro-lock'); // unlock scroll; keep the veil
      window.addEventListener('scroll', onScroll, { passive: true });
    }

    // the first scroll turns the reveal into a lift: the hole closes, the
    // paper backdrop drops away, and the real landing page (hero can + copy)
    // is made live so it rises in behind the sheet — not a blank page.
    function startSlide() {
      if (transitioning) return; transitioning = true;
      state.scrollLimit = window.innerHeight; // the damped scroll (scroll.js) honours the exit pin
      root.classList.add('intro--sliding');   // drops the mask → opaque sheet
      under.style.display = 'none';            // stop the backdrop covering the hero
      document.body.classList.remove('intro-canlock'); // hero can renders now
      document.dispatchEvent(new CustomEvent('tempo:slots-changed'));
      var r = document.querySelectorAll('.hero .reveal');
      for (var i = 0; i < r.length; i++) r[i].classList.add('in');
    }

    // the lift itself is driven from frame() at a capped pace; here we only
    // start the slide and pin the page at one viewport until the curtain is
    // done — so a hard flick can't skip past the hero
    function onScroll() {
      if (done) return;
      if (window.scrollY > 0) startSlide();
      const vh = window.innerHeight;
      if (window.scrollY > vh) window.scrollTo({ top: vh, behavior: 'instant' });
    }

    function finalize() {
      if (done) return; done = true;
      state.scrollLimit = null;
      window.removeEventListener('scroll', onScroll);
      const vh = window.innerHeight;
      const y = window.scrollY;
      document.documentElement.classList.remove('intro-veil', 'intro-lock');
      document.body.classList.remove('intro-veil', 'intro-canlock');
      lensVars.removeProperty('--mx'); lensVars.removeProperty('--my'); lensVars.removeProperty('--mr');
      root.remove();
      under.remove();
      if (spacer) spacer.remove();
      // the spacer held the page down by one viewport — drop that from the
      // scroll offset in the same tick so the hero doesn't jump ('instant'
      // sidesteps the page's scroll-behavior:smooth, which would animate this)
      window.scrollTo({ top: Math.max(0, y - vh), behavior: 'instant' });
      document.dispatchEvent(new CustomEvent('tempo:slots-changed'));
      document.dispatchEvent(new CustomEvent('tempo:intro-done'));
    }

    // reduced motion: no theatre — hold the filled logo briefly, fade, gone
    function quickExit() {
      if (done) return; done = true;
      root.classList.add('intro--gone');
      setTimeout(function () {
        document.documentElement.classList.remove('intro-veil', 'intro-lock');
        document.body.classList.remove('intro-veil', 'intro-canlock');
        lensVars.removeProperty('--mx'); lensVars.removeProperty('--my'); lensVars.removeProperty('--mr');
        root.remove();
        under.remove();
        document.dispatchEvent(new CustomEvent('tempo:slots-changed'));
        document.dispatchEvent(new CustomEvent('tempo:intro-done'));
      }, CONST.T_REDUCED_EXIT);
    }

    // A scroll/keypress/tap during the loader fast-forwards to the reveal;
    // during the reveal it's the natural scroll that drives the transition.
    function advance() {
      if (done || transitioning) return;
      const s = timeline(performance.now() - t0, reduced);
      if (s.phase === 'load' || s.phase === 'zoom') {
        t0 = performance.now() - (CONST.T_LOAD + CONST.T_ZOOM); // jump to reveal
      }
    }
    window.addEventListener('keydown', function (e) {
      if (e.code === 'Space' || e.code === 'ArrowDown' || e.code === 'PageDown') advance();
    });
    scrollBtn.addEventListener('click', function () {
      if (revealed) window.scrollTo({ top: window.innerHeight, behavior: 'smooth' });
      else advance();
    });
    // during the lock a wheel/touch can't scroll — use it to skip ahead
    window.addEventListener('wheel', function () { if (!revealed) advance(); }, { passive: true });
    let touchY = null;
    window.addEventListener('touchstart', function (e) { touchY = e.touches[0].clientY; }, { passive: true });
    window.addEventListener('touchmove', function (e) {
      if (!revealed && touchY !== null && touchY - e.touches[0].clientY > 24) advance();
    }, { passive: true });

    function frame(now) {
      if (done) return;
      const dt = prevFrame ? now - prevFrame : 16;
      prevFrame = now;
      const s = timeline(now - t0, reduced);
      state.phase = s.phase; state.progress = s.progress;

      wavePhase += dt * 0.005;
      const fp = fillPath(s.progress, wavePhase);
      fillEl.setAttribute('d', fp.d);
      state.fillY = fp.lineY;
      count.textContent = String(Math.round(s.progress));

      // loader/zoom scale DOWN from a full-size render (never up); at reveal
      // drop the transform entirely so the wordmark paints at native
      // resolution (crisp). CSS width is min(85vw,1180) so it always fits.
      if (s.phase === 'reveal' || s.phase === 'done') {
        if (logo.style.transform) logo.style.transform = '';
      } else {
        logo.style.transform = 'scale(' + s.zoom.toFixed(3) + ')';
      }

      if (s.phase === 'load' && !reduced) spawnPill(now);
      if (s.phase !== phaseSeen) {
        phaseSeen = s.phase;
        if (s.phase === 'zoom') root.classList.add('intro--zoom');
        if (s.phase === 'reveal') { root.classList.add('intro--reveal'); enterReveal(); }
        if (s.phase === 'done') { quickExit(); return; }
      }
      // the porthole snaps to the cursor; the can CHASES the same target on a
      // much slower time constant, so it trails a lazy beat behind the hole
      // and drifts into the darkness wherever the lens waits for it.
      if (s.phase === 'reveal' && !transitioning) {
        const cx = window.innerWidth / 2, cy = window.innerHeight / 2;
        if (!hasMouse) { // touch / not-yet-moved desktop: a gentle wander over the can
          tx = cx + window.innerWidth * 0.24 * Math.sin(now * 0.00045);
          ty = cy + window.innerHeight * 0.16 * Math.sin(now * 0.00032 + 1.7);
        }
        const kLens = followK(dt, CONST.LENS_TAU), kCan = followK(dt, CONST.CAN_TAU);
        mx += (tx - mx) * kLens;
        my += (ty - my) * kLens;
        lensVars.setProperty('--mx', mx.toFixed(1) + 'px');
        lensVars.setProperty('--my', my.toFixed(1) + 'px');
        // the pupil: full while the cursor moves (dilate fast), resting once it
        // stills (contract lazily). The wander never rests — it never stops.
        const rT = hasMouse ? lensTarget(now - lastMove, maskR, maskR * CONST.REST_R) : maskR;
        lensR += (rT - lensR) * followK(dt, rT > lensR ? CONST.LENS_TAU : CONST.REST_TAU);
        lensVars.setProperty('--mr', lensR.toFixed(1) + 'px');
        canX += (tx - canX) * kCan;
        canY += (ty - canY) * kCan;
        canSlot.style.transform = 'translate(' + (canX - canW / 2).toFixed(1) + 'px,' + (canY - canH / 2).toFixed(1) + 'px)';
      }
      // the exit is deliberate: the curtain follows a slow scroll 1:1 but a
      // hard flick just pins and waits — the lift completes at its own pace
      if (transitioning) {
        const vh = window.innerHeight;
        shown = slideStep(shown, Math.min(window.scrollY, vh), dt, vh);
        root.style.transform = 'translateY(' + (-shown).toFixed(1) + 'px)';
        if (shown >= vh - 0.5) { finalize(); return; }
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  if (typeof document !== 'undefined' && document.getElementById('intro')) boot();
})();
