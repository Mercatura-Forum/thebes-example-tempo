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

    # the cursor-lit hole tracks the pointer and the can rides with it
    page.mouse.move(430, 450)
    page.wait_for_timeout(1400)
    m1 = page.evaluate('''() => ({ mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
      can: document.getElementById('introCan').getBoundingClientRect().left })''')
    page.mouse.move(1000, 450)
    page.wait_for_timeout(1400)
    m2 = page.evaluate('''() => ({ mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
      can: document.getElementById('introCan').getBoundingClientRect().left })''')
    check(m1['mx'] < 600 and m2['mx'] > 840 and (m2['mx'] - m1['mx']) > 300,
          f"hole tracks the cursor left→right ({m1['mx']:.0f} → {m2['mx']:.0f})")
    check(m2['can'] - m1['can'] > 400, f"can rides with the cursor ({m1['can']:.0f} → {m2['can']:.0f})")

    # the transition is CONTINUOUS: mid-scroll the intro is still there, sliding,
    # and the live hero has risen into view beneath it (not a blank page)
    vh = page.evaluate('() => innerHeight')
    page.evaluate(f'() => window.scrollTo(0, {int(vh*0.5)})')
    page.wait_for_timeout(300)
    mid = page.evaluate('''() => { const t = document.querySelector('.hero__title').getBoundingClientRect();
      return { intro: !!document.getElementById('intro'),
        sliding: !!document.querySelector('.intro--sliding'),
        heroTop: t.top, ih: innerHeight,
        heroVisible: t.top < innerHeight && t.bottom > 0 }; }''')
    check(mid['intro'] and mid['sliding'], 'intro slides rather than cutting to a new page')
    check(mid['heroVisible'], f"the live hero rises in during the slide (title top {mid['heroTop']:.0f})")

    # finish the scroll → clean handoff: intro + spacer gone, page at the hero, no jump/overflow
    page.evaluate(f'() => window.scrollTo(0, {vh + 40})')
    page.wait_for_timeout(500)
    post = page.evaluate('''() => ({ intro: !!document.getElementById('intro'),
      spacer: !!document.querySelector('.intro__spacer'),
      veil: document.documentElement.classList.contains('intro-veil'),
      y: window.scrollY, overflow: document.documentElement.scrollWidth - window.innerWidth,
      hero: document.querySelector('.hero__title').getBoundingClientRect().top })''')
    check(not post['intro'] and not post['spacer'] and not post['veil'], 'intro + spacer + veil all cleared')
    check(post['y'] < 120, f"no scroll jump on handoff (rests at {post['y']})")
    check(post['overflow'] == 0, f"no horizontal overflow (delta {post['overflow']})")
    check(post['hero'] >= -10 and post['hero'] < 900, 'hero title on screen after handoff')
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
