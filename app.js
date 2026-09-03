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

  /* formula claims — each one annotates the part of the label it is true of */
  const FORMULA = [
    { n: '01', h: 'Zero sugar', p: 'Ten calories, no crash. Sweet from nothing artificial.', side: 'l', target: 'strip' },
    { n: '02', h: 'Fast uptake', p: 'The right osmolality moves water into you, not through you.', side: 'l', target: 'osmo' },
    { n: '03', h: 'Real sodium', p: 'A full gram per can — the dose endurance research points to, not a token pinch.', side: 'r', target: 'pill' },
    { n: '04', h: 'Nothing fake', p: 'No colours, no sucralose, no mystery blend. Every line is legible.', side: 'r', target: 'micro' },
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
    { city: 'Cairo', meta: 'Cafés, gyms & bike shops from Zamalek to New Cairo', count: '38 spots', lon: 31.24, lat: 30.05 },
    { city: 'Alexandria', meta: 'Run clubs & cafés along the Corniche', count: '21 spots', lon: 29.92, lat: 31.2 },
    { city: 'El Gouna', meta: 'The tri club, marina cafés & kite beaches', count: '17 spots', lon: 33.68, lat: 27.39 },
  ];

  const SKUS = [
    { h: '4-Pack', desc: 'A short stack of one flavour. The easy way to find your pace.', price: '200', unit: '/ 4 cans', tag: '', featured: false },
    { h: '12-Case', desc: 'The training case. One flavour, twelve cans, best value per pour.', price: '540', unit: '/ 12 cans', tag: 'Most popular', featured: true },
    { h: 'Variety Case', desc: 'Four of each — Citrus Strike, Arctic Berry, Lime Charge. Meet all three.', price: '560', unit: '/ 12 cans', tag: '', featured: false },
  ];

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
    const src = 'assets/can_' + state.flavor + '.png?v=5';
    $$('.can-slot--hero .can-fallback, .can-slot--stage .can-fallback, .ing__canhome .can-fallback').forEach((img) => {
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
    if ($('#fdFlav')) $('#fdFlav').textContent = f.name;
    if ($('#flBlurb')) $('#flBlurb').textContent = f.blurb;
    if ($('#flSpec')) $('#flSpec').innerHTML =
      f.spec.map((s) => '<li><span>' + s[0] + '</span><b>' + s[1] + '</b></li>').join('');
    $$('#flDots .fl-dot').forEach((d) => d.setAttribute('aria-selected', d.dataset.key === state.flavor));
  }

  /* ── Renderers ── */
  function renderFormula() {
    // label teardown: a flat CSS label in the middle, claims as spec callouts
    const note = (c) => '<div class="fnote reveal" data-target="' + c.target + '"><h3>' +
      '<span class="fnote__num">' + c.n + '</span>' + c.h + '</h3><p>' + c.p + '</p></div>';
    const col = (s) => FORMULA.filter((c) => c.side === s).map(note).join('');
    $('#formulaDiagram').innerHTML =
      '<div class="fdiag__col fdiag__col--l">' + col('l') + '</div>' +
      '<div class="fdiag__label reveal" aria-hidden="true">' +
        '<span class="fdiag__strip">Sparkling &middot; Zero Sugar</span>' +
        '<span class="fdiag__mark">Tempo</span>' +
        '<span class="fdiag__flav" id="fdFlav">Citrus Strike</span>' +
        '<span class="fdiag__grow"></span>' +
        '<span class="fdiag__osmo">Osmolality 290 mOsm/kg</span>' +
        '<span class="fdiag__pill">1g Sodium &middot; 0g Sugar</span>' +
        '<span class="fdiag__micro">Carbonated water &middot; coconut water (12%) &middot; Red Sea salt &middot; potassium citrate &middot; magnesium glycinate &middot; natural citrus &middot; vitamin C &middot; zinc &mdash; that\'s the whole list.</span>' +
      '</div>' +
      '<div class="fdiag__col fdiag__col--r">' + col('r') + '</div>';
    const label = $('#formulaDiagram .fdiag__label');
    $$('#formulaDiagram .fnote').forEach((n) => {
      const t = $('.fdiag__' + n.dataset.target, label);
      const on = () => { label.classList.add('dim'); t.classList.add('lit'); };
      const off = () => { label.classList.remove('dim'); t.classList.remove('lit'); };
      n.addEventListener('mouseenter', on);
      n.addEventListener('mouseleave', off);
      n.addEventListener('click', () => { on(); clearTimeout(n.__t); n.__t = setTimeout(off, 1600); });
    });
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
      '<li><span class="story__year">' + t.y + '</span>' +
      '<div><h3>' + t.h + '</h3><p>' + t.p + '</p></div></li>').join('');
  }

  /* ── Can journey: upright beside the ingredients (02), tilts to 90 as the
     story arrives (03), then rolls down the page printing the years.
     One can, one fixed slot, three scroll phases. ── */
  function initCanJourney() {
    const slot = $('.can-slot--journey'); if (!slot) return;
    const home = $('#canHome');
    const track = $('#storyTrack');
    const stage = $('.story__stage', track);
    const inner = $('.story__inner', track);
    const list = $('#timeline');
    const items = $$('#timeline li');
    const rollH = () => Math.min(400, Math.round(window.innerHeight * 0.42));
    const lerpN = (a2, b2, t) => a2 + (b2 - a2) * t;
    const apply = (r) => {
      slot.style.left = r.left + 'px'; slot.style.top = r.top + 'px';
      slot.style.width = r.width + 'px'; slot.style.height = r.height + 'px';
    };
    let ticking = false;
    function onScroll() {
      if (ticking) return; ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        if (window.innerHeight < 560 || !document.body.classList.contains('webgl')) {
          list.style.clipPath = '';
          items.forEach((el) => el.classList.add('printed'));
          return;
        }
        const H = window.innerHeight;
        const tr = track.getBoundingClientRect();
        const ir = inner.getBoundingClientRect();
        const dist = track.offsetHeight - H;
        const RH = rollH();
        // the can owns its size: the roller box fits the lying can (true GLB
        // proportions 2.0 long × 1.04 wide ≈ 1.92:1, plus margin), centred on
        // the column — never sized to the column it reveals, which let the
        // slot edges shave the can's ends
        const rw = Math.min(window.innerWidth - 16, Math.round(RH * 2.3));
        const roller = (topY) => ({ left: ir.left + (ir.width - rw) / 2, top: topY, width: rw, height: RH });
        const hide = () => {
          list.style.clipPath = 'inset(-60px -20px 100% -20px)';
          items.forEach((el) => el.classList.remove('printed'));
        };
        let tilt, travel = 0, clip = false;
        if (tr.top > H * 0.5) {                     // A: upright at home in 02
          tilt = 0;
          apply(home.getBoundingClientRect());
          hide();
        } else if (tr.top > 0) {                    // B: tilt + travel to the top of 03
          const t = 1 - tr.top / (H * 0.5);
          const e = t * t * (3 - 2 * t);            // smoothstep
          tilt = e * Math.PI / 2;
          const hr = home.getBoundingClientRect();
          // if the home has scrolled far above (mobile: it is static in 02),
          // start the morph from just above the viewport so the tilt is SEEN
          const srcTop = Math.max(hr.top, -hr.height);
          const to = roller(tr.top + 8);
          apply({ left: lerpN(hr.left, to.left, e), top: lerpN(srcTop, to.top, e),
                  width: lerpN(hr.width, to.width, e), height: lerpN(hr.height, to.height, e) });
          hide();
        } else {                                    // C: roll down, print the years
          tilt = Math.PI / 2; clip = true;
          const p = clamp(-tr.top / dist, 0, 1);
          travel = p * stage.clientHeight;    // px moved — can3d turns it into a true roll
          const y = 8 + p * stage.clientHeight;     // starts fully inside — no top cut
          apply(roller(y));
          const edge = y + RH * 0.25 - ir.top - list.offsetTop;
          list.style.clipPath = 'inset(-60px -20px calc(100% - ' + Math.max(0, edge) + 'px) -20px)';
          items.forEach((el) => el.classList.toggle('printed', el.offsetTop < edge));
        }
        slot.dataset.clipActive = clip ? '1' : '';
        if (TEMPO.can && TEMPO.can.setJourney) TEMPO.can.setJourney(tilt, travel);
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    onScroll();
  }
  function renderPress() {
    $('#pressGrid').innerHTML = PRESS.map((p) =>
      '<blockquote class="press__card"><p>' + p.q + '</p><cite>' + p.by + '</cite></blockquote>').join('');
  }
  function renderStockists() {
    $('#stockistGrid').innerHTML = STOCKISTS.map((s, i) =>
      '<div class="stockist" data-pin="' + i + '"><span class="stockist__num">0' + (i + 1) + '</span>' +
      '<div><div class="stockist__city">' + s.city + '</div><div class="stockist__meta">' + s.meta + '</div></div>' +
      '<span class="stockist__count">' + s.count + '</span></div>').join('');
    $$('#stockistGrid .stockist').forEach((row) => {
      const on = () => {
        const map = $('#egyptMap svg'); if (!map) return;
        map.classList.add('dim');
        const pin = $('.pin.p-' + row.dataset.pin, map); if (pin) pin.classList.add('hot');
      };
      const off = () => {
        const map = $('#egyptMap svg'); if (!map) return;
        map.classList.remove('dim');
        $$('.pin', map).forEach((p) => p.classList.remove('hot'));
      };
      row.addEventListener('mouseenter', on);
      row.addEventListener('mouseleave', off);
      row.addEventListener('click', () => { on(); clearTimeout(row.__t); row.__t = setTimeout(off, 1600); });
    });
  }
  function renderShop() {
    $('#shopGrid').innerHTML = SKUS.map((s, i) => {
      const key = FLAVOR_ORDER[i % FLAVOR_ORDER.length];   // one can per flavour
      return '<article class="sku' + (s.featured ? ' sku--featured' : '') + '">' +
        (s.tag ? '<span class="sku__tag">' + s.tag + '</span>' : '') +
        '<div class="sku__art can-slot" data-can3d data-role="sku" data-flavor="' + key + '">' +
        '<img class="can-fallback" src="assets/can_' + key + '.png?v=5" alt="A can of TEMPO ' + FLAVORS[key].name + '" /></div>' +
        '<h3>' + s.h + '</h3><p class="sku__desc">' + s.desc + '</p>' +
        '<div class="sku__price">' + s.price + ' <small>EGP ' + s.unit + '</small>' +
        (s.stock === 'out' ? ' <span class="sku__stock sku__stock--out">Sold out</span>'
          : s.stock === 'low' ? ' <span class="sku__stock">Low stock</span>' : '') + '</div>' +
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
  TEMPO.toast = showToast;

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
    const CITIES = STOCKISTS.map((s) => [s.lon, s.lat]);
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
           '<circle class="pin p-' + i + '" cx="' + X(lon) + '" cy="' + Y(lat) + '" r="4"/>';
    });
    box.innerHTML = '<svg viewBox="0 0 300 240" role="img" aria-label="Map of Egypt with our three cities">' + s + '</svg>';
  }

  /* ── Chain hydration: the static page is the fallback, the contract is the truth ── */
  function hydrate() {
    if (!window.TempoAPI || !TempoAPI.cid()) return; // not deployed yet: static site stands
    TempoAPI.fetchSkus().then((rows) => {
      if (!rows.length) return;
      SKUS.length = 0;
      rows.forEach((r) => SKUS.push({
        h: r.name, desc: r.desc, price: String(Math.round(r.pricePiastres / 100)),
        unit: r.unit, tag: r.tag, featured: r.featured, stock: r.stock,
      }));
      renderShop();
    }).catch(() => {});
    TempoAPI.fetchStockists().then((rows) => {
      if (!rows.length) return;
      STOCKISTS.length = 0;
      rows.forEach((r) => STOCKISTS.push({
        city: r.city, meta: r.meta, count: r.spots + ' spots',
        lon: r.lonMilli / 1000, lat: r.latMilli / 1000,
      }));
      renderStockists();
      renderMap();
    }).catch(() => {});
    refreshPoll();
  }

  /* ── Next-flavour poll (on-chain; the section stays hidden without a chain) ── */
  function renderPoll(rows, mine) {
    if (!rows.length) return;
    const sec = $('#poll');
    sec.hidden = false;
    const open = rows[0].open;
    $('#pollGrid').innerHTML = rows.map((c) => {
      const chosen = mine === c.id;
      return '<button class="poll__card' + (chosen ? ' poll__card--mine' : '') + '" data-vote="' + c.id + '"' + (open ? '' : ' disabled') + '>' +
        '<span class="poll__tally">' + c.tally + '</span>' +
        '<span class="poll__name">' + c.name + '</span>' +
        '<span class="poll__blurb">' + c.blurb + '</span>' +
        (chosen ? '<span class="poll__yours">Your vote</span>' : '') +
        '</button>';
    }).join('');
    $$('#pollGrid [data-vote]').forEach((btn) => {
      btn.addEventListener('click', () => {
        btn.classList.add('poll__card--busy');
        TempoAPI.castVote(Number(btn.dataset.vote)).then(refreshPoll).catch((e) => {
          btn.classList.remove('poll__card--busy');
          showToast(e && e.mayHaveLanded ? 'Vote may still land — check back in a minute'
            : 'Could not vote right now');
        });
      });
    });
    TempoAPI.fetchRecount().then((rc) => {
      if (!rc.length) return;
      const el = $('#pollRecount');
      el.hidden = false;
      el.textContent = 'Recomputed on-chain just now: ' + rc[0].sumTallies + ' votes across ' +
        rc[0].distinctVoters + ' voters — the books ' + (rc[0].holds ? 'balance.' : 'DO NOT balance.');
    }).catch(() => {});
  }
  function refreshPoll() {
    if (!window.TempoAPI || !TempoAPI.cid()) return;
    Promise.all([TempoAPI.fetchPoll(), TempoAPI.fetchMyVote().catch(() => null)])
      .then(([rows, mine]) => renderPoll(rows, mine)).catch(() => {});
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
    initFlavorScrub(); initCanJourney(); initScrollProgress(); initCursor(); initMagnetic(); initParallax(); initNoop();
    hydrate();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
