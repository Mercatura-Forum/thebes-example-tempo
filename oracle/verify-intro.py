# oracle/verify-intro.py — drives the intro in headless Chromium (SwiftShader).
# Run: python3 -m http.server 8000 &  then  python3 oracle/verify-intro.py
# Exits nonzero on any failure.
from playwright.sync_api import sync_playwright
import sys

failures = 0
def check(ok, name):
    global failures
    print(('ok ' if ok else 'FAIL ') + name)
    if not ok:
        failures += 1

URL = 'http://localhost:8000/'
ARGS = ['--use-gl=angle', '--enable-unsafe-swiftshader']

# the site sets `scroll-behavior: smooth`, so a programmatic scrollTo ANIMATES;
# force it off or every scroll assertion reads mid-flight (see the mobile note).
NO_SMOOTH = "() => document.documentElement.style.setProperty('scroll-behavior','auto','important')"

with sync_playwright() as p:
    browser = p.chromium.launch(args=ARGS)

    # ── desktop run ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    C = page.evaluate('() => window.TempoIntro.CONST')

    # the wordmark fills like liquid — the line RISES (fillY decreases) and the
    # counter climbs. Sampled from the live render, not the counter's own value.
    page.wait_for_timeout(int(C['T_LOAD'] * 0.28))
    a = page.evaluate('() => ({ y: TempoIntro.state.fillY, n: parseInt(document.getElementById("introCount").textContent,10), pills: document.querySelectorAll(".intro__pill").length })')
    page.wait_for_timeout(int(C['T_LOAD'] * 0.4))
    b = page.evaluate('() => ({ y: TempoIntro.state.fillY, n: parseInt(document.getElementById("introCount").textContent,10) })')
    check(b['y'] < a['y'] - 2, f"liquid fill rises over the loader ({a['y']:.0f} → {b['y']:.0f})")
    check(b['n'] > a['n'], f"counter climbs ({a['n']} → {b['n']})")
    check(a['pills'] >= 1, f"electrolyte pills spawn (got {a['pills']})")

    # reveal reached, canvas live
    page.wait_for_selector('.intro--reveal', timeout=C['T_LOAD'] + C['T_ZOOM'] + 4000)
    page.wait_for_selector('body.webgl', timeout=15000)
    check(True, 'reveal phase + webgl reached')

    # the zoomed wordmark shows in FULL — inside the viewport on every edge
    # (no top clip, no overflow) and still prominent
    lg = page.evaluate('''() => { const r = document.querySelector('.intro__logo').getBoundingClientRect();
      return { l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, iw: innerWidth, ih: innerHeight }; }''')
    check(lg['l'] >= -1 and lg['r'] <= lg['iw'] + 1 and lg['t'] >= -1 and lg['b'] <= lg['ih'] + 1,
          f"zoomed wordmark fully on screen (x {lg['l']:.0f}..{lg['r']:.0f} / y {lg['t']:.0f}..{lg['b']:.0f})")
    check(lg['w'] > 0.4 * lg['iw'], f"wordmark stays prominent ({lg['w']:.0f}px wide)")

    # the porthole tracks the pointer fast; the can CHASES the cursor — slow
    # and a beat behind, so a jump leaves it trailing before it settles in
    SAMPLE = '''() => { const r = document.getElementById('introCan').getBoundingClientRect();
      const cs = getComputedStyle(document.getElementById('introSheet'));
      return { mx: parseFloat(cs.getPropertyValue('--mx')), mr: parseFloat(cs.getPropertyValue('--mr')),
        cc: r.left + r.width / 2 }; }'''
    page.mouse.move(430, 450)
    page.wait_for_timeout(2200)
    m1 = page.evaluate(SAMPLE)
    page.mouse.move(1010, 450)
    page.wait_for_timeout(260)
    lag = page.evaluate(SAMPLE)          # right after the jump: hole ahead, can behind
    page.wait_for_timeout(2400)
    m2 = page.evaluate(SAMPLE)           # settled: can caught up under the cursor
    check(m1['mx'] < 600 and m2['mx'] > 840 and (m2['mx'] - m1['mx']) > 300,
          f"porthole tracks the cursor left→right ({m1['mx']:.0f} → {m2['mx']:.0f})")
    check(lag['mx'] - lag['cc'] > 150,
          f"can trails a beat behind the hole after a jump (gap {lag['mx'] - lag['cc']:.0f}px)")
    check(abs(m1['cc'] - 430) < 80 and abs(m2['cc'] - 1010) < 80,
          f"can settles under the cursor ({m1['cc']:.0f} ≈ 430, then {m2['cc']:.0f} ≈ 1010)")
    check(m1['mr'] < 200 and m2['mr'] < 200,
          f"hole rests to a pupil while the cursor is still (r {m1['mr']:.0f}, {m2['mr']:.0f})")
    # > 200 not ~294: computed style shows the LAST PAINTED frame, and a rAF
    # stall can leave that early in the dilation curve — 200 still proves the
    # hole is well off its 150 rest and dilating
    check(lag['mr'] > 200, f"hole dilates back the moment the cursor moves (r {lag['mr']:.0f})")

    # the lens reads as a black hole: a shadow ring rides the porthole edge
    lens = page.evaluate('''() => { const el = document.querySelector('.intro__lens');
      if (!el) return null;
      const cs = getComputedStyle(el), r = el.getBoundingClientRect();
      return { shadow: cs.boxShadow !== 'none', op: parseFloat(cs.opacity), x: r.left + r.width / 2 }; }''')
    check(lens and lens['shadow'] and lens['op'] > 0.9, 'black-hole shadow ring is live during the reveal')
    check(lens and abs(lens['x'] - m2['mx']) < 8,
          f"shadow ring rides the porthole (ring {lens['x']:.0f} vs hole {m2['mx']:.0f})" if lens else 'shadow ring rides the porthole')

    # the lens goes THROUGH the logo: an x-ray twin of the wordmark sits in the
    # dark recess, pixel-aligned under the sheet's wordmark, outline not ink
    xr = page.evaluate('''() => { const a = document.querySelector('.intro__sheet .intro__logo');
      const b = document.querySelector('.intro__under .intro__logo');
      if (!a || !b) return null;
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      const cs = getComputedStyle(document.querySelector('.intro__logo-xray'));
      return { dx: Math.abs(ra.left - rb.left), dy: Math.abs(ra.top - rb.top),
        dw: Math.abs(ra.width - rb.width), fill: cs.fill, stroke: cs.stroke }; }''')
    check(xr and xr['dx'] < 1.5 and xr['dy'] < 1.5 and xr['dw'] < 1.5,
          f"x-ray wordmark aligns under the sheet wordmark (dx {xr['dx']:.1f} dy {xr['dy']:.1f} dw {xr['dw']:.1f})" if xr else 'x-ray wordmark present + aligned')
    check(xr and xr['fill'] == 'none' and xr['stroke'] != 'none',
          'x-ray wordmark is a skeleton — stroke outline, no ink')

    # the exit cannot be rushed: a violent flick pins the page at one viewport
    # while the curtain lifts at its own capped pace, hero waiting beneath
    vh = page.evaluate('() => innerHeight')
    page.evaluate(f'() => window.scrollTo(0, {vh + 300})')   # hard flick past the spacer
    page.wait_for_timeout(250)
    mid = page.evaluate('''() => { const el = document.getElementById('intro');
      const t = document.querySelector('.hero__title').getBoundingClientRect();
      const ty = el ? Math.abs(new DOMMatrixReadOnly(getComputedStyle(el).transform).m42) : 1e9;
      return { intro: !!el, sliding: !!document.querySelector('.intro--sliding'),
        ty: ty, y: window.scrollY,
        lens: parseFloat(getComputedStyle(document.querySelector('.intro__lens')).opacity),
        heroVisible: t.top < innerHeight && t.bottom > 0 }; }''')
    check(mid['intro'] and mid['sliding'], 'intro slides rather than cutting to a new page')
    check(mid['ty'] < vh * 0.75,
          f"a flick can't rush the curtain — the lift is rate-capped ({mid['ty']:.0f}px of {vh}vh after 250ms)")
    check(mid['y'] <= vh + 2, f"scroll pins at one viewport while the curtain lifts (y {mid['y']:.0f})")
    check(mid['heroVisible'], 'the live hero waits beneath the curtain')
    check(mid['lens'] == 0, 'shadow ring snaps off once the slide begins')
    # motion is asserted as PROGRESS between two samples (an absolute lift at
    # one instant flakes when SwiftShader stalls rAF on the hero's first frame)
    page.wait_for_timeout(450)
    ty2 = page.evaluate('''() => { const el = document.getElementById('intro');
      return el ? Math.abs(new DOMMatrixReadOnly(getComputedStyle(el).transform).m42) : Infinity; }''')
    check(ty2 > mid['ty'] + 30, f"the curtain keeps lifting on its own ({mid['ty']:.0f} → {'gone' if ty2 == float('inf') else format(ty2, '.0f')})")

    # the curtain completes on its own → clean handoff at the hero top
    page.wait_for_timeout(1000)
    post = page.evaluate('''() => ({ intro: !!document.getElementById('intro'),
      spacer: !!document.querySelector('.intro__spacer'),
      veil: document.documentElement.classList.contains('intro-veil'),
      y: window.scrollY, overflow: document.documentElement.scrollWidth - window.innerWidth,
      hero: document.querySelector('.hero__title').getBoundingClientRect().top })''')
    check(not post['intro'] and not post['spacer'] and not post['veil'], 'intro + spacer + veil all cleared')
    check(post['y'] < 120, f"no scroll jump on handoff (rests at {post['y']})")
    check(post['overflow'] == 0, f"no horizontal overflow (delta {post['overflow']})")
    check(post['hero'] >= -10 and post['hero'] < 900, 'hero title on screen after handoff')

    # the page itself glides: a violent wheel flick is velocity-capped and
    # smoothed, then settles exactly at the damped target — no native blast
    C2 = page.evaluate('() => window.TempoScroll.CONST')
    y0 = page.evaluate('() => window.scrollY')
    page.mouse.wheel(0, 4000)
    page.wait_for_timeout(250)
    g1 = page.evaluate('() => window.scrollY')
    page.wait_for_timeout(700)
    g2 = page.evaluate('() => window.scrollY')
    cap250 = C2['MAX_V'] * vh * 0.25
    check(g1 - y0 > 60 and g1 - y0 < cap250 * 1.7,
          f"wheel flick is velocity-capped ({g1 - y0:.0f}px in 250ms, cap ≈ {cap250:.0f})")
    check(g2 > g1 + 100, f"the glide keeps rolling toward the target ({g1:.0f} → {g2:.0f})")
    # poll until the glide STOPS (scrollY stable across 300ms) — a fixed wait
    # races the velocity cap when the box is loaded
    g3 = prev_y = -1
    for _ in range(30):
        page.wait_for_timeout(300)
        g3 = page.evaluate('() => window.scrollY')
        if g3 == prev_y: break
        prev_y = g3
    tgt = page.evaluate(f'() => Math.min({y0} + 4000 * {C2["WHEEL_GAIN"]}, document.documentElement.scrollHeight - innerHeight)')
    check(abs(g3 - tgt) < 60, f"glide settles at the damped target ({g3:.0f} ≈ {tgt:.0f})")
    page.close()

    # ── reduced motion: exits by itself, no interaction ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    C = page.evaluate('() => window.TempoIntro.CONST')
    page.wait_for_timeout(C['T_REDUCED'] + C['T_REDUCED_EXIT'] + 600)
    check(page.evaluate("() => !document.getElementById('intro')"), 'reduced motion self-dismisses')
    page.close()

    # ── mobile: shrink-to-fit gate, clamped zoom, auto-drift, overflow ──
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    C = page.evaluate('() => window.TempoIntro.CONST')
    iw = page.evaluate('() => window.innerWidth')
    check(iw == 390, f"innerWidth == viewport ({iw}) — no shrink-to-fit zoom")
    page.wait_for_selector('.intro--reveal', timeout=C['T_LOAD'] + C['T_ZOOM'] + 4000)
    page.wait_for_timeout(500)
    ov1 = page.evaluate('() => document.documentElement.scrollWidth - window.innerWidth')
    check(ov1 == 0, f"clamped zoom introduces no mobile overflow (delta {ov1})")
    d1 = page.evaluate("() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx'))")
    page.wait_for_timeout(900)
    d2 = page.evaluate("() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx'))")
    check(abs(d2 - d1) > 8, f"auto-drift moves the hole on touch ({d1:.0f} → {d2:.0f})")
    ctx.close()

    browser.close()

sys.exit(1 if failures else 0)
