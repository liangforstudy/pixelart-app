#!/usr/bin/env python3
"""Regression tests for Pixel_Art_App.html.

Run from the repo root:   python3 tests/run_tests.py              (everything)
                          python3 tests/run_tests.py fill resize  (only those groups)
                          python3 tests/run_tests.py --list       (groups + what code each covers)
Needs:                    pip install playwright   (then: playwright install chromium)
Optional:                 CHROME=/path/to/chrome  to use an installed Chrome instead

Prints PASS/FAIL per check, how long each test and each group took,
and exits non-zero if anything failed.
Two parts:
  1. Static checks on the file itself (script parses, no duplicate ids,
     every getElementById target exists or is on the known list).
  2. Behaviour checks in a real browser with real mouse events.

Tests are grouped by the system they cover (see GROUPS), so after a change
you only run the groups for the code you touched. Static checks always run
(they take well under a second). Shared code (see SHARED_CODE) means: run all.

To add a test: write `async def test_something(pg):` below that uses
check(...), and add its name to a group in GROUPS. Every test gets a fresh
32x32 canvas. A test in no group, or a group naming a missing test, fails.
"""
import asyncio, functools, http.server, os, re, shutil, subprocess, sys, threading, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, 'Pixel_Art_App.html')
results = []

def fmt(sec):
    """Seconds under 120 as '96.4s'; from 120 on as minutes too: '2m 05s (125.3s)'."""
    if sec < 120: return f'{sec:.2f}s'
    m, r = divmod(int(round(sec)), 60)
    return f'{m}m {r:02d}s ({sec:.1f}s)'

def check(name, ok, detail=''):
    results.append((name, bool(ok)))
    print(('PASS  ' if ok else 'FAIL  ') + name + (('   -> ' + str(detail)) if (detail and not ok) else ''))

# ---------------------------------------------------------------- groups
# group -> (what it covers in Pixel_Art_App.html, [test names])
GROUPS = {
    'zoom-indicator': ('On-screen zoom readout: #zoomIndicator, formatZoom, updateZoomIndicator, live during pinch (applyCameraTransform).',
                       ['test_zoom_indicator']),
    'layers-drawer': ('Right-side glass layers drawer (#panel-layers.layers-drawer): strip/full mode, layersDrawerPrefs, hide while drawing, #layerSettingsPane, icon row, #layersSplitHandle, beginTreeDrag drag-to-reorder, #debugFab.',
                      ['test_layers_drawer_modes', 'test_layers_drawer_hides_while_drawing', 'test_layers_drag_reorder', 'test_layers_drag_into_group_and_cancel', 'test_layers_debug_on_top', 'test_layers_back_to_strip_and_done', 'test_drawer_splits_collapse_on_phone']),
    'core': ('Boot, New Canvas, pencil, plot(), undo/redo (history). Also run after editing SHARED_CODE.',
             ['test_boot_and_canvas', 'test_pencil_and_undo']),
    'layout': ('Floating bars, top-left #topBar, bottom #floatingBar, panels/drawers opening (togglePanel, closePanel).',
               ['test_file_button_top']),
    'fill': ('Bucket fill: computeBucketMask, buildBucketSample, applyBucketMask, bucket gestures (startBucketGesture, swipe, threshold HUD), bucket controls.',
             ['test_fill_close_gaps', 'test_fill_tap_and_undo', 'test_fill_hold_threshold', 'test_fill_swipe']),
    'resize': ('Canvas resize engine and the number sheet: applyCanvasResize, applyCanvasResizeOffset, anchorOffset, resize*LayerAnchored, snapshot/restoreCanvasResizeState, #resize-canvas-modal.',
               ['test_resize_anchor_top_left', 'test_resize_anchor_centre', 'test_resize_crop', 'test_resize_sheet', 'test_resize_offset_engine']),
    'resize-screen': ('The resize screen: RS, enterResizeScreen, rs* functions, #resizeScreen, openResizeFor, NUMBERS (sheet with target rect).',
                      ['test_resize_screen_grow_edge', 'test_resize_screen_draw_outside', 'test_resize_screen_move_inside',
                       'test_resize_screen_crop_two_taps', 'test_resize_screen_discard', 'test_resize_screen_lock_ratio',
                       'test_resize_screen_snap', 'test_resize_screen_second_finger_guard', 'test_resize_screen_numbers_button',
                       'test_resize_portrait_sprite_use_sheet']),
    'settings': ('Customise panel settings and saved preferences: resizePrefs, #customisationSection-*, localStorage prefs.',
                 ['test_resize_prefs']),
    'new-canvas': ('New Canvas sheet (openNewCanvasModal, #newCanvasSizeBox, #newCanvasCreateBtn), startNewProjectFromGallery, the resize screen in "new" mode.',
                   ['test_new_canvas_size_on_screen', 'test_new_canvas_discard', 'test_new_canvas_portrait_keeps_fields']),
    'mapart': ('Mapart profile: MAPART_DATA, mapartSnapColor/mapartSnapRGB/mapartLab, syncMapartPalette, toggleMapartStaircase, resolveMapartStaircaseOff, mapartConvertToFlat (pixelsMulti history), mapart import snapping, New Canvas size in maps, mapart save/load.',
               ['test_mapart_new_canvas_in_maps', 'test_resize_sheet_no_autoselect_outside_mapart', 'test_mapart_resize_sheet_in_maps', 'test_mapart_palette_locked', 'test_mapart_snap_matches_mapartcraft',
                'test_mapart_staircase_toggle', 'test_mapart_staircase_off_convert_undo', 'test_mapart_save_load_and_leave',
                'test_mapart_import_snaps', 'test_mapart_resize_whole_maps']),
    'gallery': ('Hub/gallery and saving: projectStore, IndexedDB, goToMainMenu, saveCurrentStateToStore, openProjectFromStore, gallery long-press menu (#gallery-ctx-menu).',
                ['test_resize_from_gallery']),
}
# Editing any of these can break every group: run them all.
SHARED_CODE = 'PixelLayer / ImageLayer classes, plot() / layer.plot(), bulkPixelWrite, history (pushUndo, beginEdit, commitEdit, undo, redo), layoutAll / camera, boot / init, the canvas gesture handlers (onStart, onMove, onEnd), CSS shared by many screens.'

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
    check('static: declares <meta charset="utf-8"> (emoji/symbols break without it)', re.search(r'<meta charset="utf-8">', html[:400], re.I))
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
    await pg.wait_for_timeout(400)
    # V2_1: Pixel Art's Create Canvas opens the resize screen at 32x32; confirm it.
    await pg.locator('#rsConfirmBtn').click()
    await pg.wait_for_timeout(800)

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
async def test_zoom_indicator(pg):
    txt = lambda: pg.evaluate("() => document.getElementById('zoomIndicator').textContent")
    vis = await pg.evaluate("() => { const r = document.getElementById('zoomIndicator').getBoundingClientRect(); return r.width > 0 && r.height > 0; }")
    check('zoom-indicator: visible on the canvas screen', vis)
    check('zoom-indicator: shows current zoom', await txt() == await pg.evaluate("() => formatZoom(scale)"))
    await pg.evaluate("() => zoomIn()")
    check('zoom-indicator: updates on zoom in', await txt() == await pg.evaluate("() => formatZoom(scale)"))
    await pg.evaluate("() => { cameraScale = 1.5; applyCameraTransform(); }")
    check('zoom-indicator: live during pinch', await txt() == await pg.evaluate("() => formatZoom(scale * 1.5)"))
    await pg.evaluate("() => { cameraScale = 1; applyCameraTransform(); }")
    check('zoom-indicator: below 1x shows percent', await pg.evaluate("() => formatZoom(0.25) === '25%'"))

async def test_boot_and_canvas(pg):
    check('boot: 32x32 pixel canvas created', await pg.evaluate("() => gridW === 32 && gridH === 32 && activeLayer().type === 'pixel'"))

async def test_pencil_and_undo(pg):
    await pg.evaluate("() => { handleToolBtn('pencil'); selectedColor = '#112233'; }")
    await tap(pg, 5, 5)
    check('pencil: tap draws a pixel', await px(pg, 5, 5) == '#112233', await px(pg, 5, 5))
    await pg.evaluate("() => undo()")
    check('pencil: undo removes it', await px(pg, 5, 5) is None)

LAYER_ORDER = "() => [...document.querySelectorAll('#layersList .layer-row')].map(r => r.querySelector('.layer-name') ? r.querySelector('.layer-name').innerText : '?')"

async def open_layers_full(pg, n_extra=2):
    for _ in range(n_extra):
        await pg.evaluate("() => addPixelLayer()")
    await pg.evaluate("() => { layers.forEach((l, i) => l.name = 'L' + i); openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }")
    await pg.wait_for_timeout(350)

async def drag_row(pg, from_idx, to_y_fn, hold=True, cancel=False):
    rows = pg.locator('#layersList .layer-row')
    b = await rows.nth(from_idx).bounding_box()
    x, y = b['x'] + b['width'] * 0.75, b['y'] + b['height'] / 2
    await pg.mouse.move(x, y); await pg.mouse.down()
    if hold: await pg.wait_for_timeout(380)
    ty = await to_y_fn()
    steps = 8
    for k in range(1, steps + 1):
        await pg.mouse.move(x, y + (ty - y) * k / steps); await pg.wait_for_timeout(30)
    return x, ty

async def test_layers_drawer_modes(pg):
    await open_layers_full(pg, 1)
    box = await pg.locator('#panel-layers').bounding_box()
    check('layers drawer: sits on the right side', box and box['x'] + box['width'] > 990 and box['x'] > 500, box)
    check('layers drawer: no backdrop covering the canvas', not await pg.evaluate("() => document.getElementById('panelBackdrop').classList.contains('open')"))
    check('layers drawer: full mode shows settings for the selected layer', await pg.locator('#layerSettingsPane .layer-settings-title').count() == 1)
    check('layers drawer: rows have no up/down arrows any more', await pg.evaluate("() => [...document.querySelectorAll('#layersList .layer-row')].every(r => !/\\u2B06|\\u2B07/.test(r.innerText))"))
    check('layers drawer: bin and broom live in the settings', await pg.evaluate("() => /\\u{1F5D1}/u.test(document.getElementById('layerSettingsPane').innerText) && /\\u{1F9F9}/u.test(document.getElementById('layerSettingsPane').innerText)"))
    check('layers drawer: no sideways scrolling', await pg.evaluate("() => { const p = document.getElementById('layersTopPane'); return p.scrollWidth <= p.clientWidth + 1; }"))
    small = await pg.evaluate("() => [...document.querySelectorAll('#panel-layers .layers-icon-btn, #panel-layers .layers-hdr-btn')].filter(b => b.offsetParent && (b.getBoundingClientRect().height < 44)).length")
    check('layers drawer: icon buttons at least 44px tall', small == 0, small)
    await pg.locator('#layersWidthBtn').click(); await pg.wait_for_timeout(300)
    w = (await pg.locator('#panel-layers').bounding_box())['width']
    check('layers drawer: collapses to a thin strip', w < 120, w)
    check('layers drawer: strip hides the settings pane', not await pg.locator('#layersTopPane').is_visible())
    act = pg.locator('#layersList .layer-row.active-layer')
    await act.click(); await pg.wait_for_timeout(300)
    check('layers drawer: tapping the selected thumbnail widens it', not await pg.evaluate("() => isLayersStrip()"))
    check('layers drawer: mode is remembered', await pg.evaluate("() => JSON.parse(localStorage.getItem(LAYERS_DRAWER_PREFS_KEY)).mode === 'full'"))

async def test_layers_drawer_hides_while_drawing(pg):
    await open_layers_full(pg, 0)
    x1, y1 = await grid_point(pg, 5, 5); x2, y2 = await grid_point(pg, 8, 8); x3, y3 = await grid_point(pg, 12, 12)
    await pg.mouse.move(x1, y1); await pg.mouse.down(); await pg.wait_for_timeout(50)
    check('layers drawer: hides while a stroke is down', await pg.evaluate("() => document.getElementById('panel-layers').classList.contains('stroke-hidden')"))
    await pg.mouse.move(x2, y2); await pg.mouse.up(); await pg.wait_for_timeout(50)
    check('layers drawer: comes back after the stroke', await pg.evaluate("() => openPanelName === 'layers' && !document.getElementById('panel-layers').classList.contains('stroke-hidden')"))
    check('layers drawer: the stroke was drawn', await px(pg, 5, 5) is not None)
    await pg.evaluate("() => setLayersDrawerMode('full')"); await pg.wait_for_timeout(300)
    await pg.locator('#layersReturnPrefBtn').click(); await pg.wait_for_timeout(100)
    await pg.mouse.move(x3, y3); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(50)
    check('layers drawer: with the setting off it stays closed', await pg.evaluate("() => openPanelName === null"))

async def test_layers_drag_reorder(pg):
    await open_layers_full(pg, 2)
    before = await pg.evaluate(LAYER_ORDER)
    check('drag: starts as L2, L1, L0 from the top', before == ['L2', 'L1', 'L0'], before)
    async def above_top():
        b = await pg.locator('#layersList .layer-row').nth(0).bounding_box(); return b['y'] + 4
    x, _ = await drag_row(pg, 2, above_top)
    check('drag: a floating copy follows the finger', await pg.locator('.layer-drag-ghost').count() == 1)
    await pg.mouse.up(); await pg.wait_for_timeout(300)
    after = await pg.evaluate(LAYER_ORDER)
    check('drag: bottom layer dropped on top', after == ['L0', 'L2', 'L1'], after)
    check('drag: ghost removed after drop', await pg.locator('.layer-drag-ghost').count() == 0)
    check('drag: one undo step', await pg.evaluate("() => { undo(); renderLayersPanel(); return true; }") and await pg.evaluate(LAYER_ORDER) == ['L2', 'L1', 'L0'], await pg.evaluate(LAYER_ORDER))
    async def below_bottom():
        b = await pg.locator('#layersList .layer-row').nth(2).bounding_box(); return b['y'] + b['height'] - 4
    await drag_row(pg, 0, below_bottom); await pg.mouse.up(); await pg.wait_for_timeout(300)
    after2 = await pg.evaluate(LAYER_ORDER)
    check('drag: top layer dropped at the bottom', after2 == ['L1', 'L0', 'L2'], after2)
    async def far_below():
        b = await pg.locator('#layersListPane').bounding_box(); return b['y'] + b['height'] + 120
    await drag_row(pg, 1, far_below); await pg.mouse.up(); await pg.wait_for_timeout(300)
    after3 = await pg.evaluate(LAYER_ORDER)
    check('drag: dragging past the end of the list lands at the bottom', after3 == ['L1', 'L2', 'L0'], after3)
    b0 = await pg.locator('#layersList .layer-row').nth(0).bounding_box()
    await pg.mouse.move(b0['x'] + b0['width'] * 0.75, b0['y'] + 10); await pg.mouse.down(); await pg.mouse.move(b0['x'] + b0['width'] * 0.75, b0['y'] + 60, steps=4); await pg.mouse.up(); await pg.wait_for_timeout(300)
    check('drag: a quick swipe without holding does not reorder', await pg.evaluate(LAYER_ORDER) == after3)

async def test_layers_drag_into_group_and_cancel(pg):
    await open_layers_full(pg, 1)
    await pg.evaluate("() => { addEmptyGroup(); const f = frames[activeFrameIndex]; const g = f.layerTree.find(n => n.kind === 'group'); g.name = 'G'; renderLayersPanel(); }")
    await pg.wait_for_timeout(200)
    names = await pg.evaluate(LAYER_ORDER)
    gi = names.index('G')
    li = len(names) - 1
    async def on_group():
        b = await pg.locator('#layersList .layer-row').nth(gi).bounding_box(); return b['y'] + b['height'] / 2
    await drag_row(pg, li, on_group); await pg.wait_for_timeout(500)
    check('drag: hovering over a group highlights it', await pg.locator('#layersList .layer-row.drop-inside').count() == 1)
    await pg.mouse.up(); await pg.wait_for_timeout(300)
    inside = await pg.evaluate("() => { const g = frames[activeFrameIndex].layerTree.find(n => n.kind === 'group'); return g ? g.children.map(n => n.layer && n.layer.name) : null; }")
    check('drag: layer dropped inside the group', inside == ['L0'], inside)
    order0 = await pg.evaluate(LAYER_ORDER)
    async def top():
        b = await pg.locator('#layersList .layer-row').nth(0).bounding_box(); return b['y'] + 4
    await drag_row(pg, len(order0) - 1, top)
    await pg.evaluate("() => document.dispatchEvent(new PointerEvent('pointercancel', { pointerId: 1, bubbles: true }))")
    await pg.wait_for_timeout(100)
    await pg.mouse.up(); await pg.wait_for_timeout(200)
    check('drag: a cancelled drag changes nothing', await pg.evaluate(LAYER_ORDER) == order0, await pg.evaluate(LAYER_ORDER))
    check('drag: a cancelled drag leaves no ghost or shifted rows', await pg.evaluate("() => !document.querySelector('.layer-drag-ghost') && [...document.querySelectorAll('#layersList .layer-row')].every(r => !r.style.transform) && treeDragState === null"))
    async def top2():
        b = await pg.locator('#layersList .layer-row').nth(0).bounding_box(); return b['y'] + 4
    cur = await pg.evaluate(LAYER_ORDER)
    await drag_row(pg, cur.index('L0'), top2); await pg.mouse.up(); await pg.wait_for_timeout(300)
    out = await pg.evaluate("() => frames[activeFrameIndex].layerTree.find(n => n.kind === 'group').children.length")
    check('drag: layer dragged back out of the group', out == 0, [out, await pg.evaluate(LAYER_ORDER), order0])

async def test_layers_debug_on_top(pg):
    await open_layers_full(pg, 0)
    await pg.locator('#debugFab').click(); await pg.wait_for_timeout(300)
    check('debug: opening Debug keeps the layers drawer open', await pg.evaluate("() => openPanelName === 'layers' && drawerOpenName === 'debug'"))
    z = await pg.evaluate("() => [getComputedStyle(document.getElementById('debugDrawer')).zIndex, getComputedStyle(document.getElementById('panel-layers')).zIndex].map(Number)")
    check('debug: drawer sits above the layers drawer', z[0] > z[1], z)
    fz = await pg.evaluate("() => Number(getComputedStyle(document.getElementById('debugFab')).zIndex)")
    check('debug: debug button sits above every drawer', fz > z[0], fz)
    await pg.evaluate("() => { closeDrawer(); openDrawer('tools'); }")
    b = await pg.locator('#debugFab').bounding_box()
    hit = await pg.evaluate("([x, y]) => document.elementFromPoint(x, y) && document.elementFromPoint(x, y).id", [b['x'] + 20, b['y'] + 20])
    check('debug: debug button still tappable with the tools drawer open', hit == 'debugFab', hit)

async def test_layers_back_to_strip_and_done(pg):
    await open_layers_full(pg, 0)
    x1, y1 = await grid_point(pg, 4, 4)
    await pg.mouse.move(x1, y1); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(100)
    check('layers drawer: after a stroke it comes back as the strip', await pg.evaluate("() => isLayersStrip() && openPanelName === 'layers'"))
    await pg.evaluate("() => { setLayersDrawerMode('full'); toggleLayerSelectionMode(); }"); await pg.wait_for_timeout(200)
    hdr = pg.locator('#layersQuickAddBtn')
    check('selection mode: header button becomes a blue Done', await hdr.inner_text() == 'Done' and await pg.evaluate("() => document.getElementById('layersQuickAddBtn').classList.contains('done')"))
    done = pg.locator('#layerSelectionDoneBtn')
    db = await done.bounding_box()
    check('selection mode: big Done button at the top of the actions', db and db['height'] >= 44 and await done.is_visible(), db)
    await hdr.click(); await pg.wait_for_timeout(200)
    check('selection mode: header Done leaves selection mode', await pg.evaluate("() => !layerSelectionMode") and await hdr.inner_text() == '＋')

async def test_drawer_splits_collapse_on_phone(pg):
    await pg.set_viewport_size({'width': 390, 'height': 844}); await pg.wait_for_timeout(200)
    await open_layers_full(pg, 0)
    h = pg.locator('#layersSplitHandle')
    await pg.locator('#layersDrawerHeader .layers-drawer-title').click(); await pg.wait_for_timeout(500)
    hb = await h.bounding_box()
    check('split: collapses to a 12px strip after tapping elsewhere', hb and abs(hb['height'] - 12) < 1.5, hb)
    await pg.mouse.move(hb['x'] + hb['width'] / 2, hb['y'] + 6); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(400)
    hb2 = await h.bounding_box()
    check('split: tapping the strip opens it to 44px', hb2 and abs(hb2['height'] - 44) < 1.5, hb2)
    await pg.evaluate("() => { closePanel(); openDrawer('debug'); }"); await pg.wait_for_timeout(500)
    check('split: debug drawer divider uses the same collapsing split', await pg.evaluate("() => document.getElementById('debugDrawerSplitHandle').classList.contains('cdsplit')"))
    db = await pg.locator('#debugDrawerSplitHandle').bounding_box()
    check('split: debug divider is 44px or a 12px strip', db and (abs(db['height'] - 12) < 1.5 or abs(db['height'] - 44) < 1.5), db)
    await pg.set_viewport_size({'width': 1000, 'height': 800})

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

# ---------------------------------------------------------------- resize screen (V2_0)
async def rs_point(pg, gx, gy):
    """Screen position of grid point (gx, gy) on the resize screen."""
    return await pg.evaluate(f"""() => {{ const b = document.getElementById('rsCanvas').getBoundingClientRect();
        const [x, y] = rsToScreen({gx}, {gy}); return [b.left + x, b.top + y]; }}""")

async def rs_drag(pg, a, b):
    await pg.mouse.move(*(await rs_point(pg, *a))); await pg.mouse.down()
    await pg.mouse.move(*(await rs_point(pg, *b)), steps=8); await pg.mouse.up()
    await pg.wait_for_timeout(60)

async def rs_open_from_file_panel(pg):
    await pg.locator('#tab-file').click(); await pg.wait_for_timeout(250)
    await pg.locator('#fileResizeBtn').click(); await pg.wait_for_timeout(250)

RECT = "() => [RS.rect.x, RS.rect.y, RS.rect.w, RS.rect.h]"
SCREEN_OPEN = "() => document.getElementById('resizeScreen').style.display === 'flex'"

async def test_resize_offset_engine(pg):
    await pg.evaluate(DRAW, [[[0, 0]], '#ABCDEF'])
    await pg.evaluate("() => applyCanvasResizeOffset(40, 40, 5, 3)")
    check('offset engine: old (0,0) lands at (5,3)', await px(pg, 5, 3) == '#ABCDEF' and await px(pg, 0, 0) is None)
    await pg.evaluate("() => applyCanvasResizeOffset(40, 40, -5, -3)")
    check('offset engine: same size, shifted back (negative offset crops top/left)', await px(pg, 0, 0) == '#ABCDEF')
    await pg.evaluate("() => { undo(); undo(); }")
    check('offset engine: undo twice restores 32x32', await pg.evaluate("() => gridW === 32 && gridH === 32") and await px(pg, 0, 0) == '#ABCDEF')

async def test_resize_screen_grow_edge(pg):
    await rs_open_from_file_panel(pg)
    check('screen: File panel button opens it', await pg.evaluate(SCREEN_OPEN))
    check('screen: rectangle starts as the canvas', await pg.evaluate(RECT) == [0, 0, 32, 32])
    await rs_drag(pg, (32, 16), (40.2, 16))
    check('screen: dragging the right handle grows to 40 x 32', await pg.evaluate(RECT) == [0, 0, 40, 32], await pg.evaluate(RECT))
    sz = await pg.evaluate("() => document.getElementById('rsSize').textContent")
    check('screen: info shows the new size', sz == '40 \u00d7 32', repr(sz))
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(200)
    check('screen: confirm (no crop) applies in one tap', await pg.evaluate("() => gridW === 40 && gridH === 32"))
    check('screen: from the editor it returns to the editor', not await pg.evaluate(SCREEN_OPEN) and await pg.evaluate("() => document.getElementById('pixel-canvas-screen').style.display !== 'none'"))

async def test_resize_screen_draw_outside(pg):
    await pg.evaluate(DRAW, [[[0, 0]], '#ABCDEF'])
    await rs_open_from_file_panel(pg)
    await rs_drag(pg, (-4.1, -4.1), (36.1, 36.1))
    check('screen: drawing outside makes a new 40 x 40 rectangle at (-4,-4)', await pg.evaluate(RECT) == [-4, -4, 40, 40], await pg.evaluate(RECT))
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(200)
    check('screen: confirm adds 4 px on every side', await pg.evaluate("() => gridW === 40 && gridH === 40") and await px(pg, 4, 4) == '#ABCDEF')

async def test_resize_screen_move_inside(pg):
    await rs_open_from_file_panel(pg)
    await rs_drag(pg, (16, 16), (21, 13))
    check('screen: dragging inside moves the rectangle', await pg.evaluate(RECT) == [5, -3, 32, 32], await pg.evaluate(RECT))

async def test_resize_screen_crop_two_taps(pg):
    await pg.evaluate(DRAW, [[[2, 2], [30, 30]], '#ABCDEF'])
    await rs_open_from_file_panel(pg)
    await rs_drag(pg, (32, 32), (16.1, 16.1))
    check('screen: corner drag shrinks to 16 x 16', await pg.evaluate(RECT) == [0, 0, 16, 16], await pg.evaluate(RECT))
    check('screen: info warns about the crop', 'crops 1 px' in await pg.locator('#rsDetail').inner_text(), await pg.locator('#rsDetail').inner_text())
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(100)
    label = await pg.locator('#rsConfirmBtn').inner_text()
    check('screen: first tap on a crop only arms ("tap again")', 'TAP AGAIN' in label and await pg.evaluate("() => gridW === 32"), label)
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(200)
    check('screen: second tap crops to 16 x 16', await pg.evaluate("() => gridW === 16 && gridH === 16") and await px(pg, 2, 2) == '#ABCDEF')
    await pg.evaluate("() => undo()")
    check('screen: one undo brings the cropped pixel back', await px(pg, 30, 30) == '#ABCDEF')

async def test_resize_screen_discard(pg):
    await rs_open_from_file_panel(pg)
    await rs_drag(pg, (32, 16), (50.2, 16))
    await pg.locator('#rsDiscardBtn').click(); await pg.wait_for_timeout(150)
    check('screen: discard closes it and changes nothing', not await pg.evaluate(SCREEN_OPEN) and await pg.evaluate("() => gridW === 32 && gridH === 32"))

async def test_resize_screen_lock_ratio(pg):
    await rs_open_from_file_panel(pg)
    await pg.locator('#rsLockBtn').click()
    await rs_drag(pg, (32, 16), (48.2, 16))
    check('screen: lock ratio, right edge to 48 makes 48 x 48', (await pg.evaluate(RECT))[2:] == [48, 48], await pg.evaluate(RECT))

async def test_resize_screen_snap(pg):
    await rs_open_from_file_panel(pg)
    await pg.locator('#rsSnapBtn').click()
    await rs_drag(pg, (32, 16), (46.8, 16))
    check('screen: snap pulls 47 to the common size 48', (await pg.evaluate(RECT))[2] == 48, await pg.evaluate(RECT))
    await pg.locator('#rsLockBtn').click()  # lock at 48:32 = 3:2
    await rs_drag(pg, (48, 16), (63.6, 16))
    r = await pg.evaluate(RECT)
    check('screen: snap + lock: width snaps to 64, height follows the ratio (43)', r[2:] == [64, 43], r)
    check('screen: info says the height is off a common size', 'height not a common size' in await pg.locator('#rsDetail').inner_text())

async def test_resize_screen_second_finger_guard(pg):
    await rs_open_from_file_panel(pg)
    x, y = await rs_point(pg, 32, 16)
    r = await pg.evaluate("""([x, y]) => { const c = document.getElementById('rsCanvas');
        const ev = (type, id, cx, cy) => c.dispatchEvent(new PointerEvent(type, {pointerId: id, clientX: cx, clientY: cy, bubbles: true, pointerType: 'touch', isPrimary: id === 1}));
        ev('pointerdown', 1, x, y); ev('pointermove', 1, x + 120, y);
        const mid = [RS.rect.w];
        ev('pointerdown', 2, x - 200, y + 80);
        const after = [RS.rect.x, RS.rect.y, RS.rect.w, RS.rect.h];
        ev('pointerup', 2, x - 200, y + 80); ev('pointerup', 1, x + 120, y);
        return {mid, after}; }""", [x, y])
    check('screen: one finger was mid-drag', r['mid'][0] > 32, r)
    check('screen: a second finger puts the rectangle back (stray touch guard)', r['after'] == [0, 0, 32, 32], r)

async def test_resize_screen_numbers_button(pg):
    await rs_open_from_file_panel(pg)
    await pg.locator('#rsNumbersBtn').click(); await pg.wait_for_timeout(150)
    check('numbers: opens the sheet on top of the screen', await pg.evaluate("() => document.getElementById('resize-canvas-modal').classList.contains('open')"))
    await pg.evaluate("() => { setResizeDimension('w', 48); setResizeDimension('h', 24); }")
    await pg.locator('.resize-anchor-btn[data-anchor="0,0"]').click()
    await pg.locator('#resize-apply-btn').click(); await pg.wait_for_timeout(150)
    check('numbers: apply moves the rectangle, not the canvas', await pg.evaluate(RECT) == [0, 0, 48, 24] and await pg.evaluate("() => gridW === 32"), await pg.evaluate(RECT))
    check('numbers: screen still open afterwards', await pg.evaluate(SCREEN_OPEN))

async def test_resize_portrait_sprite_use_sheet(pg):
    for prof in ('portrait', 'sprite'):
        r = await pg.evaluate(f"""() => {{ const keep = selectedProfile; selectedProfile = '{prof}';
            openResizeFor('auto', 'editor');
            const out = {{screen: document.getElementById('resizeScreen').style.display === 'flex',
                          sheet: document.getElementById('resize-canvas-modal').classList.contains('open')}};
            closeResizeCanvasSheet(false); selectedProfile = keep; return out; }}""")
        check(f'profiles: {prof} gets the number sheet, not the new screen', r == {'screen': False, 'sheet': True}, r)

async def test_resize_prefs(pg):
    await pg.evaluate("() => { resizePrefs.opens = 'sheet'; saveResizePrefs(); }")
    await pg.locator('#tab-file').click(); await pg.wait_for_timeout(250)
    await pg.locator('#fileResizeBtn').click(); await pg.wait_for_timeout(200)
    check('prefs: "opens: number sheet" makes the File button open the sheet', await pg.evaluate("() => document.getElementById('resize-canvas-modal').classList.contains('open')") and not await pg.evaluate(SCREEN_OPEN))
    await pg.evaluate("() => { closeResizeCanvasSheet(false); resizePrefs.opens = 'screen'; resizePrefs.both = true; saveResizePrefs(); }")
    check('prefs: "both items" shows the second File button', await pg.locator('#fileResizeNumbersBtn').is_visible())
    check('prefs: "both items" shows the second long-press item', await pg.evaluate("() => document.getElementById('ctx-resize-numbers').style.display !== 'none'"))
    await pg.evaluate("() => { resizePrefs.both = false; saveResizePrefs(); }")

async def test_resize_from_gallery(pg):
    await pg.evaluate(DRAW, [[[0, 0]], '#ABCDEF'])
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(600)
    pid = await pg.evaluate("() => projectStore[0] && projectStore[0].id")
    check('gallery: project saved to the hub', bool(pid))
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-resize').click(); await pg.wait_for_timeout(900)
    check('gallery: long-press Resize Canvas opens the new screen', await pg.evaluate(SCREEN_OPEN))
    await rs_drag(pg, (32, 32), (40.2, 40.2))
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(700)
    check('gallery: confirm goes back to the hub', await pg.evaluate("() => document.getElementById('gallery-screen').style.display === 'flex'") and not await pg.evaluate(SCREEN_OPEN))
    meta = await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); return [p.gridW, p.gridH]; }", pid)
    check('gallery: the saved project is now 40 x 40', meta == [40, 40], meta)
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-resize').click(); await pg.wait_for_timeout(900)
    await rs_drag(pg, (40, 40), (60.2, 60.2))
    await pg.locator('#rsDiscardBtn').click(); await pg.wait_for_timeout(500)
    meta = await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); return [p.gridW, p.gridH]; }", pid)
    check('gallery: discard goes back to the hub without saving', meta == [40, 40] and await pg.evaluate("() => document.getElementById('gallery-screen').style.display === 'flex'"), meta)

# ---------------------------------------------------------------- new canvas (V2_1)
async def open_new_canvas_sheet(pg):
    await pg.goto(BASE_URL + 'Pixel_Art_App.html'); await pg.wait_for_timeout(1200)
    await pg.get_by_text('NEW CANVAS').click(); await pg.wait_for_timeout(500)

async def test_new_canvas_size_on_screen(pg):
    await open_new_canvas_sheet(pg)
    check('new canvas: Pixel Art hides the size boxes', not await pg.locator('#newCanvasSizeBox').is_visible())
    await pg.locator('#newCanvasCreateBtn').click(); await pg.wait_for_timeout(400)
    check('new canvas: Create Canvas opens the resize screen at 32 x 32', await pg.evaluate(SCREEN_OPEN) and await pg.evaluate(RECT) == [0, 0, 32, 32])
    check('new canvas: info says "new canvas"', 'new canvas' in await pg.locator('#rsDetail').inner_text())
    await rs_drag(pg, (32, 32), (48.2, 24.2))
    check('new canvas: corner drag sets 48 x 24', await pg.evaluate(RECT) == [0, 0, 48, 24], await pg.evaluate(RECT))
    await pg.locator('#rsConfirmBtn').click(); await pg.wait_for_timeout(400)
    check('new canvas: confirm makes a 48 x 24 canvas in one tap', await pg.evaluate("() => gridW === 48 && gridH === 24 && activeLayer().gridW === 48"))
    check('new canvas: no undo entry for choosing the size', await pg.evaluate("() => undoStack.length === 0"))
    check('new canvas: editor is showing', await pg.evaluate("() => document.getElementById('pixel-canvas-screen').style.display !== 'none'") and not await pg.evaluate(SCREEN_OPEN))

async def test_new_canvas_discard(pg):
    await open_new_canvas_sheet(pg)
    await pg.locator('#newCanvasCreateBtn').click(); await pg.wait_for_timeout(400)
    await pg.locator('#rsDiscardBtn').click(); await pg.wait_for_timeout(400)
    check('new canvas: discard goes back to the hub', await pg.evaluate("() => document.getElementById('gallery-screen').style.display === 'flex'") and not await pg.evaluate(SCREEN_OPEN))
    check('new canvas: discard creates no project', await pg.evaluate("() => projectStore.length === 0"))

async def test_new_canvas_portrait_keeps_fields(pg):
    await open_new_canvas_sheet(pg)
    await pg.locator('#new-canvas-sheet .new-canvas-modal-profile-btn[data-profile="portrait"]').dispatch_event('pointerup')
    await pg.wait_for_timeout(150)
    check('new canvas: Portrait shows the size boxes', await pg.locator('#newCanvasSizeBox').is_visible())
    await pg.locator('#newCanvasCreateBtn').click(); await pg.wait_for_timeout(800)
    check('new canvas: Portrait creates directly (no resize screen), 40 x 40', not await pg.evaluate(SCREEN_OPEN) and await pg.evaluate("() => gridW === 40 && gridH === 40"))


async def mapart_canvas(pg, w=1, h=1):
    await open_new_canvas_sheet(pg)
    await pg.locator('#new-canvas-sheet .new-canvas-modal-profile-btn[data-profile="mapart"]').dispatch_event('pointerup')
    await pg.wait_for_timeout(150)
    await pg.locator('#newCanvasSizeBox input').nth(0).fill(str(w))
    await pg.locator('#newCanvasSizeBox input').nth(1).fill(str(h))
    await pg.locator('#newCanvasCreateBtn').click(); await pg.wait_for_timeout(800)

SWATCHES = "() => [...document.querySelectorAll('#palette .swatch-wrapper:not(#transparencyWrapper):not(#pickerContainer) .swatch')].map(e => rgbToHex(e.style.backgroundColor).toUpperCase())"

async def test_mapart_new_canvas_in_maps(pg):
    await open_new_canvas_sheet(pg)
    await pg.locator('#new-canvas-sheet .new-canvas-modal-profile-btn[data-profile="mapart"]').dispatch_event('pointerup')
    await pg.wait_for_timeout(150)
    check('mapart new canvas: size boxes shown, in maps', await pg.locator('#newCanvasSizeBox').is_visible() and 'maps' in (await pg.locator('#newCanvasSizeBox').inner_text()).lower())
    await pg.locator('#newCanvasSizeBox input').nth(0).fill('2')
    await pg.locator('#newCanvasSizeBox input').nth(1).fill('9')
    await pg.locator('#newCanvasCreateBtn').click(); await pg.wait_for_timeout(800)
    check('mapart new canvas: 2 x 9 maps clamps to 256 x 896 px, no resize screen', not await pg.evaluate(SCREEN_OPEN) and await pg.evaluate("() => gridW === 256 && gridH === 896 && selectedProfile === 'mapart'"), await pg.evaluate("() => [gridW, gridH]"))
    check('mapart new canvas: pixel layer (not image layer)', await pg.evaluate("() => activeLayer().type === 'pixel'"))

async def test_mapart_resize_sheet_in_maps(pg):
    await test_mapart_new_canvas_in_maps(pg)
    await pg.evaluate("() => openResizeCanvasSheet()")
    w = pg.locator('#resize-new-w'); h = pg.locator('#resize-new-h')
    check('mapart resize sheet: fields show maps', await w.input_value() == '2' and await h.input_value() == '7', [await w.input_value(), await h.input_value()])
    check('mapart resize sheet: current size in maps', 'maps' in await pg.locator('#resize-current-size').inner_text())
    await w.fill('3'); await h.fill('9'); await h.blur()
    check('mapart resize sheet: 9 maps clamps to 7', await h.input_value() == '7')
    await h.focus(); await pg.keyboard.type('4')
    check('mapart resize sheet: typing a digit replaces the number', await h.input_value() == '4', await h.input_value())
    await h.fill('7')
    check('mapart resize sheet: unchanged height greys out top and bottom anchors', await pg.evaluate("() => [...document.querySelectorAll('.resize-anchor-btn')].filter(b => b.disabled).map(b => b.dataset.anchor).sort().join(' ') === '.5,0 .5,1 0,0 0,1 1,0 1,1'"))
    await pg.locator('#resize-apply-btn').click(); await pg.wait_for_timeout(400)
    check('mapart resize sheet: 3 x 7 maps = 384 x 896 px', await pg.evaluate("() => gridW === 384 && gridH === 896"), await pg.evaluate("() => [gridW, gridH]"))

async def test_resize_sheet_no_autoselect_outside_mapart(pg):
    await pg.evaluate("() => openResizeCanvasSheet()")
    w = pg.locator('#resize-new-w')
    await w.focus(); await pg.wait_for_timeout(50); await pg.keyboard.type('4')
    check('resize sheet: outside Mapart, typing adds to the number (no auto-highlight)', await w.input_value() == '324', await w.input_value())

async def test_mapart_palette_locked(pg):
    await mapart_canvas(pg)
    sw = await pg.evaluate(SWATCHES)
    check('mapart palette: 61 flat map colours', len(sw) == 61 and len(set(sw)) == 61, len(sw))
    check('mapart palette: free colour picker hidden', await pg.evaluate("() => document.getElementById('pickerContainer').style.display === 'none'"))
    check('mapart palette: manage / swatch array hidden, staircase row shown', await pg.evaluate("() => document.getElementById('manageBtn').parentElement.style.display === 'none' && document.getElementById('mapartPaletteRow').style.display === ''"))
    await pg.evaluate("() => createSwatch('#123456')")
    check('mapart palette: adding an off-palette colour adds nothing', len(await pg.evaluate(SWATCHES)) == 61)
    await pg.evaluate("() => replaceVisiblePalette(['#000000'])")
    check('mapart palette: replacing the palette is refused', len(await pg.evaluate(SWATCHES)) == 61)
    await pg.evaluate(DRAW, [[[3, 3]], '#FF0001'])
    check('mapart palette: drawing an off-palette colour stores the nearest map colour', await px(pg, 3, 3) == '#DC0000', await px(pg, 3, 3))
    await pg.evaluate(DRAW, [[[4, 4]], 'rgba(10,10,10,0.3)'])
    check('mapart palette: mostly transparent paint becomes no block', await px(pg, 4, 4) is None)
    check('mapart palette: soft brush / colour to alpha hidden', await pg.evaluate("() => ['softBrushToolBtn','softEraserToolBtn','colorToAlphaToolBtn'].every(id => { const e = document.getElementById(id); return !e || e.style.display === 'none'; })"))

async def test_mapart_snap_matches_mapartcraft(pg):
    await mapart_canvas(pg)
    ref = [[[255,0,0],"#DC0000","#FF0000"],[[0,255,0],"#00BB32","#00D93A"],[[0,0,255],"#3737DC","#4040FF"],[[255,255,255],"#DCDCDC","#FFFFFF"],[[0,0,0],"#151515","#111111"],[[128,64,200],"#9941BA","#7F3FB2"],[[250,200,30],"#D7CD42","#D7CD42"],[[17,34,51],"#151515","#191919"]]
    got = await pg.evaluate("""(ref) => { const out = []; ref.forEach(([c]) => out.push(mapartSnapRGB(c[0], c[1], c[2])));
        mapartStaircase = true; mapartResetPaletteCache(); ref.forEach(([c]) => out.push(mapartSnapRGB(c[0], c[1], c[2])));
        mapartStaircase = false; mapartResetPaletteCache(); return out; }""", ref)
    want = [r[1] for r in ref] + [r[2] for r in ref]
    check('mapart snap: same picks as mapartcraft default (flat and staircase)', got == want, [got, want])

async def test_mapart_staircase_toggle(pg):
    await mapart_canvas(pg)
    await pg.evaluate("() => toggleMapartStaircase()")
    sw = await pg.evaluate(SWATCHES)
    check('mapart staircase: on shows 183 colours', len(sw) == 183, len(sw))
    check('mapart staircase: button and hint say so', await pg.evaluate("() => document.getElementById('mapartStaircaseBtn').textContent === 'STAIRCASE: ON' && document.getElementById('mapartPaletteHint').textContent.startsWith('183')"))
    await pg.evaluate(DRAW, [[[2, 2]], '#FF0000'])
    check('mapart staircase: light shade can be drawn', await px(pg, 2, 2) == '#FF0000')
    await pg.evaluate("() => toggleMapartStaircase()")
    check('mapart staircase: turning off with shaded pixels asks first', await pg.evaluate("() => document.getElementById('mapartStaircaseOffBox').style.display === '' && mapartStaircase === true"))
    await pg.evaluate("() => resolveMapartStaircaseOff('cancel')")
    check('mapart staircase: cancel keeps staircase on', await pg.evaluate("() => mapartStaircase === true") and len(await pg.evaluate(SWATCHES)) == 183)
    await pg.evaluate("() => { toggleMapartStaircase(); resolveMapartStaircaseOff('keep'); }")
    check('mapart staircase: keep leaves the pixel and flags it', await px(pg, 2, 2) == '#FF0000' and len(await pg.evaluate(SWATCHES)) == 61 and 'staircase shades' in await pg.locator('#mapartPaletteHint').text_content())

async def test_mapart_staircase_off_convert_undo(pg):
    await mapart_canvas(pg)
    await pg.evaluate("() => toggleMapartStaircase()")
    await pg.evaluate(DRAW, [[[1, 1]], '#FF0000'])
    await pg.evaluate(DRAW, [[[2, 1]], '#B40000'])
    await pg.evaluate(DRAW, [[[3, 1]], '#DC0000'])
    await pg.evaluate("() => { toggleMapartStaircase(); resolveMapartStaircaseOff('convert'); }")
    check('mapart staircase convert: light and dark become the normal shade', [await px(pg, 1, 1), await px(pg, 2, 1), await px(pg, 3, 1)] == ['#DC0000'] * 3, [await px(pg, 1, 1), await px(pg, 2, 1)])
    await pg.evaluate("() => undo()")
    check('mapart staircase convert: one undo restores both shades', await px(pg, 1, 1) == '#FF0000' and await px(pg, 2, 1) == '#B40000' and await px(pg, 3, 1) == '#DC0000')
    await pg.evaluate("() => redo()")
    check('mapart staircase convert: redo converts again', await px(pg, 1, 1) == '#DC0000' and await px(pg, 2, 1) == '#DC0000')

async def test_mapart_save_load_and_leave(pg):
    await mapart_canvas(pg, 2, 1)
    await pg.evaluate("() => toggleMapartStaircase()")
    await pg.evaluate(DRAW, [[[5, 5]], '#FF0000'])
    data = await pg.evaluate("() => JSON.parse(JSON.stringify(currentProjectSaveData('m')))")
    check('mapart save: profile and staircase saved', data['profile'] == 'mapart' and data['mapartStaircase'] is True)
    await pg.evaluate("() => { mapartStaircase = false; selectProfile('pixelArt'); }")
    check('mapart leave: Pixel Art gets its own palette back and the picker returns', await pg.evaluate("() => document.getElementById('pickerContainer').style.display === '' && !document.getElementById('palette').classList.contains('mapart-locked')") and len(await pg.evaluate(SWATCHES)) != 61)
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data)
    await pg.wait_for_timeout(300)
    check('mapart load: reopens as mapart 256 x 128 with staircase on', await pg.evaluate("() => selectedProfile === 'mapart' && gridW === 256 && gridH === 128 && mapartStaircase === true") and len(await pg.evaluate(SWATCHES)) == 183)
    check('mapart load: pixel kept', await px(pg, 5, 5) == '#FF0000')

async def test_mapart_import_snaps(pg):
    await mapart_canvas(pg)
    ok = await pg.evaluate("""() => { const l = new PixelLayer('t', 128, 128); l.pixelData[0][0] = '#FF0001'; l.pixelData[1][0] = 'rgba(0,0,255,0.2)'; l.pixelData[2][0] = '#123456';
        mapartSnapLayerInPlace(l); return [l.pixelData[0][0], l.pixelData[1][0], l.pixelData[2][0]]; }""")
    check('mapart import: layer pixels snap to map colours, faint pixels become empty', ok[0] == '#DC0000' and ok[1] is None and ok[2] in await pg.evaluate("() => mapartAllowedHexes()"), ok)
    IMPORT = """([w, h]) => new Promise(res => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d');
        x.fillStyle = '#FF0102'; x.fillRect(0, 0, w, h); x.fillStyle = '#00FF00'; x.fillRect(0, 0, 1, 1);
        const img = new Image(); img.onload = () => { selectProfile('mapart'); importAsNewProjectFromImage(img, { name: 'pic.png' }); res(); }; img.src = c.toDataURL(); })"""
    await pg.evaluate(IMPORT, [256, 128]); await pg.wait_for_timeout(300)
    check('mapart import: 256 x 128 image opens as a 2 x 1 mapart, pixels snapped', await pg.evaluate("() => selectedProfile === 'mapart' && gridW === 256 && gridH === 128") and await px(pg, 0, 0) == '#00BB32' and await px(pg, 100, 100) == '#DC0000', [await px(pg, 0, 0), await px(pg, 100, 100)])
    await pg.evaluate(IMPORT, [200, 128]); await pg.wait_for_timeout(300)
    check('mapart import: 200 x 128 image falls back to Pixel Art, unsnapped', await pg.evaluate("() => selectedProfile === 'pixelArt' && gridW === 200") and await px(pg, 100, 100) == '#FF0102', await px(pg, 100, 100))
    check('mapart import: whole-map sizes accepted, others refused', await pg.evaluate("() => mapartDimensionsCompatible(256,128) && !mapartDimensionsCompatible(200,128) && !mapartDimensionsCompatible(1024,128)"))

async def test_mapart_resize_whole_maps(pg):
    await mapart_canvas(pg)
    await pg.evaluate("() => applyCanvasResizeOffset(300, 140, 0, 0)")
    check('mapart resize: snapped to whole maps (2 x 1)', await pg.evaluate("() => gridW === 256 && gridH === 128"), await pg.evaluate("() => [gridW, gridH]"))
    check('mapart resize: resize screen not offered', await pg.evaluate("() => !resizeScreenAllowed('mapart')"))

# ---------------------------------------------------------------- runner
BASE_URL = ''
SELECTED_GROUPS = list(GROUPS)
group_time, test_time = {}, []

def find_chrome():
    if os.environ.get('CHROME'): return os.environ['CHROME']
    for p in ('/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
              r'C:\Program Files\Google\Chrome\Application\chrome.exe'):
        if os.path.exists(p): return p
    return None  # fall back to Playwright's own Chromium

async def browser_checks():
    from playwright.async_api import async_playwright
    all_tests = {n: f for n, f in globals().items() if n.startswith('test_') and asyncio.iscoroutinefunction(f)}
    grouped = {t for _, (_, ts) in GROUPS.items() for t in ts}
    check('groups: every test belongs to a group', not (set(all_tests) - grouped), sorted(set(all_tests) - grouped))
    check('groups: every grouped test exists', not (grouped - set(all_tests)), sorted(grouped - set(all_tests)))
    tests = [(g, n, all_tests[n]) for g in SELECTED_GROUPS for n in GROUPS[g][1] if n in all_tests]
    only = os.environ.get('ONLY')  # e.g. ONLY=snap runs just the tests whose name contains it
    if only: tests = [(g, n, f) for g, n, f in tests if only in n]
    async with async_playwright() as p:
        exe = find_chrome()
        b = await p.chromium.launch(executable_path=exe, args=['--no-sandbox']) if exe else await p.chromium.launch()
        current = None
        for grp, name, fn in tests:
            if grp != current:
                if current: print(f'== group {current} took {fmt(group_time[current])}')
                current = grp; print(f'== group {grp}')
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
            took = time.perf_counter() - t0
            group_time[grp] = group_time.get(grp, 0) + took
            test_time.append((took, name))
            print(f'   {name} took {fmt(took)}')
            await ctx.close()
        if current: print(f'== group {current} took {fmt(group_time[current])}')
        await b.close()

def main():
    global BASE_URL, SELECTED_GROUPS
    args = sys.argv[1:]
    if '--list' in args:
        print('Groups (run: python3 tests/run_tests.py <group> [<group> ...])\n')
        for g, (what, ts) in GROUPS.items(): print(f'  {g:14} {len(ts):2} tests  {what}')
        print('\nShared code -- run everything after editing: ' + SHARED_CODE)
        return
    unknown = [a for a in args if a not in GROUPS and a != 'all']
    if unknown:
        print('Unknown group(s): ' + ', '.join(unknown) + '. Use --list to see them.'); sys.exit(2)
    if args and 'all' not in args: SELECTED_GROUPS = [g for g in GROUPS if g in args]
    print('groups: ' + ', '.join(SELECTED_GROUPS))
    t_all = time.perf_counter()
    t0 = time.perf_counter()
    print('== static checks'); static_checks()
    print(f'== static checks took {fmt(time.perf_counter() - t0)}')
    # Serve over HTTP (IndexedDB is unreliable on file://).
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=ROOT)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    BASE_URL = f'http://127.0.0.1:{srv.server_address[1]}/'
    t0 = time.perf_counter()
    print('== browser checks'); asyncio.run(browser_checks())
    print(f'== browser checks took {fmt(time.perf_counter() - t0)}')
    srv.shutdown()
    failed = [n for n, ok in results if not ok]
    print('\n== time per group: ' + ', '.join(f'{g} {fmt(group_time[g])}' for g in SELECTED_GROUPS if g in group_time))
    print('== slowest tests: ' + ', '.join(f'{n} {fmt(t)}' for t, n in sorted(test_time, reverse=True)[:3]))
    print(f'\n{len(results) - len(failed)} passed, {len(failed)} failed in {fmt(time.perf_counter() - t_all)}  (groups: {", ".join(SELECTED_GROUPS)})')
    sys.exit(1 if failed else 0)

if __name__ == '__main__':
    main()
