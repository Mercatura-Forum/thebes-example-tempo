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
    // Task 2 fills this in. Guarded so the oracle (and a stripped page)
    // loads the script with no side effects.
  }

  if (typeof document !== 'undefined' && document.getElementById('intro')) boot();
})();
