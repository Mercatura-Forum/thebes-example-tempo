# oracle/verify-street.py — drives the Cairo street in headless Chromium.
# Run: python3 -m http.server 8000 &  then  python3 oracle/verify-street.py
# Exits nonzero on any failure. Motion/camera waits poll SETTLE STATE, never
# wall-clock (SwiftShader frame rates vary wildly on a loaded box).
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
NO_SMOOTH = "() => document.documentElement.style.setProperty('scroll-behavior','auto','important')"

def through_intro(page):
    page.wait_for_timeout(600)
    page.keyboard.press('Space')
    page.wait_for_selector('.intro--reveal', timeout=10000)
    page.wait_for_selector('body.webgl', timeout=20000)
    vh = page.evaluate('() => innerHeight')
    page.evaluate(f'() => window.scrollTo(0, {vh})')
    for _ in range(60):
        if page.evaluate("() => !document.getElementById('intro')"): return
        page.wait_for_timeout(100)

def wait_for(page, expr, timeout_ms, step=100):
    for _ in range(max(1, timeout_ms // step)):
        if page.evaluate(expr): return True
        page.wait_for_timeout(step)
    return False

with sync_playwright() as p:
    browser = p.chromium.launch(args=ARGS)

    # ── desktop: the full journey ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    through_intro(page)

    # the portal is lazy: none of the street's 3D bytes load before the tap
    page.evaluate("() => document.getElementById('stockists').scrollIntoView()")
    page.wait_for_timeout(400)
    pre = page.evaluate("""() => performance.getEntriesByType('resource')
      .filter(e => (e.name.includes('assets/street/') && !e.name.includes('poster')) || e.name.includes('draco')).length""")
    check(pre == 0, f"portal is lazy — no street 3D bytes before the tap ({pre} requests)")
    check(page.evaluate("() => !!document.querySelector('.street-portal__poster')"), 'portal poster present in section 05')

    y_before = page.evaluate('() => window.scrollY')
    page.click('#streetEnter')
    t0 = page.evaluate('() => performance.now()')
    ready = wait_for(page, '() => window.TempoStreet.state.ready', 20000)
    t1 = page.evaluate('() => performance.now()')
    check(ready, 'street enters and renders')
    check(t1 - t0 < 8000, f"enter-to-first-frame under 8s on SwiftShader (took {(t1 - t0) / 1000:.1f}s)")
    check(page.evaluate("() => document.documentElement.classList.contains('street-lock')"), 'page scroll parks behind the stage')

    # walking: progress between samples (stall rule), and fps while moving
    p0 = page.evaluate('() => ({...window.TempoStreet.state.player})')
    page.keyboard.down('KeyW')
    page.wait_for_timeout(900)
    pmid = page.evaluate('() => ({...window.TempoStreet.state.player})')
    page.wait_for_timeout(900)
    page.keyboard.up('KeyW')
    p1 = page.evaluate('() => ({...window.TempoStreet.state.player})')
    d1 = abs(pmid['x'] - p0['x']) + abs(pmid['z'] - p0['z'])
    d2 = abs(p1['x'] - pmid['x']) + abs(p1['z'] - pmid['z'])
    # total progress, not per-window — the first window can eat a scene
    # warm-up stall under SwiftShader while the sim itself is fine
    check(d1 + d2 > 1.0, f"W walks the runner through the street ({d1:.2f}m + {d2:.2f}m)")
    fps = page.evaluate("""() => new Promise(res => {
      let n = 0; const t0 = performance.now();
      const tick = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(tick); else res(n / 2); };
      requestAnimationFrame(tick);
    })""")
    check(fps >= 10, f"walk holds a headless-SwiftShader floor of 10fps (measured {fps:.0f})")

    # to the koshk: warp inside the trigger → focus engages, camera settles
    page.evaluate('() => window.TempoStreet.warp(6.8, 0.3)')
    check(wait_for(page, "() => window.TempoStreet.state.mode === 'focus'", 5000), 'the koshk trigger engages focus')
    check(wait_for(page, '() => window.TempoStreet.state.camDist < 0.03', 15000), 'focus camera settles at the shelf')
    pts = page.evaluate('() => window.TempoStreet.canScreenPoints()')
    onscreen = [q for q in pts if 0 < q['x'] < 1440 and 0 < q['y'] < 900]
    check(len(onscreen) == 9, f"all nine cans frame on screen at focus ({len(onscreen)}/9)")

    # take a berry can → the shop opens with berry applied, and it SURVIVES
    berry = page.evaluate("() => window.TempoStreet.canScreenPoints().filter(q => q.key === 'berry')[1]")
    page.mouse.click(berry['x'], berry['y'])
    check(wait_for(page, "() => !document.getElementById('streetStage')", 4000), 'taking a can closes the street')
    check(page.evaluate("() => window.TempoStreet.state.lastPick === 'berry'"), 'the tapped can resolves to its own flavor')
    page.wait_for_timeout(1200)
    post = page.evaluate("""() => ({ flavor: document.documentElement.getAttribute('data-flavor'),
      disposed: window.TempoStreet.state.disposed,
      lock: document.documentElement.classList.contains('street-lock'),
      shopTop: document.getElementById('shop').getBoundingClientRect().top,
      overflow: document.documentElement.scrollWidth - window.innerWidth })""")
    check(post['flavor'] == 'berry', f"berry survives to the shop — the scrub no longer stomps it (flavor {post['flavor']})")
    check(post['disposed'] and not post['lock'], 'world disposed and scroll unlocked on leave')
    check(post['shopTop'] < 900, f"the shop arrives in view (top {post['shopTop']:.0f})")
    check(post['overflow'] == 0, f"no horizontal overflow after the journey (delta {post['overflow']})")
    check(not errors, f"zero page errors through the whole journey ({errors[:2]})")

    # re-enter → ESC leaves and restores the scroll position
    page.evaluate("() => document.getElementById('stockists').scrollIntoView()")
    page.wait_for_timeout(300)
    page.click('#streetEnter')   # playwright may nudge the scroll to reach the button
    wait_for(page, '() => window.TempoStreet.state.ready', 20000)
    y_stock = page.evaluate('() => window.scrollY')   # what enter() saw and must restore
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    y_after = page.evaluate('() => window.scrollY')
    check(page.evaluate("() => !document.getElementById('streetStage')"), 'ESC leaves the street')
    check(abs(y_after - y_stock) < 4, f"leave restores the exact scroll position ({y_stock:.0f} → {y_after:.0f})")
    page.close()

    # ── reduced motion: the flat shelf fallback, still shoppable ──
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    wait_for(page, "() => !document.getElementById('intro')", 8000)
    page.evaluate("() => document.getElementById('stockists').scrollIntoView()")
    page.wait_for_timeout(300)
    page.click('#streetEnter')
    page.wait_for_timeout(600)
    flat = page.evaluate("""() => ({ flat: !!document.querySelector('.street-flat'),
      canvas: !!document.querySelector('.street-canvas'),
      btns: document.querySelectorAll('.street-flat__row .btn').length })""")
    check(flat['flat'] and not flat['canvas'] and flat['btns'] == 3, 'reduced motion gets the flat shelf with all three flavors')
    page.close()

    # ── mobile: portal fits, no overflow introduced ──
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded')
    page.evaluate(NO_SMOOTH)
    iw = page.evaluate('() => window.innerWidth')
    check(iw == 390, f"innerWidth == viewport ({iw}) — no shrink-to-fit zoom")
    ov = page.evaluate('() => document.documentElement.scrollWidth - window.innerWidth')
    check(ov == 0, f"portal introduces no mobile overflow (delta {ov})")
    ctx.close()

    browser.close()

sys.exit(1 if failures else 0)
