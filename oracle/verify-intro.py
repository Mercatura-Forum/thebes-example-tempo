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

with sync_playwright() as p:
    browser = p.chromium.launch(args=ARGS)

    # ── desktop run ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto(URL, wait_until='domcontentloaded')
    C = page.evaluate('() => window.TempoIntro.CONST')

    # loader mid-flight: counter and fill agree (both derive from progress)
    page.wait_for_timeout(C['T_LOAD'] * 0.5)
    mid = page.evaluate('''() => ({
      n: parseInt(document.getElementById('introCount').textContent, 10),
      w: parseFloat(document.getElementById('introFillRect').getAttribute('width')),
      pills: document.querySelectorAll('.intro__pill').length,
    })''')
    check(20 <= mid['n'] <= 90, f"mid-load counter in 20..90 (got {mid['n']})")
    check(abs(mid['w'] / C['FILL_W'] * 100 - mid['n']) <= 3, 'fill width tracks the counter (±3)')
    check(mid['pills'] >= 1, f"pills are spawning (got {mid['pills']})")

    # reveal reached, canvas live
    page.wait_for_selector('.intro--reveal', timeout=C['T_LOAD'] + C['T_ZOOM'] + 3000)
    page.wait_for_selector('body.webgl', timeout=15000)
    check(True, 'reveal phase + webgl reached')

    # the mask eases toward the cursor and the can slot rides with it. The
    # follow is a per-frame lerp and headless rAF is slow, so assert the real
    # objective — the mask tracks left→right and settles on the correct side —
    # rather than demanding it snap to an exact pixel within a fixed wait.
    # A non-following mask sits at centre (~720) and fails every clause below.
    page.mouse.move(430, 450)
    page.wait_for_timeout(1400)
    a = page.evaluate('''() => ({
      mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
      can: document.getElementById('introCan').getBoundingClientRect().left,
    })''')
    page.mouse.move(1000, 450)
    page.wait_for_timeout(1400)
    b = page.evaluate('''() => ({
      mx: parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx')),
      can: document.getElementById('introCan').getBoundingClientRect().left,
    })''')
    check(a['mx'] < 600 and b['mx'] > 840 and (b['mx'] - a['mx']) > 300,
          f"mask tracks the cursor left→right ({a['mx']:.0f} → {b['mx']:.0f})")
    check(b['can'] - a['can'] > 400, f"can slot follows the cursor ({a['can']:.0f} → {b['can']:.0f})")

    # exit on wheel: intro gone, page unlocked, no horizontal overflow
    page.mouse.wheel(0, 120)
    page.wait_for_timeout(C['T_EXIT'] + 300)
    post = page.evaluate('''() => ({
      intro: !!document.getElementById('intro'),
      htmlClass: document.documentElement.classList.contains('intro'),
      scrollY: window.scrollY,
      overflow: document.documentElement.scrollWidth - window.innerWidth,
      hero: document.querySelector('.hero__title').getBoundingClientRect().top,
    })''')
    check(not post['intro'] and not post['htmlClass'], 'intro removed after wheel exit')
    check(post['scrollY'] == 0, 'page rests at the top')
    check(post['overflow'] == 0, f"no horizontal overflow (delta {post['overflow']})")
    check(0 <= post['hero'] < 900, 'hero title on screen')
    page.close()

    # ── reduced motion: exits by itself, no interaction ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(URL, wait_until='domcontentloaded')
    C = page.evaluate('() => window.TempoIntro.CONST')
    page.wait_for_timeout(C['T_REDUCED'] + C['T_EXIT'] + 600)
    check(page.evaluate("() => !document.getElementById('intro')"), 'reduced motion self-dismisses')
    page.close()

    # ── mobile: shrink-to-fit gate, auto-drift, overflow ──
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded')
    C = page.evaluate('() => window.TempoIntro.CONST')
    iw = page.evaluate('() => window.innerWidth')
    check(iw == 390, f"innerWidth == viewport ({iw}) — no shrink-to-fit zoom")
    page.wait_for_selector('.intro--reveal', timeout=C['T_LOAD'] + C['T_ZOOM'] + 3000)
    page.wait_for_timeout(500)
    d1 = page.evaluate("() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx'))")
    page.wait_for_timeout(900)
    d2 = page.evaluate("() => parseFloat(getComputedStyle(document.getElementById('introSheet')).getPropertyValue('--mx'))")
    check(abs(d2 - d1) > 8, f"auto-drift moves the mask ({d1:.0f} → {d2:.0f})")
    ow = page.evaluate('() => document.documentElement.scrollWidth - window.innerWidth')
    check(ow == 0, f"no mobile horizontal overflow (delta {ow})")
    ctx.close()

    browser.close()

sys.exit(1 if failures else 0)
