/* ============================================================
   TEMPO — the page moves at its own tempo. A wheel-driven damped
   scroll: each notch feeds a target, and the page GLIDES toward it,
   velocity-capped at MAX_V viewports/second — a violent flick
   becomes a glide, so models load in and the design gets its beat.
   Touch, keyboard, scrollbar and anchor scrolling stay native (the
   page's CSS scroll-behavior:smooth already softens those); ctrl+
   wheel (pinch zoom) passes through; inner scrollables (drawers)
   scroll natively; reduced-motion users are never hijacked.
   The glide math is pure and exposed for the node oracle.
   ============================================================ */
(function () {
  'use strict';

  const CONST = {
    WHEEL_GAIN: 0.9, // wheel notch → target distance (1 = native)
    MAX_V: 1.4,      // viewports per second — the speed of appreciation
    TAU: 150,        // ms smoothing toward the target
    SETTLE: 0.5,     // px — snap-and-stop threshold on the exponential tail
  };

  // Pure: one frame of the glide — exponential approach to the target,
  // clamped to the velocity cap, snapping once inside SETTLE so the tail
  // never creeps. Never overshoots the target.
  function glideStep(current, target, dt, vh) {
    let d = (target - current) * (1 - Math.exp(-dt / CONST.TAU));
    const cap = (CONST.MAX_V * vh * dt) / 1000;
    if (d > cap) d = cap; else if (d < -cap) d = -cap;
    const next = current + d;
    return Math.abs(target - next) < CONST.SETTLE ? target : next;
  }

  window.TempoScroll = { CONST, glideStep };

  function boot() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    let target = 0, current = 0, written = -1, active = false, prev = 0;

    // the ceiling: the document's own end, and the intro's one-viewport pin
    // while its exit curtain is running (state.scrollLimit, set by intro.js)
    function limit() {
      const lim = (window.TempoIntro && window.TempoIntro.state.scrollLimit) || Infinity;
      const max = document.documentElement.scrollHeight - window.innerHeight;
      return Math.max(0, Math.min(lim, max));
    }

    // wheel over a scrollable drawer/panel that can still move → native
    function innerScrolls(node, dy) {
      for (let el = node; el && el !== document.body && el.nodeType === 1; el = el.parentElement) {
        const cs = getComputedStyle(el);
        if (/(auto|scroll)/.test(cs.overflowY) && el.scrollHeight > el.clientHeight + 1) {
          if (dy < 0 ? el.scrollTop > 0 : el.scrollTop + el.clientHeight < el.scrollHeight - 1) return true;
        }
      }
      return false;
    }

    function frame(now) {
      const dt = prev ? Math.min(now - prev, 100) : 16;
      prev = now;
      const actual = window.scrollY;
      // someone else moved the page (anchor click, intro pin, handoff,
      // scrollbar drag) — adopt their position and go idle, never fight
      if (written >= 0 && Math.abs(actual - written) > 1) {
        current = target = actual; written = -1; active = false; prev = 0;
        return;
      }
      target = Math.max(0, Math.min(target, limit()));
      current = Math.max(0, glideStep(current, target, dt, window.innerHeight));
      window.scrollTo({ top: current, behavior: 'instant' });
      written = window.scrollY; // the browser may clamp or round our write
      if (current === target) { written = -1; active = false; prev = 0; return; }
      requestAnimationFrame(frame);
    }

    window.addEventListener('wheel', function (e) {
      if (e.ctrlKey || e.defaultPrevented) return;  // pinch zoom stays native
      if (document.documentElement.classList.contains('intro-lock')) return; // page locked; intro owns the wheel
      let dy = e.deltaY;
      if (!dy) return;
      if (e.deltaMode === 1) dy *= 16; else if (e.deltaMode === 2) dy *= window.innerHeight;
      if (innerScrolls(e.target, dy)) return;
      e.preventDefault();
      if (!active) {
        active = true; prev = 0; written = -1;
        current = target = window.scrollY;
        requestAnimationFrame(frame);
      }
      target = Math.max(0, Math.min(target + dy * CONST.WHEEL_GAIN, limit()));
    }, { passive: false });
  }

  if (typeof document !== 'undefined' && document.body) boot();
})();
