#!/usr/bin/env python3
"""Regression tests for Pixel_Art_App.html.

Run from the repo root:   python3 tests/run_tests.py
Needs:                    pip install playwright   (then: playwright install chromium)
Optional:                 CHROME=/path/to/chrome  to use an installed Chrome instead

Prints PASS/FAIL per check, how long each test and each group took,
and exits non-zero if anything failed.
Two parts:
  1. Static checks on the file itself (script parses, no duplicate ids,
     every getElementById target exists or is on the known list).
  2. Behaviour checks in a real browser with real mouse events.

To add a test: write a function `def test_something(pg):` below that uses
check(...). It is picked up automatically and gets a fresh 32x32 canvas.
"""
import asyncio, functools, http.server, os, re, shutil, subprocess, sys, threading, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'Pixel_Art_App.html')
results = []

def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(('PASS  ' if ok else 'FAIL  ') + name + (('   -> ' + str(detail)) if (detail and not ok) else ''))

# ---------------------------------------------------------------- static
# getElementById targets that are looked up but intentionally missing
# (optional elements, guarded with `if (el)`). V1_47 docs list 9.
KNOWN_MISSING_IDS_MAX = 9

def static_checks():
    html = open(APP, encoding='utf-8').read()
    scripts = re.findall(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', html)
    node = shutil.which('node')
    if node:
        for i, src in enumerate(scripts):
            with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(src); path = f.name
            r = subprocess.run([node, '--check', path], capture_output=True, text=True)
            os.unlink(path)
            check(f'static: inline script {i+1} parses (node --check)', r.returncode == 0, r.stderr[:300])
    else:
        print('SKIP  static: node not installed, script parse check skipped')
    ids = re.findall(r'\sid="([^"]+)"', html)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    check('static: no duplicate element ids', not dupes, dupes)
    looked_up = set(re.findall(r"getElementById\(\s*'([^']+)'\s*\)", html))
    created = set(re.findall(r"\.id\s*=\s*'([^']+)'", html))
    missing = sorted(looked_up - set(ids) - created)
    check(f'static: unresolved getElementById targets <= {KNOWN_MISSING_IDS_MAX}', len(missing) <= KNOWN_MISSING_IDS_MAX, missing)
    m = re.search(r"const BUILD_VERSION = '([^']+)'", html)
    check('static: BUILD_VERSION present', bool(m), '')
    if m: print('      build ' + m.group(1))

# ---------------------------------------------------------------- browser helpers
async def new_canvas(pg):
    await pg.goto(BASE_URL + 'Pixel_Art_App.html')
    await pg.wait_for_timeout(1200)
    await pg.get_by_text('NEW CANVAS').click()
    await pg.wait_for_timeout(600)
    await pg.get_by_role('button', name='Create Canvas', exact=True).click()
    await pg.wait_for_timeout(1200)

async def grid_point(pg, gx, gy):
    r = await pg.evaluate("() => { const r = container.getBoundingClientRect(); return {l:r.left, t:r.top, w:r.width/gridW, h:r.height/gridH}; }")
    return r['l'] + (gx + .5) * r['w'], r['t'] + (gy + .5) * r['h']

async def tap(pg, gx, gy):
    x, y = await grid_point(pg, gx, gy)
    await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.up()
    await pg.wait_for_timeout(80)

async def px(pg, x, y):
    return await pg.evaluate(f"() => {{ const c = activeLayer().pixelData[{x}]; return c ? c[{y}] : null; }}")

DRAW = "([pts, col]) => { selectedColor = col; pts.forEach(([x,y]) => plot(x,y)); }"

# ---------------------------------------------------------------- tests
async def test_boot_and_canvas(pg):
    check('boot: 32x32 pixel canvas created', await pg.evaluate("() => gridW === 32 && gridH === 32 && activeLayer().type === 'pixel'"))

async def test_pencil_and_undo(pg):
    await pg.evaluate("() => { handleToolBtn('pencil'); selectedColor = '#112233'; }")
    await tap(pg, 5, 5)
    check('pencil: tap draws a pixel', await px(pg, 5, 5) == '#112233', await px(pg, 5, 5))
    await pg.evaluate("() => undo()")
    check('pencil: undo removes it', await px(pg, 5, 5) is None)

async def test_file_button_top(pg):
    box = await pg.locator('#tab-file').bounding_box()
    check('file button: floats at the top-left', box and box['y'] < 80 and box['x'] < 80, box)
    check('file button: at least 44px tall', box and box['height'] >= 44, box)
    await pg.locator('#tab-file').click(); await pg.wait_for_timeout(300)
    check('file button: opens the File panel', await pg.evaluate("() => openPanelName === 'file'"))

async def gappy_square(pg):
    pts = [[i, 10] for i in range(10, 31) if not 19 <= i <= 21] + [[i, 30] for i in range(10, 31)] + \
          [[10, i] for i in range(10, 31)] + [[30, i] for i in range(10, 31)]
    await pg.evaluate(DRAW, [pts, '#000000'])

async def test_fill_close_gaps(pg):
    await gappy_square(pg)
    r = await pg.evaluate("""() => { const s = buildBucketSample(activeLayer());
        bucketGapClose = 0; const leak = computeBucketMask(s, 20, 20).count;
        bucketGapClose = 2; const m = computeBucketMask(s, 20, 20); bucketGapClose = 0;
        let outside = 0; for (let y = 0; y < gridH; y++) for (let x = 0; x < gridW; x++)
            if (m.mask[y*gridW+x] && (x < 10 || x > 30 || y < 10 || y > 30)) outside++;
        return {leak, held: m.count, outside}; }""")
    check('fill: without close-gaps the fill leaks out', r['leak'] > 361, r)
    check('fill: close-gaps 2px keeps it inside (19x19 = 361)', r['held'] == 361, r)
    check('fill: close-gaps leaks nothing outside the square', r['outside'] == 0, r)

async def test_fill_tap_and_undo(pg):
    await gappy_square(pg)
    await pg.evaluate("() => { handleToolBtn('bucket'); selectedColor = '#FF0000'; bucketGapClose = 2; }")
    await tap(pg, 20, 20)
    check('fill tap: inside filled', await px(pg, 20, 20) == '#FF0000')
    check('fill tap: outside untouched', await px(pg, 2, 2) is None)
    await pg.evaluate("() => undo()")
    check('fill tap: one undo removes the fill', await px(pg, 20, 20) is None)

async def test_fill_hold_threshold(pg):
    await pg.evaluate("() => { handleToolBtn('bucket'); selectedColor = '#00FF00'; }")
    x, y = await grid_point(pg, 16, 16)
    await pg.mouse.move(x, y); await pg.mouse.down(); await pg.wait_for_timeout(450)
    await pg.mouse.move(x + 60, y, steps=4); await pg.wait_for_timeout(100)
    hud = await pg.evaluate("() => { const h = document.getElementById('bucketThresholdHud'); return h ? h.style.display : 'none'; }")
    check('fill hold: threshold HUD shows after holding still', hud == 'block', hud)
    await pg.mouse.up(); await pg.wait_for_timeout(150)
    check('fill hold: release commits the fill', await px(pg, 16, 16) == '#00FF00')
    check('fill hold: preview and HUD hidden after release', await pg.evaluate("() => document.getElementById('shapePreview').style.display === 'none' && document.getElementById('bucketThresholdHud').style.display === 'none'"))

async def test_fill_swipe(pg):
    pts = [[c, y] for c in (10, 21) for y in range(32)]
    await pg.evaluate(DRAW, [pts, '#000000'])
    await pg.evaluate("() => { handleToolBtn('bucket'); selectedColor = '#00AA00'; }")
    a = await grid_point(pg, 3, 16); b = await grid_point(pg, 28, 16)
    await pg.mouse.move(*a); await pg.mouse.down(); await pg.mouse.move(*b, steps=12); await pg.mouse.up()
    await pg.wait_for_timeout(150)
    got = [await px(pg, 3, 2), await px(pg, 15, 2), await px(pg, 28, 2), await px(pg, 10, 2)]
    check('fill swipe: all three areas filled', got[:3] == ['#00AA00'] * 3, got)
    check('fill swipe: the lines crossed are not recoloured', got[3] == '#000000', got)
    await pg.evaluate("() => undo()")
    check('fill swipe: one undo removes the whole swipe', await px(pg, 3, 2) is None and await px(pg, 28, 2) is None)

# Baseline for the resize rework: how applyCanvasResize behaves today.
async def test_resize_anchor_top_left(pg):
    await pg.evaluate(DRAW, [[[0, 0], [31, 31]], '#ABCDEF'])
    await pg.evaluate("() => applyCanvasResize(40, 36, 0, 0)")
    ok = await pg.evaluate("() => gridW === 40 && gridH === 36")
    check('resize: grows to 40x36', ok)
    check('resize: top-left anchor keeps pixel at (0,0)', await px(pg, 0, 0) == '#ABCDEF')
    check('resize: and the far pixel at (31,31)', await px(pg, 31, 31) == '#ABCDEF')
    await pg.evaluate("() => undo()")
    check('resize: undo restores 32x32 with the pixels', await pg.evaluate("() => gridW === 32 && gridH === 32") and await px(pg, 0, 0) == '#ABCDEF')

async def test_resize_anchor_centre(pg):
    await pg.evaluate(DRAW, [[[0, 0]], '#ABCDEF'])
    await pg.evaluate("() => applyCanvasResize(40, 40, .5, .5)")
    check('resize: centre anchor shifts by half the growth (4,4)', await px(pg, 4, 4) == '#ABCDEF' and await px(pg, 0, 0) is None)

async def test_resize_crop(pg):
    await pg.evaluate(DRAW, [[[2, 2], [20, 20]], '#ABCDEF'])
    await pg.evaluate("() => applyCanvasResize(16, 16, 0, 0)")
    check('resize: shrinking crops to 16x16', await pg.evaluate("() => gridW === 16 && gridH === 16"))
    check('resize: crop keeps pixels inside', await px(pg, 2, 2) == '#ABCDEF')
    await pg.evaluate("() => undo()")
    check('resize: undo brings back the cropped pixel', await px(pg, 20, 20) == '#ABCDEF')

async def test_resize_sheet(pg):
    await pg.evaluate("() => openResizeCanvasSheet(false)")
    check('resize sheet: opens', await pg.evaluate("() => document.getElementById('resize-canvas-modal').classList.contains('open')"))
    await pg.evaluate("() => { setResizeDimension('w', 48); setResizeDimension('h', 24); }")
    await pg.locator('#resize-apply-btn').click(); await pg.wait_for_timeout(200)
    check('resize sheet: apply resizes to 48x24', await pg.evaluate("() => gridW === 48 && gridH === 24"))
    check('resize sheet: closes after apply', await pg.evaluate("() => !document.getElementById('resize-canvas-modal').classList.contains('open')"))

# ---------------------------------------------------------------- runner
BASE_URL = ''

def find_chrome():
    if os.environ.get('CHROME'): return os.environ['CHROME']
    for p in ('/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              r'C:\Program Files\Google\Chrome\Application\chrome.exe'):
        if os.path.exists(p): return p
    return None  # fall back to Playwright's own Chromium

async def browser_checks():
    from playwright.async_api import async_playwright
    tests = [(n, f) for n, f in globals().items() if n.startswith('test_') and asyncio.iscoroutinefunction(f)]
    async with async_playwright() as p:
        exe = find_chrome()
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox']) if exe else await p.chromium.launch()
        for name, fn in tests:
            ctx = await b.new_context(viewport={'width': 1000, 'height': 800})
            pg = await ctx.new_page()
            errors = []
            pg.on('pageerror', lambda e: errors.append(str(e)))
            print(f'-- {name}')
            t0 = time.perf_counter()
            try:
                await new_canvas(pg)
                await fn(pg)
            except Exception as e:
                check(f'{name}: ran without crashing', False, repr(e)[:300])
            check(f'{name}: no page errors', not errors, errors[:3])
            print(f'   {name} took {time.perf_counter() - t0:.2f}s')
            await ctx.close()
        await b.close()

def main():
    global BASE_URL
    t_all = time.perf_counter()
    t0 = time.perf_counter()
    print('== static checks'); static_checks()
    print(f'== static checks took {time.perf_counter() - t0:.2f}s')
    # Serve over HTTP (IndexedDB is unreliable on file://).
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    BASE_URL = f'http://127.0.0.1:{srv.server_address[1]}/'
    t0 = time.perf_counter()
    print('== browser checks'); asyncio.run(browser_checks())
    print(f'== browser checks took {time.perf_counter() - t0:.2f}s')
    srv.shutdown()
    failed = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(failed)} passed, {len(failed)} failed in {time.perf_counter() - t_all:.2f}s')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()
