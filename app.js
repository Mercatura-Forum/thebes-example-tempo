/* ============================================================
   TEMPO — content + interaction layer (fictional demo brand)
   ============================================================ */
(function () {
  'use strict';

  /* ── Data (all original) ── */
  const FLAVORS = {
    citrus: {
      name: 'Citrus Strike', tag: 'Citrus', color: '#ff7a1a',
      head: 'Flavour 01 — the sprint',
      blurb: 'Blood orange and grapefruit with a clean saline edge. The one that tastes like the start line — bright, sharp, gone before the next rep.',
      spec: [['Sodium', '1000mg'], ['Potassium', '250mg'], ['Sugar', '0g'], ['Calories', '10']],
    },
    berry: {
      name: 'Arctic Berry', tag: 'Berry', color: '#5566ff',
      head: 'Flavour 02 — the long one',
      blurb: 'Dark blueberry and a whisper of mint, served cold-blue. Smooth enough for long, slow miles when you want flavour without the sting.',
      spec: [['Sodium', '1000mg'], ['Potassium', '250mg'], ['Sugar', '0g'], ['Calories', '10']],
    },
    lime: {
      name: 'Lime Charge', tag: 'Lime', color: '#2fbf5d',
      head: 'Flavour 03 — the heat',
      blurb: 'Kaffir lime and cucumber, green and almost savoury. Our most electrolyte-forward pour — built for heat, humidity and back-to-backs.',
      spec: [['Sodium', '1200mg'], ['Potassium', '300mg'], ['Sugar', '0g'], ['Calories', '10']],
    },
  };
  const FLAVOR_ORDER = ['citrus', 'berry', 'lime'];

  const FORMULA = [
    { icon: 'salt', h: 'Real sodium', p: 'A full gram per can — the dose endurance research actually points to, not a token pinch.' },
    { icon: 'drop', h: 'Fast uptake', p: 'A light glucose escort and the right osmolality move water into you, not through you.' },
    { icon: 'leaf', h: 'Nothing fake', p: 'No artificial colours, no sucralose, no mystery blend. You can read every line on the can.' },
    { icon: 'bolt', h: 'Zero sugar', p: 'Ten calories, no sugar crash — hydration that works whether you are racing or recovering.' },
  ];

  const INGREDIENTS = [
    { k: 'Sodium', n: '01', h: 'Sodium — the one that matters', p: 'You lose it by the gram in sweat, and it is what pulls water into your bloodstream. TEMPO carries a full 1000–1200mg per can, sourced from Red Sea salt.' },
    { k: 'Potassium', n: '02', h: 'Potassium', p: 'Partners with sodium to move fluid into your cells and keep muscles firing cleanly through the back half of a session.' },
    { k: 'Magnesium', n: '03', h: 'Magnesium', p: 'The mineral most of us run low on. It supports energy metabolism and helps quiet the late-session cramps before they start.' },
    { k: 'Chloride', n: '04', h: 'Chloride', p: 'The quiet half of salt. It keeps your fluid balance and blood pH steady while everything else is working hard.' },
    { k: 'Vitamin C', n: '05', h: 'Vitamin C + zinc', p: 'A small immune hedge for the day after a big effort, when your defences dip and a cold likes to sneak in.' },
    { k: 'Coconut', n: '06', h: 'Coconut water base', p: 'Our liquid foundation instead of plain water — naturally mineral-rich, faintly sweet, and easy on a working stomach.' },
  ];

  const TIMELINE = [
    { y: '2021', h: 'A bonk on the Sokhna road', p: 'Our founder cramped out of a race she should have finished, stared at a sugar-bomb sports drink, and started reading labels that night.' },
    { y: '2022', h: 'The kitchen-counter formula', p: 'Forty batches, one blender and a lot of salt later, the first drinkable version of TEMPO existed in three unlabelled bottles.' },
    { y: '2023', h: 'First cans, first run club', p: 'We printed 5,000 cans of Citrus Strike and handed most of them out at Friday-morning runs in Cairo. They came back for the recipe.' },
    { y: '2024', h: 'Arctic Berry & Lime Charge', p: 'Two new flavours, a real cannery, and a promise we still keep: nothing on the can we would not drink mid-race.' },
    { y: '2025', h: 'On the shelf, on the start line', p: 'Now in three cities and a few hundred gyms, cafés and bike shops — with the same one-gram-of-sodium backbone we started with.' },
  ];

  const PRESS = [
    { q: 'The rare electrolyte drink that dosed the sodium like it meant it. My legs noticed on the long ones.', by: 'The Morning Mile' },
    { q: 'Tastes like a premium soda, works like a serious hydration tab. That combination is genuinely hard to pull off.', by: 'Field & Court' },
    { q: 'Lime Charge got me through a brutal, humid half. No cramps, no sugar wall, no complaints.', by: 'Endurance Weekly' },
  ];

  const STOCKISTS = [
    { city: 'Cairo', meta: 'Cafés, gyms & bike shops from Zamalek to New Cairo', count: '38 spots' },
    { city: 'Alexandria', meta: 'Run clubs & cafés along the Corniche', count: '21 spots' },
    { city: 'El Gouna', meta: 'The tri club, marina cafés & kite beaches', count: '17 spots' },
  ];

  const SKUS = [
    { h: '4-Pack', desc: 'A short stack of one flavour. The easy way to find your pace.', price: '200', unit: '/ 4 cans', tag: '', featured: false },
    { h: '12-Case', desc: 'The training case. One flavour, twelve cans, best value per pour.', price: '540', unit: '/ 12 cans', tag: 'Most popular', featured: true },
    { h: 'Variety Case', desc: 'Four of each — Citrus Strike, Arctic Berry, Lime Charge. Meet all three.', price: '560', unit: '/ 12 cans', tag: '', featured: false },
  ];

  /* Tabler Icons (MIT) — see NOTICE.md */
  const ICONS = {
    salt: '<path d="M12 13v.01"/><path d="M10 16v.01"/><path d="M14 16v.01"/><path d="M7.5 8h9l-.281 -2.248a2 2 0 0 0 -1.985 -1.752h-4.468a2 2 0 0 0 -1.986 1.752l-.28 2.248z"/><path d="M7.5 8l-1.612 9.671a2 2 0 0 0 1.973 2.329h8.278a2 2 0 0 0 1.973 -2.329l-1.612 -9.671"/>',
    drop: '<path d="M7.502 19.423c2.602 2.105 6.395 2.105 8.996 0c2.602 -2.105 3.262 -5.708 1.566 -8.546l-4.89 -7.26c-.42 -.625 -1.287 -.803 -1.936 -.397a1.376 1.376 0 0 0 -.41 .397l-4.893 7.26c-1.695 2.838 -1.035 6.441 1.567 8.546z"/><path d="M5 14h14"/>',
    leaf: '<path d="M5 21c.5 -4.5 2.5 -8 7 -10"/><path d="M9 18c6.218 0 10.5 -3.288 11 -12v-2h-4.014c-9 0 -11.986 4 -12 9c0 1 0 3 2 5h3z"/>',
    bolt: '<path d="M13 3l0 7l6 0l-8 11l0 -7l-6 0l8 -11"/>',
    pin: '<path d="M9 11a3 3 0 1 0 6 0a3 3 0 0 0 -6 0"/><path d="M17.657 16.657l-4.243 4.243a2 2 0 0 1 -2.827 0l-4.244 -4.243a8 8 0 1 1 11.314 0z"/>',
  };
  const svg = (inner, cls) =>
    `<svg class="${cls || ''}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${inner}</svg>`;

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Shared namespace so the 3D module can register itself. */
  const TEMPO = (window.TEMPO = window.TEMPO || {});
  TEMPO.flavors = FLAVORS;
  TEMPO.order = FLAVOR_ORDER;

  const state = { flavor: 'citrus', cart: 0 };

  /* ── Static fallback image (shown only when WebGL is unavailable) ── */
  function updateFallbacks() {
    const src = 'assets/can_' + state.flavor + '.png?v=4';
    $$('.can-slot--hero .can-fallback, .can-slot--stage .can-fallback').forEach((img) => {
      if (img.getAttribute('src') !== src) img.setAttribute('src', src);
    });
  }

  /* ── Flavour switch — themes the whole page ── */
  function setFlavor(key) {
    if (!FLAVORS[key]) return;
    state.flavor = key;
    document.documentElement.setAttribute('data-flavor', key);
    updateFallbacks();
    updateFlavorCopy();
    TEMPO.__pendingFlavor = key;               // in case the 3D model is still loading
    if (TEMPO.can && TEMPO.can.setFlavor) TEMPO.can.setFlavor(key);
  }

  function updateFlavorCopy() {
    const f = FLAVORS[state.flavor];
    if ($('#flHead')) $('#flHead').textContent = f.head;
    if ($('#flName')) $('#flName').textContent = f.name;
    if ($('#flWord')) $('#flWord').textContent = f.name;
    if ($('#flBlurb')) $('#flBlurb').textContent = f.blurb;
    if ($('#flSpec')) $('#flSpec').innerHTML =
      f.spec.map((s) => '<li><span>' + s[0] + '</span><b>' + s[1] + '</b></li>').join('');
    $$('#flDots .fl-dot').forEach((d) => d.setAttribute('aria-selected', d.dataset.key === state.flavor));
  }

  /* ── Renderers ── */
  function renderFormula() {
    // --i places each card on the rotating ring (wide screens only); the ring
    // div is display:contents in the flat grid, so small screens see no change
    $('#formulaCards').innerHTML = '<div class="cards__ring">' + FORMULA.map((c, i) =>
      '<article class="card" style="--i:' + i + '">' + svg(ICONS[c.icon], 'card__icon') +
      '<h3>' + c.h + '</h3><p>' + c.p + '</p></article>').join('') + '</div>';
  }
  function renderDots() {
    $('#flDots').innerHTML = FLAVOR_ORDER.map((k) =>
      '<button class="fl-dot" role="tab" data-key="' + k + '" aria-selected="' + (k === state.flavor) +
      '" aria-label="' + FLAVORS[k].name + '"></button>').join('');
    $$('#flDots .fl-dot').forEach((d) => d.addEventListener('click', () => {
      const idx = FLAVOR_ORDER.indexOf(d.dataset.key);
      const track = $('#flavorTrack');
      const dist = track.offsetHeight - window.innerHeight;
      const top = trackTop() + (idx + 0.5) / FLAVOR_ORDER.length * dist;
      window.scrollTo({ top: top, behavior: prefersReduced ? 'auto' : 'smooth' });
    }));
  }
  function renderIngredients() {
    $('#ingTabs').innerHTML = INGREDIENTS.map((i, idx) =>
      '<button class="ing__tab" role="tab" data-idx="' + idx + '" aria-selected="' + (idx === 0) + '">' + i.k + '</button>').join('');
    const setPanel = (idx) => {
      const i = INGREDIENTS[idx];
      $('#ingBody').innerHTML = '<div class="ing__panel"><span class="ing__num">' + i.n + '</span></div>' +
        '<div class="ing__panel"><h3>' + i.h + '</h3><p>' + i.p + '</p></div>';
    };
    setPanel(0);
    $$('#ingTabs .ing__tab').forEach((btn) => btn.addEventListener('click', () => {
      $$('#ingTabs .ing__tab').forEach((b) => b.setAttribute('aria-selected', b === btn));
      setPanel(Number(btn.dataset.idx));
    }));
  }
  function renderTimeline() {
    $('#timeline').innerHTML = TIMELINE.map((t) =>
      '<li class="tl"><span class="tl__year">' + t.y + '</span>' +
      '<div class="tl__body"><h3>' + t.h + '</h3><p>' + t.p + '</p></div></li>').join('');
  }
  function renderPress() {
    $('#pressGrid').innerHTML = PRESS.map((p) =>
      '<blockquote class="press__card"><p>“' + p.q + '”</p><cite>' + p.by + '</cite></blockquote>').join('');
  }
  function renderStockists() {
    $('#stockistGrid').innerHTML = STOCKISTS.map((s) =>
      '<div class="stockist"><span class="stockist__pin">' + svg(ICONS.pin) + '</span>' +
      '<div><div class="stockist__city">' + s.city + '</div><div class="stockist__meta">' + s.meta + '</div></div>' +
      '<span class="stockist__count">' + s.count + '</span></div>').join('');
  }
  function renderShop() {
    $('#shopGrid').innerHTML = SKUS.map((s, i) => {
      const key = FLAVOR_ORDER[i % FLAVOR_ORDER.length];   // one can per flavour
      return '<article class="sku' + (s.featured ? ' sku--featured' : '') + '">' +
        (s.tag ? '<span class="sku__tag">' + s.tag + '</span>' : '') +
        '<div class="sku__art can-slot" data-can3d data-role="sku" data-flavor="' + key + '">' +
        '<img class="can-fallback" src="assets/can_' + key + '.png?v=4" alt="A can of TEMPO ' + FLAVORS[key].name + '" /></div>' +
        '<h3>' + s.h + '</h3><p class="sku__desc">' + s.desc + '</p>' +
        '<div class="sku__price">' + s.price + ' <small>EGP ' + s.unit + '</small></div>' +
        '<div class="sku__buy"><button class="btn btn--solid" data-add="' + s.h + '" data-magnetic data-cursor="add">Add to cart</button></div>' +
        '<button class="sku__sub" data-sub="' + s.h + '">Subscribe &amp; save 15%</button></article>';
    }).join('');
    $$('#shopGrid [data-add]').forEach((b) => b.addEventListener('click', () => addToCart(b.dataset.add, false)));
    $$('#shopGrid [data-sub]').forEach((b) => b.addEventListener('click', () => addToCart(b.dataset.sub, true)));
  }

  /* ── Cart + toast ── */
  function addToCart(name, sub) {
    state.cart += 1;
    const c = $('#cartCount');
    c.textContent = state.cart; c.setAttribute('data-count', state.cart);
    const cart = $('#cartBtn'); cart.classList.remove('bump'); void cart.offsetWidth; cart.classList.add('bump');
    showToast('Added <b>' + name + '</b>' + (sub ? ' (subscription)' : '') + ' — ' + FLAVORS[state.flavor].name);
  }
  let toastTimer;
  function showToast(html) {
    const t = $('#toast'); t.innerHTML = html; t.hidden = false;
    void t.offsetWidth; t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { t.classList.remove('show'); setTimeout(() => { t.hidden = true; }, 300); }, 2600);
  }

  /* ── Newsletter ── */
  function initNewsletter() {
    $('#newsForm').addEventListener('submit', (e) => {
      e.preventDefault();
      const input = $('#newsEmail'), msg = $('#newsMsg');
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(input.value.trim())) {
        msg.textContent = 'That email doesn’t look right — try again.'; msg.className = 'news__msg err'; return;
      }
      msg.textContent = 'You’re on the list. We’ll send the next drop your way.'; msg.className = 'news__msg ok'; input.value = '';
    });
  }

  /* ── Mobile nav ── */
  function initMobileNav() {
    const btn = $('#hamburger'), menu = $('#mobileNav');
    btn.addEventListener('click', () => {
      const open = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!open)); menu.hidden = open;
    });
    $$('#mobileNav a').forEach((a) => a.addEventListener('click', () => { btn.setAttribute('aria-expanded', 'false'); menu.hidden = true; }));
  }

  /* ── Reveal + count-up ── */
  function initReveal() {
    if (!('IntersectionObserver' in window)) { $$('.reveal').forEach((el) => el.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.15 });
    $$('.reveal').forEach((el) => io.observe(el));
  }
  function initCountUp() {
    const els = $$('[data-countup]'); if (!els.length) return;
    const run = (el) => {
      const target = Number(el.dataset.countup), dur = 1100, start = performance.now();
      const step = (now) => { const t = Math.min(1, (now - start) / dur); el.textContent = Math.round(target * (1 - Math.pow(1 - t, 3))).toLocaleString(); if (t < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    };
    if (!('IntersectionObserver' in window)) { els.forEach(run); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { run(e.target); io.unobserve(e.target); } }), { threshold: 0.6 });
    els.forEach((el) => io.observe(el));
  }

  /* ── The pinned flavour scrub — scroll drives flavour + can spin ── */
  // Absolute document offset of the track — NOT offsetTop, which is relative to
  // the positioned .flavors ancestor and would put the scrub at ~0.
  function trackTop() { const t = $('#flavorTrack'); return t.getBoundingClientRect().top + window.scrollY; }

  function initFlavorScrub() {
    const track = $('#flavorTrack'), hint = $('#flHint');
    let ticking = false;
    function onScroll() {
      if (ticking) return; ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        const top = trackTop();
        const dist = track.offsetHeight - window.innerHeight;
        const p = clamp((window.scrollY - top) / dist, 0, 1);
        const idx = Math.min(FLAVOR_ORDER.length - 1, Math.floor(p * FLAVOR_ORDER.length));
        const key = FLAVOR_ORDER[idx];
        if (key !== state.flavor) setFlavor(key);
        if (TEMPO.can && TEMPO.can.setSpin) TEMPO.can.setSpin(p);
        if (hint) hint.classList.toggle('hide', p > 0.03 || window.scrollY < top - window.innerHeight);
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }

  /* ── Scroll progress bar ── */
  function initScrollProgress() {
    const bar = $('#scrollProgress');
    const upd = () => {
      const h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
    };
    window.addEventListener('scroll', upd, { passive: true });
    window.addEventListener('resize', upd); upd();
  }

  /* ── Custom "scope" cursor (fine pointers only) ── */
  function initCursor() {
    if (!window.matchMedia('(pointer:fine)').matches) return;
    document.body.classList.add('has-cursor');
    const cur = $('#cursor'), dot = $('.cursor__dot', cur), ring = $('.cursor__ring', cur), label = $('.cursor__label', cur);
    let mx = innerWidth / 2, my = innerHeight / 2, rx = mx, ry = my;
    const LABELS = { shop: 'Shop', find: 'Map', add: 'Add', drag: 'Drag', view: 'View' };
    window.addEventListener('mousemove', (e) => {
      mx = e.clientX; my = e.clientY;
      dot.style.transform = 'translate(' + mx + 'px,' + my + 'px) translate(-50%,-50%)';
      const el = e.target.closest('a,button,[data-magnetic],[data-cursor]');
      if (el) {
        cur.classList.add('is-hover');
        const key = el.getAttribute('data-cursor');
        label.textContent = key ? (LABELS[key] || key) : '';
      } else { cur.classList.remove('is-hover'); label.textContent = ''; }
    });
    window.addEventListener('mousedown', () => cur.classList.add('is-down'));
    window.addEventListener('mouseup', () => cur.classList.remove('is-down'));
    (function loop() {
      rx = lerp(rx, mx, prefersReduced ? 1 : 0.18); ry = lerp(ry, my, prefersReduced ? 1 : 0.18);
      ring.style.transform = 'translate(' + rx + 'px,' + ry + 'px) translate(-50%,-50%)';
      requestAnimationFrame(loop);
    })();
  }

  /* ── Magnetic buttons ── */
  function initMagnetic() {
    if (prefersReduced || !window.matchMedia('(pointer:fine)').matches) return;
    $$('[data-magnetic]').forEach((el) => {
      el.addEventListener('mousemove', (e) => {
        const r = el.getBoundingClientRect();
        const x = e.clientX - (r.left + r.width / 2), y = e.clientY - (r.top + r.height / 2);
        el.style.transform = 'translate(' + x * 0.3 + 'px,' + y * 0.4 + 'px)';
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });
  }

  /* ── Hero mouse parallax ── */
  function initParallax() {
    if (prefersReduced || !window.matchMedia('(pointer:fine)').matches) return;
    const art = $('.hero__art'); if (!art) return;
    const glow = $('.hero__glow'), slot = $('.can-slot--hero');
    window.addEventListener('mousemove', (e) => {
      const dx = (e.clientX / innerWidth - 0.5), dy = (e.clientY / innerHeight - 0.5);
      if (slot) slot.style.transform = 'translate(' + dx * 20 + 'px,' + dy * 16 + 'px)';  // the 3D can tracks its slot
      if (glow) glow.style.transform = 'translate(' + dx * -30 + 'px,' + dy * -24 + 'px)';
    });
  }

  function initNoop() {
    $$('[data-noop]').forEach((a) => a.addEventListener('click', (e) => { e.preventDefault(); showToast('This is a demo link — no page behind it.'); }));
  }

  /* ── Dotted Egypt map (stockists) ── */
  function renderMap() {
    const box = $('#egyptMap'); if (!box) return;
    // rough Egypt outline as [lon, lat] — Mediterranean, Sinai, the gulfs,
    // the Red Sea coast, then the straight southern and western borders
    const EG = [[24.7,31.4],[27,31.2],[28.8,30.9],[30.3,31.5],[31.2,31.6],[32.1,31.1],[33.7,31.1],
      [34.25,31.25],[34.9,29.5],[34.4,28.2],[33.9,27.75],[33.1,28.4],[32.6,29.4],[32.55,29.95],
      [32.3,29.6],[32.6,28.5],[33.4,27.4],[34.1,26.5],[35.2,24.9],[35.6,23.9],[36.9,22],[24.9,22]];
    const CITIES = [[31.24,30.05],[29.92,31.2],[33.68,27.39]];   // Cairo, Alexandria, El Gouna
    const X = (lon) => (lon - 24.2) * 23, Y = (lat) => (32.1 - lat) * 23;
    const inside = (x, y) => {                                   // ray casting
      let inp = false;
      for (let i = 0, j = EG.length - 1; i < EG.length; j = i++) {
        const xi = X(EG[i][0]), yi = Y(EG[i][1]), xj = X(EG[j][0]), yj = Y(EG[j][1]);
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inp = !inp;
      }
      return inp;
    };
    let s = '';
    for (let y = 4; y < 236; y += 8)
      for (let x = 4; x < 300; x += 8)
        if (inside(x, y)) s += '<circle class="dot" cx="' + x + '" cy="' + y + '" r="1.7"/>';
    CITIES.forEach(([lon, lat], i) => {
      s += '<circle class="pin-ring" cx="' + X(lon) + '" cy="' + Y(lat) + '" r="7" style="animation-delay:' + i * 0.8 + 's"/>' +
           '<circle class="pin" cx="' + X(lon) + '" cy="' + Y(lat) + '" r="4"/>';
    });
    box.innerHTML = '<svg viewBox="0 0 300 240" role="img" aria-label="Map of Egypt with our three cities">' + s + '</svg>';
  }

  /* ── Boot ── */
  function init() {
    $('#year').textContent = new Date().getFullYear();
    renderFormula();
    renderDots();
    renderIngredients();
    renderTimeline();
    renderPress();
    renderStockists();
    renderShop();
    renderMap();
    setFlavor('citrus');
    initMobileNav(); initNewsletter(); initReveal(); initCountUp();
    initFlavorScrub(); initScrollProgress(); initCursor(); initMagnetic(); initParallax(); initNoop();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
