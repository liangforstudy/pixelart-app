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
                      ['test_layers_drawer_modes', 'test_layers_drawer_hides_while_drawing', 'test_layers_drag_reorder', 'test_layers_drag_into_group_and_cancel', 'test_layers_debug_on_top', 'test_layers_back_to_strip_and_done', 'test_drawer_splits_collapse_on_phone', 'test_layers_duplicate_reachable']),
    'palette': ('Colour swatches: createSwatch, handleManageClick edit mode, setupPaletteDragEvents drag-to-swap, delete badges.',
                ['test_palette_drag_swaps']),
    'transform': ('Transform screen (V2_6): xfOpen/xfClose/xfDone/xfCancel, xfResample, xfNudge/xfStepSize/xfStepRotate/xfFlip, xfFieldChanged, handles (xfPointerDown/Move), layerTransform history, #xfScreen, buildTransformOpenRow.',
                  ['test_transform_basics', 'test_transform_selection_and_kinds', 'test_transform_live_preview']),
    'eyedrop': ('Eyedropper (Colours drawer #coloursEyedropBtn, startEyedropFromColours, #currentColourChip) and sample size: EYEDROP_SAMPLE_SIZES, setEyedropSampleSize, renderEyedropSampleRow, averageCanvasColour, #eyedropControls, doToolAt eyedrop, cursor square.',
                ['test_eyedrop_sample_size', 'test_eyedrop_faded_reference', 'test_eyedrop_from_colours']),
    'space-pan': ('Hold Space to pan: spacePanHeld, setSpacePanHeld, keyTargetIsTextField, setupKeyboardShortcuts keydown/keyup, onStart viaSpace manualPan, window mousemove forwarding manualPan.',
                  ['test_space_pan', 'test_wheel_zoom_anchor', 'test_mouse_cursor_visibility']),
    'reference': ('Reference layers: ReferenceLayer (drawSource, isPixelated, layoutCSS, setActualSize, drawInto, sampleAt), sampling modes, buildReferenceTransformUI, eyedropper (doToolAt eyedrop), flattenTreeToCanvas includeRefs, generateThumbnailDataURL, reference save/load. Mapart colours on references: see the mapart group.',
                  ['test_reference_layer']),
    'pinch': ('Two-finger camera gesture: startTwoFingerGesture (ends an in-progress stroke as an undo step), updateCanvasPanZoomRotate, rebaseLivePinchScale (live zoom rebase so the transformed container never stays huge), reanchorCameraPanAfterZoomSnap.',
              ['test_pinch_after_stroke_is_undoable', 'test_pinch_rebases_live']),
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
    'mapart': ('Mapart profile: MAPART_DATA, mapartSnapColor/mapartSnapRGB/mapartLab, syncMapartPalette, toggleMapartStaircase, resolveMapartStaircaseOff, mapartConvertToFlat (pixelsMulti history), mapart import snapping, New Canvas size in maps, mapart save/load, reference layer MAPART COLOURS (ReferenceLayer.mapartMatched, MAPART_REF_SCALINGS, lanczosResizeImage, refreshMapartReferenceLayers, #refMapartMatchBtn, #refMapartScalingRow).',
               ['test_mapart_new_canvas_in_maps', 'test_resize_sheet_no_autoselect_outside_mapart', 'test_mapart_resize_sheet_in_maps', 'test_mapart_palette_locked', 'test_mapart_snap_matches_mapartcraft',
                'test_mapart_staircase_toggle', 'test_mapart_staircase_off_convert_undo', 'test_mapart_save_load_and_leave',
                'test_mapart_import_snaps', 'test_mapart_resize_whole_maps', 'test_mapart_grid_lines', 'test_mapart_colour_methods', 'test_mapart_reference_match', 'test_mapart_pencil_after_empty_pick']),
    'background': ('Background fill (roadmap 9): backgroundColor, setBackgroundColor, updateBackgroundFill/UI, background pick mode (Colours + Layers), flattenTreeToCanvas bg argument, saveImage, save/load, mapart default and snapping.',
                   ['test_background_fill', 'test_background_mapart']),
    'cloud': ('Cloud Sync and share links (V2_8): opt-in per project (#ctx-cloud, cloudLinkProject/cloudUnlinkProject, relink choice sheet cloudResolveChoice), pixel-app/ folder, cloud, cloudState, cloudSync/cloudSyncOnce, cloudConnect, cloudMarkDirty/cloudMarkDeleted (hooked into persistProject/deleteProjectRecord), #galleryCloudBar, #cloud-modal sheets, openShareSheet, shareCompress, checkIncomingShare, saveDataLooksValid, #ctx-share.',
              ['test_cloud_sync_two_devices', 'test_cloud_share_links']),
    'gallery': ('Hub/gallery and saving: projectStore, IndexedDB, goToMainMenu, saveCurrentStateToStore, openProjectFromStore, gallery long-press menu (#gallery-ctx-menu).',
                ['test_resize_from_gallery', 'test_gallery_thumbnail_privacy']),
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

async def touch_session(pg):
    cdp = await pg.context.new_cdp_session(pg)
    await cdp.send('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
    async def t(kind, pts):
        await cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})
    return t

async def test_pinch_after_stroke_is_undoable(pg):
    await pg.evaluate("() => { handleToolBtn('pencil'); selectedColor = '#112233'; }")
    t = await touch_session(pg)
    x0, y0 = await grid_point(pg, 2, 10)
    u0 = await pg.evaluate("() => undoStack.length")
    await t('touchStart', [(x0, y0)]); await pg.wait_for_timeout(100)
    for k in range(1, 8):
        await t('touchMove', [(x0 + k * 25, y0)]); await pg.wait_for_timeout(16)
    await t('touchStart', [(x0 + 175, y0), (x0 + 100, y0 + 150)]); await pg.wait_for_timeout(30)
    for k in range(1, 4):
        await t('touchMove', [(x0 + 175 - k * 10, y0), (x0 + 100 + k * 10, y0 + 150)]); await pg.wait_for_timeout(16)
    await t('touchEnd', []); await pg.wait_for_timeout(200)
    check('pinch: stroke ended by a second finger is one undo step', await pg.evaluate("() => undoStack.length") == u0 + 1)
    check('pinch: the stroke pixels are there', await px(pg, 2, 10) == '#112233')
    await pg.evaluate("() => undo()")
    check('pinch: undo removes the stroke', await px(pg, 2, 10) is None)

async def test_pinch_rebases_live(pg):
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(12); scale = 12; resetCameraPanZoom(); layoutAll(); }")
    t = await touch_session(pg)
    await t('touchStart', [(300, 200), (700, 600)])
    seen = []
    for k in range(1, 8):
        await t('touchMove', [(300 + k * 25, 200 + k * 25), (700 - k * 25, 600 - k * 25)]); await pg.wait_for_timeout(16)
        seen.append(await pg.evaluate("() => [scale, cameraScale]"))
    check('pinch: zooming out lowers the real scale mid-gesture', seen[-1][0] < 12, seen)
    check('pinch: camera scale stays near 1 while pinching', all(0.6 <= c <= 1.6 for _, c in seen), seen)
    await t('touchEnd', []); await pg.wait_for_timeout(200)
    check('pinch: release snaps to a zoom step with camera scale 1', await pg.evaluate("() => ZOOM_STEPS.includes(scale) && cameraScale === 1"))

async def test_boot_and_canvas(pg):
    check('boot: 32x32 pixel canvas created', await pg.evaluate("() => gridW === 32 && gridH === 32 && activeLayer().type === 'pixel'"))

async def test_pencil_and_undo(pg):
    await pg.evaluate("() => { handleToolBtn('pencil'); selectedColor = '#112233'; }")
    await tap(pg, 5, 5)
    check('pencil: tap draws a pixel', await px(pg, 5, 5) == '#112233', await px(pg, 5, 5))
    await pg.evaluate("() => undo()")
    check('pencil: undo removes it', await px(pg, 5, 5) is None)

class FakeGitHub:
    """In-memory stand-in for the parts of api.github.com Cloud Sync and share links use."""
    def __init__(self):
        import hashlib
        self.h = lambda b: hashlib.sha1(b).hexdigest()
        self.blobs, self.trees, self.commits, self.gists = {}, {}, {}, {}
        self.head = None
        self.calls = 0
    def tree_of_head(self):
        return dict(self.trees[self.commits[self.head]]) if self.head else {}
    def remote_projects(self):
        import re as _re
        return sorted({_re.match(r'pixel-app/projects/(\d+)/', p).group(1) for p in self.tree_of_head() if p.startswith('pixel-app/projects/')})
    def deleted_ids(self):
        import json as _j
        t = self.tree_of_head()
        return _j.loads(self.blobs[t['pixel-app/deleted.json']])['ids'] if 'pixel-app/deleted.json' in t else []
    def project_data(self, pid):
        import json as _j
        return _j.loads(self.blobs[self.tree_of_head()['pixel-app/projects/%s/project.json' % pid]])
    async def handle(self, route):
        import json as _j, base64 as _b, re as _re
        req = route.request
        url = req.url.split('api.github.com', 1)[1]
        path, _, _q = url.partition('?')
        m, body = req.method, (_j.loads(req.post_data) if req.post_data else None)
        self.calls += 1
        def ok(o, status=200): return route.fulfill(status=status, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=_j.dumps(o))
        def err(status, msg): return route.fulfill(status=status, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=_j.dumps({'message': msg}))
        if m == 'OPTIONS': return await route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': '*', 'Access-Control-Allow-Methods': '*'})
        if path.startswith('/gists'):
            if m == 'POST':
                gid = self.h(_j.dumps(body).encode())[:20]
                self.gists[gid] = body
                return await ok({'id': gid}, 201)
            g = self.gists.get(path.split('/')[2])
            if not g: return await err(404, 'Not Found')
            return await ok({'owner': {'login': 'tester'}, 'files': {n: {'filename': n, 'content': f['content'], 'truncated': False} for n, f in g['files'].items()}})
        if req.headers.get('authorization') != 'Bearer good-token': return await err(401, 'Bad credentials')
        if path == '/user': return await ok({'login': 'tester'})
        if path == '/repos/tester/saves': return await ok({'default_branch': 'main', 'private': True})
        if not path.startswith('/repos/tester/saves/'): return await err(404, 'Not Found')
        rest = path[len('/repos/tester/saves/'):]
        if rest == 'git/ref/heads/main':
            return await (ok({'object': {'sha': self.head}}) if self.head else err(409, 'Git Repository is empty.'))
        if rest == 'contents/pixel-app/README.md' and m == 'PUT':
            data = _b.b64decode(body['content']); bs = self.h(data); self.blobs[bs] = data.decode()
            ts = self.h(b'tree' + bs.encode()); self.trees[ts] = {'pixel-app/README.md': bs}
            cs = self.h(b'c0'); self.commits[cs] = ts; self.head = cs
            return await ok({'content': {}}, 201)
        if rest.startswith('git/commits/'): return await ok({'sha': rest[12:], 'tree': {'sha': self.commits[rest[12:]]}})
        if rest.startswith('git/trees/') and m == 'GET':
            return await ok({'tree': [{'path': p, 'type': 'blob', 'sha': s} for p, s in self.trees[rest[10:]].items()], 'truncated': False})
        if rest == 'git/blobs' and m == 'POST':
            bs = self.h(body['content'].encode()); self.blobs[bs] = body['content']
            return await ok({'sha': bs}, 201)
        if rest.startswith('git/blobs/'):
            return await ok({'encoding': 'base64', 'content': _b.b64encode(self.blobs[rest[10:]].encode()).decode()})
        if rest == 'git/trees' and m == 'POST':
            t = dict(self.trees[body['base_tree']])
            for e in body['tree']:
                if e['sha'] is None: t.pop(e['path'], None)
                else: t[e['path']] = e['sha']
            ts = self.h(_j.dumps(sorted(t.items())).encode()); self.trees[ts] = t
            return await ok({'sha': ts}, 201)
        if rest == 'git/commits' and m == 'POST':
            cs = self.h((body['tree'] + body['parents'][0] + str(len(self.commits))).encode())
            self.commits[cs] = body['tree']; self.parent = getattr(self, 'parent', {}); self.parent[cs] = body['parents'][0]
            return await ok({'sha': cs}, 201)
        if rest == 'git/refs/heads/main' and m == 'PATCH':
            if self.parent.get(body['sha']) != self.head: return await err(422, 'Update is not a fast forward')
            self.head = body['sha']
            return await ok({'object': {'sha': self.head}})
        return await err(404, 'Not Found ' + rest)

async def cloud_connect_ui(pg, token='good-token', open_sheet=True):
    if open_sheet: await pg.locator('#galleryCloudBar .cloud-bar-btn').click(); await pg.wait_for_timeout(200)
    await pg.locator('#cloud-box input[type=password]').fill(token)
    await pg.locator('#cloud-box input[type=text]').fill('saves')
    await pg.locator('#cloud-box button', has_text='CONNECT').click()

async def cloud_wait_idle(pg, timeout=8000):
    await pg.wait_for_function("() => typeof cloud !== 'undefined' && !cloud.running && !cloud.timer && (cloud.status === 'idle' || cloud.status === 'error') && !cloudPendingCount()", timeout=timeout)
    await pg.wait_for_timeout(150)

async def cloud_sync(pg):
    await pg.evaluate("() => cloudSync()")
    await cloud_wait_idle(pg)

async def ctx_cloud(pg, pid):
    await pg.evaluate("() => closeCloudSheet()")
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-cloud').click(); await pg.wait_for_timeout(150)

async def second_device(pg, gh):
    ctx = await pg.context.browser.new_context(viewport={'width': 1000, 'height': 800})
    await ctx.route('https://api.github.com/**', gh.handle)
    p2 = await ctx.new_page()
    errs = []
    p2.on('pageerror', lambda e: errs.append(str(e)))
    await p2.goto(BASE_URL + 'Pixel_Art_App.html'); await p2.wait_for_timeout(1000)
    return ctx, p2, errs

STORED_PIXEL = """async ([id, x, y]) => { const d = await getProjectDataP(id); const img = new Image(); img.src = d.frames[0].layers[0].dataURL; await img.decode(); const c = document.createElement('canvas'); c.width = d.gridW; c.height = d.gridH; const g = c.getContext('2d'); g.drawImage(img, 0, 0); return Array.from(g.getImageData(x, y, 1, 1).data).slice(0, 3).join(','); }"""

async def test_cloud_sync_two_devices(pg):
    gh = FakeGitHub()
    await pg.context.route('https://api.github.com/**', gh.handle)
    await pg.evaluate(DRAW, [[[1, 1]], '#FF0000'])
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(500)
    check('cloud: gallery shows the Sync with GitHub bar', 'Sync with GitHub' in await pg.locator('#galleryCloudBar').inner_text())
    small = await pg.evaluate("() => document.querySelector('#galleryCloudBar .cloud-bar-btn').getBoundingClientRect().height")
    check('cloud: bar is a 44px+ touch target', small >= 44, small)
    await pg.locator('#galleryCloudBar .cloud-bar-btn').click(); await pg.wait_for_timeout(200)
    await pg.locator('#cloud-box input[type=password]').fill('wrong'); await pg.locator('#cloud-box input[type=text]').fill('saves')
    await pg.locator('#cloud-box button', has_text='CONNECT').click(); await pg.wait_for_timeout(400)
    check('cloud: a bad token shows an in-page error and stays disconnected', 'rejected the token' in await pg.locator('#cloud-box .cloud-err').inner_text() and not await pg.evaluate("() => cloudConnected()"))
    check('cloud: token and repo inputs are 16px (no iOS zoom)', await pg.evaluate("() => [...document.querySelectorAll('#cloud-box input')].every(i => getComputedStyle(i).fontSize === '16px')"))
    await pg.evaluate("() => closeCloudSheet()")
    pid = await pg.evaluate("() => projectStore[0].id")
    await cloud_connect_ui(pg); await cloud_wait_idle(pg)
    check('cloud: connecting does not upload anything by itself', gh.remote_projects() == [] and await pg.evaluate("() => cloudLinkedCount() === 0"), gh.remote_projects())
    check('cloud: repo setup file goes in the pixel-app folder, not the root', list(gh.tree_of_head()) == ['pixel-app/README.md'], list(gh.tree_of_head()))
    await pg.evaluate("() => { cloudDisconnect(); closeCloudSheet(); }")
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    check('cloud: long-press offers Save to Cloud', 'Save to Cloud' in await pg.locator('#ctx-cloud').inner_text())
    await pg.locator('#ctx-cloud').click(); await pg.wait_for_timeout(200)
    check('cloud: Save to Cloud while disconnected opens the connect sheet', await pg.evaluate("() => cloudSheetMode === 'settings' && !!document.querySelector('#cloud-box input[type=password]')"))
    await cloud_connect_ui(pg, open_sheet=False); await cloud_wait_idle(pg)
    check('cloud: after connecting, that project is saved to the cloud', gh.remote_projects() == [str(pid)], gh.remote_projects())
    check('cloud: files live under pixel-app/', all(p.startswith('pixel-app/') for p in gh.tree_of_head()), list(gh.tree_of_head()))
    check('cloud: card shows a cloud badge', await pg.locator('.gallery-card[data-id="%s"] .card-cloud' % pid).count() == 1)
    check('cloud: token is stored only in this browser (localStorage)', await pg.evaluate("() => localStorage.getItem('pixelAppCloudToken') === 'good-token' && cloud.repo === 'tester/saves'"))
    await pg.evaluate("() => closeCloudSheet()")
    await pg.evaluate("() => { const n = projectStore.length; saveCurrentStateToStore(null, 'Local only'); }"); await pg.wait_for_timeout(200)
    await cloud_sync(pg)
    check('cloud: projects not saved to the cloud stay local', gh.remote_projects() == [str(pid)] and await pg.evaluate("() => projectStore.length === 2"), gh.remote_projects())
    local_only = await pg.evaluate("() => projectStore.find(p => p.name === 'Local only').id")
    await pg.evaluate("(id) => { const i = projectStore.findIndex(p => p.id === id); projectStore.splice(i, 1); deleteProjectRecord(id); renderGallery(); }", local_only)
    ctx2, p2, errs2 = await second_device(pg, gh)
    try:
        await cloud_connect_ui(p2); await cloud_wait_idle(p2)
        check('cloud: second device gets the project', await p2.evaluate("(id) => projectStore.some(p => p.id === id)", pid))
        check('cloud: second device has the same pixels', await p2.evaluate(STORED_PIXEL, [pid, 1, 1]) == '255,0,0')
        check('cloud: synced card shows in the gallery', await p2.locator('.gallery-card[data-id="%s"]' % pid).count() == 1)
        await p2.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", pid); await p2.wait_for_timeout(400)
        await p2.evaluate(DRAW, [[[2, 2]], '#0000FF'])
        await p2.evaluate("() => goToMainMenu()"); await p2.wait_for_timeout(300)
        await cloud_wait_idle(p2)
        check('cloud: saving on device 2 uploads the edit', '0,0,255' == await p2.evaluate(STORED_PIXEL, [pid, 2, 2]) and gh.project_data(pid)['frames'] is not None)
        await cloud_sync(pg)
        check('cloud: device 1 picks up the edit', await pg.evaluate(STORED_PIXEL, [pid, 2, 2]) == '0,0,255')
        await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'From A'; persistProject(p, null); }", pid)
        await p2.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'From B'; persistProject(p, null); }", pid)
        await cloud_sync(pg); await cloud_sync(p2)
        names2 = await p2.evaluate("() => projectStore.map(p => p.name).sort()")
        check('cloud: edited on both devices keeps both versions', names2 == ['From A (other device)', 'From B'], names2)
        await cloud_sync(pg)
        names1 = await pg.evaluate("() => projectStore.map(p => p.name).sort()")
        check('cloud: both devices end up with the same projects', names1 == names2, names1)
        copy_id = await pg.evaluate("() => projectStore.find(p => p.name.endsWith('(other device)')).id")
        await pg.evaluate("() => closeCloudSheet()")
        await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", copy_id)
        await pg.locator('#ctx-delete').click(); await pg.wait_for_timeout(200)
        await cloud_wait_idle(pg)
        check('cloud: deleting uploads the delete', str(copy_id) not in gh.remote_projects() and str(copy_id) in gh.deleted_ids(), gh.remote_projects())
        await cloud_sync(p2)
        check('cloud: the delete reaches the other device', not await p2.evaluate("(id) => projectStore.some(p => p.id === id)", copy_id))
        await p2.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", pid); await p2.wait_for_timeout(300)
        await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'Renamed on A'; persistProject(p, null); }", pid)
        await cloud_wait_idle(pg)
        await p2.evaluate("() => cloudSync()"); await cloud_wait_idle(p2)
        check('cloud: the project open in the editor is not replaced mid-drawing', await p2.evaluate("(id) => projectStore.find(p => p.id === id).name === 'From B' && currentProjectId === id", pid))
        await p2.evaluate("() => goToMainMenu()"); await p2.wait_for_timeout(300); await cloud_wait_idle(p2)
        check('cloud: drawing session ends without losing either side', len(gh.remote_projects()) == 2, gh.remote_projects())
        await cloud_wait_idle(p2)
        await cloud_sync(pg)
        other = await pg.evaluate("() => projectStore.find(p => p.name.endsWith('(other device)')).id")
        await ctx_cloud(pg, other); await cloud_wait_idle(pg)
        check('cloud: unlink takes it out of the cloud', str(other) not in gh.remote_projects() and str(other) not in gh.deleted_ids(), gh.remote_projects())
        check('cloud: unlinked project stays on this device without the badge', await pg.evaluate("(id) => projectStore.some(p => p.id === id) && !cloudIsLinked(id)", other) and await pg.locator('.gallery-card[data-id="%s"] .card-cloud' % other).count() == 0)
        await cloud_sync(p2)
        check('cloud: other device keeps its copy, no longer synced', await p2.evaluate("(id) => projectStore.some(p => p.id === id) && !cloudIsLinked(id)", other))
        await p2.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'Edited after unlink'; persistProject(p, null); }", other)
        await cloud_sync(p2)
        check('cloud: edits to an unlinked project are not uploaded', str(other) not in gh.remote_projects())
        NAME = "(id) => (projectStore.find(p => p.id === id) || {}).name"
        pg_name = await pg.evaluate(NAME, other)
        await ctx_cloud(p2, other); await cloud_wait_idle(p2)
        check('relink: linking again uploads it when the cloud has no copy', str(other) in gh.remote_projects() and await p2.evaluate("() => cloudSheetMode !== 'choice'"))
        await cloud_sync(pg)
        check('relink: another device with an unlinked copy leaves it alone', await pg.evaluate(NAME, other) == pg_name and not await pg.evaluate("(id) => cloudIsLinked(id)", other))
        await ctx_cloud(pg, other); await cloud_wait_idle(pg); await pg.wait_for_timeout(300)
        check('relink: different cloud version asks which to keep', await pg.evaluate("() => cloudSheetMode === 'choice' && document.querySelectorAll('#cloud-box .cloud-choice-side img').length === 2"))
        check('relink: nothing was overwritten while asking', await pg.evaluate(NAME, other) == pg_name and str(other) in gh.remote_projects())
        small = await pg.evaluate("() => [...document.querySelectorAll('#cloud-box .cloud-btn')].filter(b => b.getBoundingClientRect().height < 44).length")
        check('relink: choice buttons are 44px+', small == 0, small)
        await pg.locator('#cloud-box button', has_text='DECIDE LATER').click(); await pg.wait_for_timeout(200)
        check('later: sheet closes and the project waits, still linked', await pg.evaluate("(id) => cloudSheetMode === null && cloudIsLinked(id) && cloudState.ask[id] === 'later'", other))
        check('later: card is marked as waiting', '\u26a0' in await pg.locator('.gallery-card[data-id="%s"] .card-cloud' % other).inner_text())
        check('later: gallery bar says a choice is waiting', 'waiting for your choice' in await pg.locator('#galleryCloudBar').inner_text())
        cloud_before = gh.tree_of_head()['pixel-app/projects/%s/project.json' % other]
        await pg.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", other); await pg.wait_for_timeout(300)
        await pg.evaluate(DRAW, [[[9, 9]], '#00FFFF'])
        await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(400)
        await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'Edited while deciding'; persistProject(p, null); }", other)
        await cloud_wait_idle(pg); await cloud_sync(pg)
        check('later: editing the local copy uploads nothing and does not nag', gh.tree_of_head()['pixel-app/projects/%s/project.json' % other] == cloud_before and await pg.evaluate("() => cloudSheetMode === null"))
        check('later: the local edits are kept', await pg.evaluate(STORED_PIXEL, [other, 9, 9]) == '0,255,255')
        await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", other)
        check('later: long-press offers Choose Cloud Version', 'Choose Cloud Version' in await pg.locator('#ctx-cloud').inner_text())
        await pg.locator('#ctx-cloud').click(); await cloud_wait_idle(pg); await pg.wait_for_timeout(300)
        check('later: choosing reopens the sheet with the edited local copy', await pg.evaluate("() => cloudSheetMode === 'choice'") and 'Edited while deciding' in await pg.locator('#cloud-box').inner_text())
        await pg.locator('#cloud-box button', has_text="USE THE CLOUD").click(); await pg.wait_for_timeout(200); await cloud_wait_idle(pg)
        check("relink: Use the cloud's replaces this device's copy", await pg.evaluate(NAME, other) == 'Edited after unlink' and await pg.evaluate("(id) => cloudIsLinked(id)", other))
        await ctx_cloud(p2, other); await cloud_wait_idle(p2)
        await p2.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'P2 version'; persistProject(p, null); }", other)
        await cloud_sync(pg)
        check('relink: unlinking elsewhere unlinks here but keeps the project', not await pg.evaluate("(id) => cloudIsLinked(id)", other) and await pg.evaluate(NAME, other) == 'Edited after unlink')
        await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'PG version'; persistProject(p, null); }", other)
        await ctx_cloud(pg, other); await cloud_wait_idle(pg)
        await ctx_cloud(p2, other); await cloud_wait_idle(p2); await p2.wait_for_timeout(300)
        check('relink: the other device gets asked too', await p2.evaluate("() => cloudSheetMode === 'choice'"))
        await p2.locator('#cloud-box button', has_text='KEEP BOTH').click(); await p2.wait_for_timeout(200); await cloud_wait_idle(p2)
        names = await p2.evaluate("() => projectStore.map(p => p.name).sort()")
        check('relink: Keep both keeps this one and brings the cloud one in as a copy', 'P2 version' in names and 'PG version (other device)' in names, names)
        check('relink: both versions end up in the cloud', await p2.evaluate("() => projectStore.filter(p => cloudIsLinked(p.id)).length") == len(gh.remote_projects()), gh.remote_projects())
        before = await p2.evaluate("() => projectStore.length")
        await p2.evaluate("() => openCloudSheet('settings')")
        off = p2.locator('#cloud-box .cloud-btn.danger')
        await off.click(); await p2.wait_for_timeout(100)
        check('cloud: disconnect needs a second tap', await p2.evaluate("() => cloudConnected()"))
        await off.click(); await p2.wait_for_timeout(100)
        check('cloud: disconnect forgets the token but keeps projects', await p2.evaluate("() => !cloudConnected() && !localStorage.getItem('pixelAppCloudToken') && projectStore.length === " + str(before) + ""))
        check('cloud: device 2 had no page errors', not errs2, errs2[:3])
    finally:
        await ctx2.close()

async def test_cloud_share_links(pg):
    gh = FakeGitHub()
    await pg.context.route('https://api.github.com/**', gh.handle)
    await pg.evaluate(DRAW, [[[3, 4]], '#00FF00'])
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(500)
    pid = await pg.evaluate("() => projectStore[0].id")
    await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); p.name = 'Green dot'; persistProject(p, null); }", pid)
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-share').click()
    await pg.wait_for_function("() => cloudSheetArg && cloudSheetArg.inlineLink")
    check('share: gist button is off until Cloud Sync is connected', await pg.locator('#cloud-box button', has_text='GITHUB GIST').is_disabled())
    await pg.locator('#cloud-box button', has_text='DRAWING INSIDE').click(); await pg.wait_for_timeout(100)
    link = await pg.evaluate("() => cloudSheetArg.link")
    check('share: inline link holds the drawing', '#p=' in link)
    check('share: small drawing fits in a Discord message', len(link) <= 2000 and 'Fits in a Discord' in await pg.locator('#cloud-box').inner_text(), len(link))
    await pg.evaluate("() => closeCloudSheet()")
    ctx2, p2, errs2 = await second_device(pg, gh)
    try:
        await p2.goto(link); await p2.wait_for_timeout(1200)
        check('share: opening the link shows the shared project', 'Green dot' in await p2.locator('#cloud-box').inner_text())
        check('share: preview thumbnail is drawn', await p2.locator('#cloud-box .cloud-incoming-thumb img').count() == 1)
        await p2.locator('#cloud-box button', has_text='OPEN MY COPY').click(); await p2.wait_for_timeout(800)
        check('share: recipient gets their own copy with the pixels', await px(p2, 3, 4) == '#00FF00' and await p2.evaluate("() => currentProjectId === null && currentProjectName === 'Green dot' && !location.hash"))
        await p2.evaluate("() => goToMainMenu()"); await p2.wait_for_timeout(500)
        check('share: the copy joins the recipient gallery', await p2.evaluate("() => projectStore.length === 1 && projectStore[0].name === 'Green dot'"))
        await p2.goto(BASE_URL + 'Pixel_Art_App.html#p=AAAA'); await p2.wait_for_timeout(900)
        check('share: a broken or cut-off link shows an in-page message', 'cut off' in (await p2.locator('#cloud-box .cloud-err').inner_text()))
        bad = '#p=' + await p2.evaluate("async () => shareCompress(JSON.stringify({version: 7, gridW: 2, gridH: 2, frames: [{layers: [{type: 'pixel', dataURL: 'https://example.com/x.png'}]}]}))")
        await p2.goto(BASE_URL + 'Pixel_Art_App.html' + bad); await p2.wait_for_timeout(900)
        check('share: links whose images point at other websites are refused', await p2.locator('#cloud-box .cloud-err').count() == 1 and await p2.locator('#cloud-box button', has_text='OPEN MY COPY').count() == 0)
        await cloud_connect_ui(pg); await cloud_wait_idle(pg)
        await pg.evaluate("(id) => openShareSheet(id)", pid)
        await pg.wait_for_function("() => cloudSheetArg && cloudSheetArg.data")
        await pg.locator('#cloud-box button', has_text='GITHUB GIST').click()
        await pg.wait_for_function("() => cloudSheetArg.linkKind === 'gist'")
        glink = await pg.evaluate("() => cloudSheetArg.link")
        check('share: gist link is short', '#gist=' in glink and len(glink) < 200, glink)
        await p2.goto('about:blank'); await p2.goto(glink); await p2.wait_for_timeout(1200)
        txt = await p2.locator('#cloud-box').inner_text()
        check('share: gist link opens without a token and names the sharer', 'Green dot' in txt and 'shared by tester' in txt)
        check('share: recipient had no page errors', not errs2, errs2[:3])
    finally:
        await ctx2.close()

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

async def test_layers_duplicate_reachable(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }"); await pg.wait_for_timeout(300)
    await pg.locator('#layerDuplicateBtn').click(); await pg.wait_for_timeout(200)
    check('dup: layer settings DUPLICATE copies the active layer and selects the copy', await pg.evaluate("() => layers.length === 2 && activeLayer().name === 'Layer 1 copy'"))
    await pg.evaluate("() => undo()")
    check('dup: one undo removes the copy', await pg.evaluate("() => layers.length === 1"))
    await pg.locator('#layerSelectBtn').click(); await pg.wait_for_timeout(300)
    hit = await pg.evaluate("""() => { const b = [...document.querySelectorAll('#layerSelectionActions button')].find(b => b.textContent.includes('DUPLICATE')); const r = b.getBoundingClientRect();
        const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return el === b || b.contains(el); }""")
    check('dup: Select mode DUPLICATE is on screen and not covered', hit)
    check('dup: add-layer buttons hidden while selecting', await pg.evaluate("() => getComputedStyle(document.querySelector('.layers-icon-grid')).display === 'none'"))

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
    check('split: collapses to a 20px strip after tapping elsewhere', hb and abs(hb['height'] - 20) < 1.5, hb)
    await pg.mouse.move(hb['x'] + hb['width'] / 2, hb['y'] + 6); await pg.mouse.down(); await pg.mouse.up(); await pg.wait_for_timeout(400)
    hb2 = await h.bounding_box()
    check('split: tapping the strip opens it to 44px', hb2 and abs(hb2['height'] - 44) < 1.5, hb2)
    await pg.evaluate("() => { closePanel(); openDrawer('debug'); }"); await pg.wait_for_timeout(500)
    check('split: debug drawer divider uses the same collapsing split', await pg.evaluate("() => document.getElementById('debugDrawerSplitHandle').classList.contains('cdsplit')"))
    db = await pg.locator('#debugDrawerSplitHandle').bounding_box()
    check('split: debug divider is 44px or a 20px strip', db and (abs(db['height'] - 20) < 1.5 or abs(db['height'] - 44) < 1.5), db)
    await pg.set_viewport_size({'width': 1000, 'height': 800})

async def test_palette_drag_swaps(pg):
    await pg.evaluate("() => { openPanel('colors'); ['#111111','#222222','#333333','#444444','#555555'].forEach(c => createSwatch(c)); }")
    await pg.wait_for_timeout(200)
    before = await pg.evaluate(SWATCHES)
    i1, i2 = before.index('#111111'), before.index('#444444')
    await pg.evaluate("() => handleManageClick()"); await pg.wait_for_timeout(100)
    check('palette: edit mode shows delete badges', await pg.locator('#palette .swatch-wrapper .delete-badge').first.is_visible())
    w = pg.locator('#palette .swatch-wrapper')
    a = await w.nth(i1).bounding_box(); b = await w.nth(i2).bounding_box()
    await pg.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2); await pg.mouse.down()
    await pg.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, steps=4); await pg.mouse.up(); await pg.wait_for_timeout(100)
    check('palette: a quick swipe (scroll) does not start a drag or swap', await pg.evaluate(SWATCHES) == before and await pg.locator('.swatch-drag-ghost').count() == 0 and await pg.locator('#palette .swatch-wrapper.dragging').count() == 0)
    await pg.mouse.move(a['x'] + a['width'] / 2, a['y'] + a['height'] / 2); await pg.mouse.down(); await pg.wait_for_timeout(320)
    check('palette: holding a swatch still picks it up', await pg.locator('#palette .swatch-wrapper.dragging').count() == 1)
    await pg.mouse.move(b['x'] + b['width'] / 2, b['y'] + b['height'] / 2, steps=8); await pg.wait_for_timeout(50)
    check('palette: target swatch is highlighted', await pg.locator('#palette .swatch-wrapper.swap-target').count() == 1)
    await pg.mouse.up(); await pg.wait_for_timeout(100)
    after = await pg.evaluate(SWATCHES)
    expect = list(before); expect[i1], expect[i2] = expect[i2], expect[i1]
    check('palette: the two colours swap and nothing else moves', after == expect, [before, after])
    check('palette: drag ghost removed', await pg.locator('.swatch-drag-ghost').count() == 0)
    check('palette: a big Done button shows while rearranging', await pg.locator('#paletteDoneBtn').is_visible())
    await pg.evaluate("() => { for (let i = 0; i < 160; i++) createSwatch('#' + (0x100000 + i * 4099).toString(16).slice(-6).toUpperCase()); let el = document.getElementById('palette'); while (el && !(el.scrollHeight > el.clientHeight + 4 && /auto|scroll/.test(getComputedStyle(el).overflowY))) el = el.parentElement; if (el) el.scrollTop = el.scrollHeight; }")
    await pg.wait_for_timeout(150)
    vis = await pg.evaluate("() => { const b = document.getElementById('paletteDoneBtn'), r = b.getBoundingClientRect(), el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return r.top >= 0 && r.bottom <= innerHeight && (el === b || b.contains(el)); }")
    check('palette: Done stays on screen after scrolling down a long palette', vis)
    await pg.locator('#paletteDoneBtn').click(); await pg.wait_for_timeout(100)
    check('palette: Done leaves rearrange mode', await pg.evaluate("() => !isEditing") and not await pg.locator('#paletteDoneBtn').is_visible())

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

THUMB_ALPHA = """(id) => new Promise(res => { const p = projectStore.find(q => q.id === id); const img = new Image();
    img.onload = () => { const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const x = c.getContext('2d'); x.drawImage(img, 0, 0); res(x.getImageData(img.width >> 1, img.height >> 1, 1, 1).data[3]); };
    img.onerror = () => res(-1); img.src = p.thumbnailDataURL; })"""

async def test_gallery_thumbnail_privacy(pg):
    await new_canvas(pg)
    await pg.evaluate(DRAW, [[[x, y] for x in range(32) for y in range(32)], '#FF0000'])
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(600)
    pid = await pg.evaluate("() => projectStore[0].id")
    check('thumb privacy: card thumbnail shows the art', await pg.evaluate(THUMB_ALPHA, pid) == 255)
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-thumb-privacy').click(); await pg.wait_for_timeout(800)
    check('thumb privacy: sheet lists the layers with sliders at 100%', await pg.evaluate("() => document.getElementById('thumb-privacy-modal').classList.contains('open') && document.querySelectorAll('#thumb-privacy-list input[type=range]').length === 1 && document.querySelector('#thumb-privacy-list input').value === '100'"))
    await pg.evaluate("() => { const r = document.querySelector('#thumb-privacy-list input'); r.value = '0'; r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change')); }")
    await pg.locator('#thumb-privacy-done-btn').click(); await pg.wait_for_timeout(600)
    check('thumb privacy: card thumbnail now hides that layer', await pg.evaluate(THUMB_ALPHA, pid) == 0)
    await pg.evaluate("() => { document.getElementById('appToast').textContent = ''; }")
    await pg.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", pid); await pg.wait_for_timeout(600)
    check('thumb privacy: inside the project the layer keeps 100% opacity', await pg.evaluate("() => layers[0].opacity === 1 && layers[0].thumbOpacity === 0"))
    check('thumb privacy: opening it shows the reminder toast', 'Thumbnail opacity is different' in (await pg.locator('#appToast').text_content() or ''))
    await pg.evaluate("() => addPixelLayer()")
    check('thumb privacy: new layers start at 100% in the thumbnail', await pg.evaluate("() => layers[layers.length - 1].thumbOpacity === undefined"))
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(600)
    check('thumb privacy: saving the project keeps the thumbnail setting', await pg.evaluate(THUMB_ALPHA, pid) == 0)
    await pg.evaluate("() => { document.getElementById('appToast').textContent = ''; }")
    await pg.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", pid); await pg.wait_for_timeout(600)
    check('thumb privacy: the toast shows only once per page load', 'Thumbnail opacity' not in (await pg.locator('#appToast').text_content() or ''))
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(600)
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    check('thumb privacy: menu offers Hide Thumbnail', 'Hide Thumbnail' in await pg.locator('#ctx-thumb-hide').text_content())
    await pg.evaluate("() => closeGalleryCtxMenu()")
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: window.innerHeight - 20})", pid)
    check('gallery menu: long-press near the bottom keeps the whole menu on screen', await pg.evaluate("() => { const r = document.getElementById('gallery-ctx-menu').getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight; }"))
    await pg.set_viewport_size({'width': 390, 'height': 300})
    await pg.evaluate("() => closeGalleryCtxMenu()")
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 250})", pid)
    check('gallery menu: on a short screen it fits and scrolls', await pg.evaluate("() => { const m = document.getElementById('gallery-ctx-menu'); const r = m.getBoundingClientRect(); return r.top >= 0 && r.bottom <= window.innerHeight && m.scrollHeight > m.clientHeight && getComputedStyle(m).overflowY === 'auto'; }"))
    await pg.set_viewport_size({'width': 1000, 'height': 800})
    await pg.evaluate("() => closeGalleryCtxMenu()")
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    await pg.locator('#ctx-thumb-hide').click(); await pg.wait_for_timeout(600)
    check('thumb privacy: hidden card is just the name strip (no thumbnail area, rounded card)', await pg.evaluate("(id) => { const c = document.querySelector('.gallery-card[data-id=\"' + id + '\"]'); return c.classList.contains('thumb-hidden-card') && !c.querySelector('.thumb-wrap') && !c.querySelector('img') && !!c.querySelector('.card-name') && getComputedStyle(c).borderTopLeftRadius === '12px'; }", pid))
    check('thumb privacy: the stored image is kept (screen privacy only)', await pg.evaluate("(id) => { const p = projectStore.find(q => q.id === id); return p.thumbHidden === true && p.thumbnailDataURL.length > 100; }", pid))
    await pg.evaluate("(id) => new Promise(r => openProjectFromStore(id, r))", pid); await pg.wait_for_timeout(600)
    await pg.evaluate("() => goToMainMenu()"); await pg.wait_for_timeout(600)
    check('thumb privacy: still hidden after opening and saving', await pg.evaluate("(id) => projectStore.find(q => q.id === id).thumbHidden === true", pid))
    await pg.evaluate("(id) => openGalleryCtxMenu(id, {clientX: 100, clientY: 100})", pid)
    check('thumb privacy: menu now offers Show Thumbnail', 'Show Thumbnail' in await pg.locator('#ctx-thumb-hide').text_content())
    await pg.locator('#ctx-thumb-hide').click(); await pg.wait_for_timeout(600)
    check('thumb privacy: Show brings the image back', await pg.evaluate("(id) => !!document.querySelector('.gallery-card[data-id=\"' + id + '\"] img')", pid))

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
    await pg.evaluate("() => { openPanel('colors'); handleManageClick(); }")
    check('mapart palette: Done button shows in rearrange mode', await pg.locator('#paletteDoneBtn').is_visible())
    await pg.evaluate("() => exitSwatchEditMode()")
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

async def test_mapart_grid_lines(pg):
    await mapart_canvas(pg, 2, 2)
    LINES = "() => [document.querySelectorAll('#gridOverlay .grid-chunk-line').length, document.querySelectorAll('#gridOverlay .grid-map-line').length, getComputedStyle(document.getElementById('gridOverlay')).display]"
    check('grid: button lives in the View panel, off by default', await pg.evaluate("() => !!document.querySelector('#panel-view #gridToggleBtn') && !document.querySelector('#toolsDrawer #gridToggleBtn') && showGridLines === false"))
    await pg.evaluate("() => { toggleGridLines(); zoomIndex = ZOOM_STEPS.indexOf(4); scale = 4; layoutAll(); }")
    # 256 x 256: chunk lines at 16..240 (15 per axis), map line at 128 (1 per axis)
    check('grid: mapart at 4x shows chunk (16px) and map (128px) lines', await pg.evaluate(LINES) == [30, 2, 'block'], await pg.evaluate(LINES))
    check('grid: map line is red at x = 128 * scale', await pg.evaluate("() => { const d = document.querySelector('#gridOverlay .grid-map-line'); return d.style.background.includes('229, 57, 53') && parseFloat(d.style.left) + 1.5 === 512; }"))
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(0.35); scale = 0.35; layoutAll(); }")
    check('grid: at 0.35x chunk and pixel lines hide, map lines stay', await pg.evaluate(LINES) == [0, 2, 'block'] and await pg.evaluate("() => document.getElementById('gridOverlay').style.backgroundImage === 'none'"), await pg.evaluate(LINES))
    data = await pg.evaluate("() => JSON.parse(JSON.stringify(currentProjectSaveData('g')))")
    check('grid: on/off saved with the project', data.get('gridLines') is True)
    await pg.evaluate("() => setGridLines(false)")
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data)
    await pg.wait_for_timeout(300)
    check('grid: reopening the project turns it back on', await pg.evaluate("() => showGridLines === true && document.getElementById('gridToggleBtn').innerText.includes('ON')") and (await pg.evaluate(LINES))[1] == 2)
    await new_canvas(pg)
    check('grid: a new project starts with the grid off', await pg.evaluate("() => showGridLines === false") and (await pg.evaluate(LINES))[2] == 'none')
    await pg.evaluate("() => { toggleGridLines(); zoomIndex = ZOOM_STEPS.indexOf(8); scale = 8; layoutAll(); }")
    check('grid: outside mapart only pixel lines, no chunk/map lines', (await pg.evaluate(LINES))[:2] == [0, 0] and await pg.evaluate("() => document.getElementById('gridOverlay').style.backgroundImage !== 'none'"))

SWATCH_CLICK = "(hex) => { const el = [...document.querySelectorAll('#palette .swatch-wrapper:not(#transparencyWrapper):not(#pickerContainer) .swatch')].find(e => rgbToHex(e.style.backgroundColor).toUpperCase() === hex); el.click(); return !!el; }"
BG_PX = "([x, y, bg]) => { const c = flattenLayersToCanvas(frames[activeFrameIndex].layerTree, bg ? backgroundColor : undefined); const d = c.getContext('2d').getImageData(x, y, 1, 1).data; return d[3] ? rgbToHexBytes(d[0], d[1], d[2]) : null; }"

async def test_background_fill(pg):
    await new_canvas(pg)
    check('bg: new Pixel Art project has no background', await pg.evaluate("() => backgroundColor === null && document.getElementById('bgSwatchColours').classList.contains('bg-none')"))
    pal = await pg.evaluate(SWATCHES)
    target, drawing = pal[1], pal[0]
    await pg.evaluate("(c) => handleSwatchClick(c)", drawing)
    await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }"); await pg.wait_for_timeout(300)
    await pg.locator('#layersBgBtn').click(); await pg.wait_for_timeout(150)
    check('bg: Layers Background button opens Colours in pick mode', await pg.evaluate("() => openPanelName === 'colors' && backgroundPickMode && document.getElementById('bgPickHint').style.display === ''"))
    await pg.evaluate(SWATCH_CLICK, target); await pg.wait_for_timeout(150)
    check('bg: tapping a swatch sets the background, drawing colour unchanged', await pg.evaluate("([t, d]) => backgroundColor === t && selectedColor === d && !backgroundPickMode", [target, drawing]))
    check('bg: goes back to the Layers drawer, both swatches show it', await pg.evaluate("(t) => openPanelName === 'layers' && rgbToHex(document.getElementById('layersBgSwatch').style.backgroundColor).toUpperCase() === t && rgbToHex(document.getElementById('bgSwatchColours').style.backgroundColor).toUpperCase() === t", target))
    check('bg: live fill sits under every layer', await pg.evaluate("() => { const el = document.getElementById('backgroundFill'); return container.firstChild === el && el.style.display === 'block' && parseFloat(el.style.width) === gridW * scale; }"))
    await pg.evaluate(DRAW, [[[1, 1]], '#FF0000'])
    check('bg: export flatten fills empty pixels, keeps drawn ones', await pg.evaluate(BG_PX, [0, 0, True]) == target and await pg.evaluate(BG_PX, [1, 1, True]) == '#FF0000')
    check('bg: tool flatten (bucket/eyedropper) still sees empty pixels', await pg.evaluate(BG_PX, [0, 0, False]) is None)
    data = await pg.evaluate("() => JSON.parse(JSON.stringify(currentProjectSaveData('b')))")
    check('bg: saved in the project', data.get('backgroundColor') == target)
    await pg.evaluate("() => undo()")
    check('bg: undo removes the background', await pg.evaluate("() => backgroundColor === null && document.getElementById('backgroundFill').style.display === 'none'"))
    await pg.evaluate("() => redo()")
    check('bg: redo brings it back', await pg.evaluate("(t) => backgroundColor === t", target))
    await pg.evaluate("() => { openPanel('colors'); }"); await pg.locator('#bgNoneBtn').click()
    check('bg: NONE clears it', await pg.evaluate("() => backgroundColor === null"))
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data); await pg.wait_for_timeout(300)
    check('bg: reopening the project restores it', await pg.evaluate("(t) => backgroundColor === t && document.getElementById('backgroundFill').style.display === 'block'", target))
    await pg.locator('#bgPickBtn').click()
    await pg.evaluate("() => closePanel()")
    check('bg: closing the panel cancels pick mode', await pg.evaluate("() => !backgroundPickMode && !document.getElementById('palette').classList.contains('bg-picking')"))

async def test_background_mapart(pg):
    await mapart_canvas(pg)
    check('bg mapart: new mapart starts on white carpet, NONE hidden', await pg.evaluate("() => backgroundColor === '#DCDCDC' && document.getElementById('bgNoneBtn').style.display === 'none'"))
    await pg.evaluate("() => { openPanel('colors'); toggleBackgroundPickMode(); }")
    await pg.locator('#transparencyBtn').click()
    check('bg mapart: transparent swatch in pick mode cancels, never none', await pg.evaluate("() => backgroundColor === '#DCDCDC' && !backgroundPickMode"))
    check('bg mapart: setting a non-map colour snaps it', await pg.evaluate("() => { setBackgroundColor('#FF0001', true); return backgroundColor === '#DC0000'; }"))
    await pg.evaluate("() => toggleMapartStaircase()")
    await pg.evaluate("() => { toggleBackgroundPickMode(); }")
    await pg.evaluate(SWATCH_CLICK, '#FFFFFF')
    check('bg mapart: staircase on allows a light shade', await pg.evaluate("() => backgroundColor === '#FFFFFF'"))
    await pg.evaluate("() => toggleMapartStaircase()")
    check('bg mapart: staircase off moves it to the normal shade', await pg.evaluate("() => mapartStaircase === false && backgroundColor === '#DCDCDC'"))
    await pg.evaluate(DRAW, [[[3, 3]], '#DC0000'])
    check('bg mapart: PNG flatten has no transparent pixels', await pg.evaluate(BG_PX, [0, 0, True]) == '#DCDCDC' and await pg.evaluate(BG_PX, [3, 3, True]) == '#DC0000')
    data = await pg.evaluate("() => { const d = JSON.parse(JSON.stringify(currentProjectSaveData('m'))); delete d.backgroundColor; return d; }")
    await pg.evaluate("() => setBackgroundColor('#DC0000', false)")
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data); await pg.wait_for_timeout(300)
    check('bg mapart: older mapart save without the field opens on white carpet', await pg.evaluate("() => backgroundColor === '#DCDCDC'"))

async def test_space_pan(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(40); scale = 40; layoutAll(); handleToolBtn('pencil'); selectedColor = '#FF0000'; }")
    await pg.wait_for_timeout(200)
    x, y = await grid_point(pg, 10, 10)
    before = await pg.evaluate("() => [viewport.scrollLeft, viewport.scrollTop]")
    await pg.keyboard.down('Space')
    check('space pan: holding Space shows the grab cursor', await pg.evaluate("() => spacePanHeld && viewport.classList.contains('space-pan')"))
    await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.move(x - 120, y - 90, steps=6); await pg.mouse.up()
    await pg.keyboard.up('Space')
    after = await pg.evaluate("() => [viewport.scrollLeft, viewport.scrollTop]")
    check('space pan: Space + drag pans the view', after[0] > before[0] + 50 and after[1] > before[1] + 40, [before, after])
    check('space pan: nothing drawn while panning', await pg.evaluate("() => activeLayer().pixelData.every(c => c.every(v => v == null))"))
    check('space pan: releasing Space ends it', await pg.evaluate("() => !spacePanHeld && !viewport.classList.contains('space-pan')"))
    await tap(pg, 10, 10)
    check('space pan: the pencil draws again after release', await px(pg, 10, 10) == '#FF0000')
    await pg.evaluate("() => handleToolBtn('pan')")
    b2 = await pg.evaluate("() => viewport.scrollLeft")
    x, y = await grid_point(pg, 12, 12)
    await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.move(x + 100, y, steps=5); await pg.mouse.up()
    check('space pan: Pan tool mouse drag pans too (was broken)', await pg.evaluate("() => viewport.scrollLeft") < b2 - 50)
    ok = await pg.evaluate("""() => { const i = document.createElement('input'); document.body.appendChild(i); i.focus();
        i.dispatchEvent(new KeyboardEvent('keydown', { code: 'Space', key: ' ', bubbles: true })); const held = spacePanHeld; i.remove(); return held; }""")
    check('space pan: Space in a text field types instead of panning', ok is False)

REF_PNG = """() => { const c = document.createElement('canvas'); c.width = 64; c.height = 48; const x = c.getContext('2d');
    for (let by = 0; by < 6; by++) for (let bx = 0; bx < 8; bx++) { x.fillStyle = ((bx + by) % 2) ? '#123456' : '#ABCDEF'; x.fillRect(bx * 8, by * 8, 8, 8); }
    return c.toDataURL('image/png').split(',')[1]; }"""

async def test_reference_layer(pg):
    import base64
    await new_canvas(pg)
    png = base64.b64decode(await pg.evaluate(REF_PNG))
    await pg.locator('#refInput').set_input_files({'name': 'ref.png', 'mimeType': 'image/png', 'buffer': png})
    await pg.wait_for_timeout(800)
    check('ref: reference layer added and fitted (64 x 48 into 32 x 32)', await pg.evaluate("() => activeLayer().type === 'reference' && activeLayer().gw === 32 && activeLayer().gh === 24"))
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(40); scale = 40; layoutAll(); }")
    check('ref: canvas holds the image at its own size, not a zoom-sized buffer', await pg.evaluate("() => activeLayer().el.width === 64 && activeLayer().el.height === 48"))
    check('ref: auto shows sharp pixels when zoomed in', await pg.evaluate("() => activeLayer().el.style.imageRendering === 'pixelated'"))
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(0.25); scale = 0.25; layoutAll(); }")
    check('ref: auto smooths when shrunk', await pg.evaluate("() => activeLayer().el.style.imageRendering === 'auto'"))
    await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }"); await pg.wait_for_timeout(200)
    await pg.locator('#refSamplingRow button[data-sampling="pixel"]').click()
    check('ref: PIXEL forces sharp pixels at any zoom', await pg.evaluate("() => activeLayer().sampling === 'pixel' && activeLayer().el.style.imageRendering === 'pixelated'"))
    await pg.locator('#refSamplingRow button[data-sampling="smooth"]').click()
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(40); scale = 40; layoutAll(); }")
    check('ref: SMOOTH forces smoothing even zoomed in', await pg.evaluate("() => activeLayer().el.style.imageRendering === 'auto'"))
    await pg.evaluate("() => { activeLayer().sampling = 'auto'; renderLayersPanel(); }"); await pg.wait_for_timeout(200)
    await pg.locator('#refActualSizeBtn').click()
    check('ref: 1:1 ACTUAL SIZE = 64 x 48 cells on whole-cell positions', await pg.evaluate("() => { const l = activeLayer(); return l.gw === 64 && l.gh === 48 && l.gx === -16 && l.gy === -8 && l.rotation === 0; }"))
    await pg.evaluate("() => { closePanel(); zoomIndex = ZOOM_STEPS.indexOf(8); scale = 8; layoutAll(); }")
    # with the reference at 1:1 from (-16,-8), canvas cell (0,0) is image px (16,8) = block (2,1) -> odd -> #123456; cell (8,0) = block (3,1) -> even -> #ABCDEF
    await pg.evaluate("() => handleToolBtn('eyedrop')"); await tap(pg, 0, 0)
    check('ref: eyedropper on the selected reference picks its exact colour', await pg.evaluate("() => selectedColor") == '#123456', await pg.evaluate("() => selectedColor"))
    await pg.evaluate("() => setActiveLayer(0)")
    await pg.evaluate("() => handleToolBtn('eyedrop')"); await tap(pg, 8, 0)
    check('ref: eyedropper on a pixel layer still picks the reference shown underneath', await pg.evaluate("() => selectedColor") == '#ABCDEF', await pg.evaluate("() => selectedColor"))
    thumb_ok = await pg.evaluate("""() => new Promise(res => { const img = new Image(); img.onload = () => { const c = document.createElement('canvas'); c.width = 200; c.height = 200; const x = c.getContext('2d'); x.drawImage(img, 0, 0); res(x.getImageData(100, 100, 1, 1).data[3] > 0); }; img.src = generateThumbnailDataURL(frames, gridW, gridH, null); })""")
    check('ref: gallery card thumbnail shows the reference', thumb_ok)
    check('ref: PNG export still leaves it out (guide only)', await pg.evaluate("() => flattenLayersToCanvas(frames[activeFrameIndex].layerTree).getContext('2d').getImageData(5, 5, 1, 1).data[3] === 0"))
    th = await pg.evaluate("""() => new Promise(res => { const l = layers.find(l => l.type === 'reference'); const img = new Image(); img.onload = () => {
        const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const x = c.getContext('2d'); x.drawImage(img, 0, 0);
        const mid = x.getImageData(Math.floor(img.width / 2), Math.floor(img.height / 2), 1, 1).data;
        const big = new Image(); big.onload = () => { const c2 = document.createElement('canvas'); c2.width = big.width; c2.height = big.height; const y = c2.getContext('2d'); y.drawImage(big, 0, 0);
            res([img.width, Array.from(mid), Array.from(y.getImageData(Math.floor(big.width / 2), 0, 1, 1).data)]); }; big.src = makeThumbnail(l, 40); }; img.src = makeThumbnail(l, 6); })""")
    # 6 css px thumbnail of the 8px-block checker: blocks average out instead of nearest-neighbour picking one colour
    check('thumb: rendered at css size x devicePixelRatio', th[0] == 6 * await pg.evaluate("() => Math.min(3, window.devicePixelRatio || 1)"), th[0])
    check('thumb: shrinking averages colours (MediBang-style), not nearest-neighbour', th[1][0] not in (0x12, 0xAB) and 0x12 < th[1][0] < 0xAB, th[1])
    check('thumb: keeps the aspect ratio (64 x 48 letterboxed, top row is checker)', th[2][:3] in ([0x3A] * 3, [0x4A] * 3), th[2])
    data = await pg.evaluate("() => { layers.find(l => l.type === 'reference').sampling = 'pixel'; return JSON.parse(JSON.stringify(currentProjectSaveData('r'))); }")
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data); await pg.wait_for_timeout(500)
    check('ref: display mode and 1:1 placement saved with the project', await pg.evaluate("() => { const l = layers.find(l => l.type === 'reference'); return l && l.sampling === 'pixel' && l.gw === 64 && l.gx === -16; }"))

async def test_mapart_reference_match(pg):
    import base64
    await mapart_canvas(pg)
    png = base64.b64decode(await pg.evaluate(REF_PNG))
    await pg.locator('#refInput').set_input_files({'name': 'ref.png', 'mimeType': 'image/png', 'buffer': png})
    await pg.wait_for_timeout(800)
    await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }"); await pg.wait_for_timeout(200)
    check('refmatch: MAPART COLOURS button shown on a reference in Mapart, off by default', await pg.locator('#refMapartMatchBtn').count() == 1 and not await pg.evaluate("() => activeLayer().mapartMatch"))
    await pg.locator('#refMapartMatchBtn').click(); await pg.wait_for_timeout(200)
    check('refmatch: on = canvas-sized, unrotated, sharp; default scaling pixel', await pg.evaluate("() => { const l = activeLayer(); return l.mapartMatch && l.mapartScaling === 'pixel' && l.el.width === 128 && l.el.height === 128 && l.el.style.transform === 'none' && l.el.style.imageRendering === 'pixelated'; }"))
    CHECK = """() => { const l = activeLayer(), d = l.el.getContext('2d').getImageData(0, 0, 128, 128).data, ok = new Set(mapartAllowedHexes()); let bad = 0, n = 0;
        for (let i = 0; i < d.length; i += 4) { if (!d[i + 3]) continue; n++; if (d[i + 3] !== 255 || !ok.has(rgbToHexBytes(d[i], d[i + 1], d[i + 2]))) bad++; }
        const at = (x, y) => { const s = l.sampleAt(x, y); return s && s[3] ? rgbToHexBytes(s[0], s[1], s[2]) : null; };
        return { bad, n, a: at(32, 40), b: at(48, 48), out: at(5, 5), wa: mapartSnapColor('#ABCDEF'), wb: mapartSnapColor('#123456') }; }"""
    r = await pg.evaluate(CHECK)
    check('refmatch: every shown pixel is an allowed map colour, fully opaque, 64 x 48 of them', r['bad'] == 0 and r['n'] == 64 * 48, r)
    check('refmatch: pixel-perfect: each cell is its image pixel snapped', r['a'] == r['wa'] and r['b'] == r['wb'] and r['out'] is None, r)
    await pg.evaluate("() => toggleMapartStaircase()")
    r = await pg.evaluate(CHECK)
    check('refmatch: staircase on re-matches against the 3-shade palette', r['bad'] == 0 and r['a'] == r['wa'] and r['b'] == r['wb'], r)
    await pg.evaluate("() => setMapartColourMethod('euclidean')")
    r = await pg.evaluate(CHECK)
    check('refmatch: colour method change re-matches', r['a'] == r['wa'] and r['b'] == r['wb'], r)
    await pg.evaluate("() => setMapartColourMethod('mapartcraft')")
    await pg.evaluate("() => { const l = activeLayer(); l.gx = 0; l.gy = 0; l.gw = 32; l.gh = 24; l.layoutCSS(); renderLayersPanel(); }"); await pg.wait_for_timeout(150)
    px_mode = await pg.evaluate("() => { const s = activeLayer().sampleAt(0, 0); return rgbToHexBytes(s[0], s[1], s[2]); }")
    check('refmatch: PIXEL at half size picks one source pixel per cell (nearest)', px_mode in (await pg.evaluate("() => [mapartSnapColor('#ABCDEF'), mapartSnapColor('#123456')]")), px_mode)
    for mode in ('smooth', 'lanczos'):
        await pg.locator(f'#refMapartScalingRow button[data-scaling="{mode}"]').click(); await pg.wait_for_timeout(200)
        r = await pg.evaluate("() => { const l = activeLayer(), d = l.el.getContext('2d').getImageData(0, 0, 128, 128).data, ok = new Set(mapartAllowedHexes()); let bad = 0; for (let i = 0; i < d.length; i += 4) if (d[i + 3] && !ok.has(rgbToHexBytes(d[i], d[i + 1], d[i + 2]))) bad++; return [l.mapartScaling, bad]; }")
        check(f'refmatch: {mode.upper()} scaling selected, still only map colours', r == [mode, 0], r)
    lz = await pg.evaluate("""() => { const c = document.createElement('canvas'); c.width = 8; c.height = 8; const x = c.getContext('2d'); x.fillStyle = '#336699'; x.fillRect(0, 0, 8, 8);
        const o = lanczosResizeImage(c, 4, 4).getContext('2d').getImageData(0, 0, 4, 4).data; return Array.from(o.slice(20, 24)); }""")
    check('refmatch: Lanczos keeps a flat colour flat', all(abs(a - b) <= 1 for a, b in zip(lz, [0x33, 0x66, 0x99, 255])), lz)
    await pg.evaluate("() => { closePanel(); zoomIndex = ZOOM_STEPS.indexOf(4); scale = 4; layoutAll(); handleToolBtn('eyedrop'); }")
    await tap(pg, 3, 3)
    picked = await pg.evaluate("() => selectedColor")
    check('refmatch: eyedropper on it picks the matched map colour', picked == await pg.evaluate("() => { const s = activeLayer().sampleAt(3, 3); return rgbToHexBytes(s[0], s[1], s[2]); }"), picked)
    data = await pg.evaluate("() => JSON.parse(JSON.stringify(currentProjectSaveData('rm')))")
    await pg.evaluate("(d) => new Promise(r => openProjectFromSaveData(d, {}, r))", data); await pg.wait_for_timeout(500)
    check('refmatch: setting and scaling saved with the project', await pg.evaluate("() => { const l = layers.find(l => l.type === 'reference'); return l && l.mapartMatch && l.mapartScaling === 'lanczos' && l.el.width === 128; }"))
    await pg.evaluate("() => selectProfile('pixelArt')"); await pg.wait_for_timeout(200)
    check('refmatch: outside Mapart the reference shows the original image again', await pg.evaluate("() => { const l = layers.find(l => l.type === 'reference'); return l.el.width === 64 && l.el.height === 48 && l.el.style.transform !== 'none'; }"))

async def test_eyedrop_faded_reference(pg):
    import base64
    await new_canvas(pg)
    png = base64.b64decode(await pg.evaluate(REF_PNG))
    await pg.locator('#refInput').set_input_files({'name': 'ref.png', 'mimeType': 'image/png', 'buffer': png})
    await pg.wait_for_timeout(800)
    await pg.evaluate("() => { const r = activeLayer(); r.setActualSize(); r.gx = 0; r.gy = 0; r.opacity = 0.3; r.applyVisualState(); const t = frames[activeFrameIndex].layerTree; t.unshift(...t.splice(t.findIndex(n => n.layer === r), 1)); syncActiveLayersFromTree(); setActiveLayer(layers.findIndex(l => l.type === 'pixel')); zoomIndex = ZOOM_STEPS.indexOf(8); scale = 8; layoutAll(); closePanel(); }")
    for n in (1, 3):
        await pg.evaluate("(n) => { setEyedropSampleSize(n); handleToolBtn('eyedrop'); }", n)
        await tap(pg, 3, 3)
        c = await pg.evaluate("() => selectedColor")
        check(f'eyedrop: {n}x{n} on a pixel layer over a 30% reference picks its real colour', c == '#ABCDEF', c)
    await pg.evaluate("() => setEyedropSampleSize(1)")
    check('eyedrop: reference opacity left unchanged', await pg.evaluate("() => layers.find(l => l.type === 'reference').opacity === 0.3"))

async def test_mapart_pencil_after_empty_pick(pg):
    await mapart_canvas(pg)
    await pg.evaluate("() => handleSwatchClick('#DC0000')")
    await pg.evaluate("() => toggleMapartStaircase()")
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(4); scale = 4; layoutAll(); closePanel(); handleToolBtn('eyedrop'); }")
    await tap(pg, 10, 10)
    check('mapart empty pick: eyedropper on an empty pixel picks transparent', await pg.evaluate("() => selectedColor") is None)
    await pg.evaluate("() => handleToolBtn('pencil')")
    c = await pg.evaluate("() => selectedColor")
    check('mapart empty pick: pencil goes back to the last real colour, not the last palette swatch', c == '#DC0000', c)

async def test_eyedrop_from_colours(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { handleToolBtn('pencil'); handleSwatchClick('#FF0000'); }")
    await pg.evaluate(DRAW, [[[4, 4]], '#FF0000'])
    await pg.evaluate("() => { handleSwatchClick('#00FF00'); setBackgroundColor('#0000FF', false); openPanel('colors'); }"); await pg.wait_for_timeout(200)
    chip = await pg.evaluate("() => getComputedStyle(document.getElementById('currentColourChip')).backgroundColor")
    check('colours: drawing colour chip shows the selected colour, not the background', chip == 'rgb(0, 255, 0)', chip)
    check('colours: background swatch is labelled BG', await pg.evaluate("() => getComputedStyle(document.getElementById('bgSwatchColours'), '::after').content") == '"BG"')
    await pg.locator('#coloursEyedropBtn').click(); await pg.wait_for_timeout(200)
    check('colours: EYEDROPPER closes the drawer and arms the eyedropper', await pg.evaluate("() => currentTool === 'eyedrop' && openPanelName === null"))
    await tap(pg, 4, 4)
    check('colours: pick sets the colour, returns to the pencil and reopens Colours', await pg.evaluate("() => selectedColor === '#FF0000' && currentTool === 'pencil' && openPanelName === 'colors'"), await pg.evaluate("() => [selectedColor, currentTool, openPanelName]"))
    check('colours: chip updates to the picked colour', await pg.evaluate("() => getComputedStyle(document.getElementById('currentColourChip')).backgroundColor") == 'rgb(255, 0, 0)')
    await pg.evaluate("() => { closePanel(); openDrawer('tools'); }"); await pg.wait_for_timeout(200)
    await pg.locator('#toolsDrawer .tool-btn[data-tool="eyedrop"]').click(); await pg.wait_for_timeout(200)
    check('tools: Select a colour closes the Tools drawer at once', await pg.evaluate("() => currentTool === 'eyedrop' && drawerOpenName === null && !document.getElementById('toolsDrawer').classList.contains('open')"))
    await tap(pg, 4, 4)
    check('colours: eyedropper from the Tools drawer does not open Colours', await pg.evaluate("() => openPanelName === null"))
    await pg.evaluate("() => openDrawer('tools')"); await pg.wait_for_timeout(200)
    await pg.locator('#toolsDrawer .tool-btn[data-tool="pencil"]').click(); await pg.wait_for_timeout(100)
    check('tools: other tools still leave the drawer open', await pg.evaluate("() => drawerOpenName === 'tools'"))

async def test_mapart_colour_methods(pg):
    await mapart_canvas(pg)
    r = await pg.evaluate("""() => ({ red65: colourLab(255,0,0,false), red50: colourLab(255,0,0,true),
        de: [colourDeltaE2000([50,2.6772,-79.7751],[50,0,-82.7485]), colourDeltaE2000([50,0,0],[50,-1,2]), colourDeltaE2000([50,2.5,0],[73,25,-18]), colourDeltaE2000([60.2574,-34.0099,36.2677],[60.4626,-34.1751,39.4387])],
        hct: colourHct(255,0,0) })""")
    close = lambda a, b, t: all(abs(x - y) <= t for x, y in zip(a, b))
    check('colour: sRGB red in CIE Lab D65 / D50 matches published values', close(r['red65'], [53.2408, 80.0925, 67.2032], 0.01) and close(r['red50'], [54.2917, 80.8125, 69.8851], 0.01), r)
    check('colour: CIEDE2000 matches Sharma et al. 2005 test pairs 1, 7, 17, 25', close(r['de'], [2.0425, 2.3669, 27.1492, 1.2644], 0.0001), r['de'])
    check('colour: HCT of #FF0000 matches Material (hue 27.41, chroma 113.36, tone 53.24)', close(r['hct'], [27.408, 113.357, 53.24], 0.02), r['hct'])
    check('colour: Customise lists the 7 methods, default selected', await pg.evaluate("() => document.getElementById('mapartColourMethodSelect').options.length === 7 && mapartColourMethod === 'mapartcraft'"))
    # each method's snap must equal an independent brute-force nearest search in that method's space
    res = await pg.evaluate("""() => { const pal = mapartAllowedHexes().slice(); const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
        const sq = (p, q) => (p[0]-q[0])**2 + (p[1]-q[1])**2 + (p[2]-q[2])**2;
        const spaces = { euclidean: c => c, 'cie76-d65': c => colourLab(...c, false), 'cie76-d50': c => colourLab(...c, true), 'ciede2000-d65': c => colourLab(...c, false), 'ciede2000-d50': c => colourLab(...c, true), hct: c => colourHctPoint(...c) };
        const tests = [[74,144,217],[200,120,40],[30,200,180],[250,180,200],[90,60,140],[128,128,20],[10,10,60],[230,230,140]];
        const out = {}; let differs = false;
        const dflt = tests.map(t => { setMapartColourMethod('mapartcraft'); return mapartSnapColor(rgbToHexBytes(...t)); });
        for (const [m, f] of Object.entries(spaces)) {
            setMapartColourMethod(m);
            out[m] = tests.every((t, ti) => { const v = f(t); let best = null, bd = Infinity;
                for (const h of pal) { const q = f(rgb(h)); const d = m.startsWith('ciede') ? colourDeltaE2000(v, q) : sq(v, q); if (d < bd) { bd = d; best = h; } }
                const got = mapartSnapColor(rgbToHexBytes(...t)); if (got !== dflt[ti]) differs = true; return got === best; });
        }
        setMapartColourMethod('mapartcraft'); return [out, differs]; }""")
    check('colour: every method snaps to its true nearest map colour', all(res[0].values()), res[0])
    check('colour: switching method really changes some picks', res[1])
    await pg.evaluate("() => setMapartColourMethod('hct')")
    await pg.reload(); await pg.wait_for_timeout(1200)
    check('colour: method is remembered app-wide', await pg.evaluate("() => mapartColourMethod === 'hct' && document.getElementById('mapartColourMethodSelect').value === 'hct'"))
    await pg.evaluate("() => setMapartColourMethod('mapartcraft')")
    await mapart_canvas(pg)
    await pg.evaluate("() => { mapartSnapToasts = true; createSwatch('#4A90D9'); }")
    check('colour: debug snap toast names the map colour', '\u2192' in (await pg.locator('#appToast').text_content() or '') and await pg.evaluate("() => /^#[0-9A-F]{6}$/.test(selectedColor)"), await pg.locator('#appToast').text_content())
    await pg.evaluate("() => { mapartSnapToasts = false; saveMapartPrefs(); }")

async def test_eyedrop_sample_size(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(10); scale = 10; layoutAll(); }")
    # 3x3 around (5,5): 4 red, 5 blue -> average; one transparent pixel elsewhere doesn't darken a 3x3 at (20,20)
    await pg.evaluate(DRAW, [[[4,4],[5,4],[6,4],[4,5]], '#FF0000'])
    await pg.evaluate(DRAW, [[[5,5],[6,5],[4,6],[5,6],[6,6]], '#0000FF'])
    await pg.evaluate(DRAW, [[[19,19],[20,19],[21,19],[19,20],[20,20],[21,20],[19,21],[20,21]], '#00FF00'])
    await pg.evaluate("() => handleToolBtn('eyedrop')")
    check('eyedrop: sample size row shows while the eyedropper is on', await pg.evaluate("() => document.getElementById('eyedropControls').style.display === '' && document.querySelectorAll('#eyedropSampleRow button').length === 7"))
    await pg.evaluate("() => openDrawer('tools')"); await pg.wait_for_timeout(300)
    await pg.locator('#eyedropSampleRow button[data-size="3"]').click()
    await pg.evaluate("() => closeDrawer()"); await pg.wait_for_timeout(300)
    await tap(pg, 5, 5)
    check('eyedrop: 3 x 3 averages the square', await pg.evaluate("() => selectedColor") == '#71008E', await pg.evaluate("() => selectedColor"))
    await pg.evaluate("() => handleToolBtn('eyedrop')"); await tap(pg, 20, 20)
    check('eyedrop: transparent pixels in the square do not darken it', await pg.evaluate("() => selectedColor") == '#00FF00', await pg.evaluate("() => selectedColor"))
    await pg.evaluate("() => handleToolBtn('eyedrop')"); await tap(pg, 28, 28)
    check('eyedrop: an empty square picks transparent', await pg.evaluate("() => selectedColor") is None)
    check('eyedrop: sample size remembered', await pg.evaluate("() => localStorage.getItem(EYEDROP_PREFS_KEY) === '3'"))
    await pg.evaluate("() => { handleToolBtn('eyedrop'); setEyedropSampleSize(1); }"); await tap(pg, 5, 5)
    check('eyedrop: POINT picks the single pixel', await pg.evaluate("() => selectedColor") == '#0000FF')

LAYER_GRID = "() => { const l = activeLayer(); const out = {}; for (let x = 0; x < gridW; x++) for (let y = 0; y < gridH; y++) { const v = l.pixelData[x][y]; if (v != null) out[x + ',' + y] = v; } return out; }"

async def test_transform_basics(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { localStorage.removeItem(XF_PREFS_KEY); xfPrefs = { moveStep: 1, sizeStep: 1, rotStep: 15, interp: 'nearest', lock: true }; }")
    # 3 x 2 pattern at (4,4): row0 A B C, row1 D E F
    cols = {(4,4):'#AA0000',(5,4):'#00AA00',(6,4):'#0000AA',(4,5):'#AAAA00',(5,5):'#00AAAA',(6,5):'#AA00AA'}
    for (x, y), c in cols.items(): await pg.evaluate(DRAW, [[[x, y]], c])
    await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); }"); await pg.wait_for_timeout(300)
    await pg.locator('#layerTransformOpenBtn').click(); await pg.wait_for_timeout(300)
    check('xf: TRANSFORM opens the full screen around the layer content', await pg.evaluate("() => XF.open && document.getElementById('xfScreen').style.display === 'flex' && XF.st.w === 3 && XF.st.h === 2 && XF.st.cx === 5.5 && XF.st.cy === 5"))
    check('xf: Free and Mesh are shown as planned, Default is active', await pg.evaluate("() => document.querySelector('.xf-tab.active').textContent === 'Default' && document.querySelectorAll('.xf-tab-later').length === 2"))
    await pg.locator('#xfMoveStep').fill('10'); await pg.locator('#xfMoveStep').dispatch_event('change')
    await pg.locator('#xfRightBtn').click()
    check('xf: typed move step: one arrow press moves 10 px', await pg.evaluate("() => xfPrefs.moveStep === 10 && document.getElementById('xfX').value === '14'"))
    await pg.keyboard.press('ArrowDown')
    check('xf: keyboard arrows nudge by the step', await pg.evaluate("() => XF.st.cy === 15"))
    await pg.locator('#xfDoneBtn').click(); await pg.wait_for_timeout(200)
    g = await pg.evaluate(LAYER_GRID)
    check('xf: Done moves the pixels exactly (nearest)', g == {f'{x+10},{y+10}': c for (x, y), c in cols.items()}, g)
    check('xf: one undo step', await pg.evaluate("() => undoStack[undoStack.length - 1].type === 'layerTransform'"))
    await pg.evaluate("() => undo()")
    check('xf: undo puts them back', await pg.evaluate(LAYER_GRID) == {f'{x},{y}': c for (x, y), c in cols.items()})
    await pg.evaluate("() => redo()"); await pg.evaluate("() => undo()")
    # rotate 90 clockwise
    await pg.evaluate("() => { xfPrefs.rotStep = 90; xfOpen(); }")
    await pg.locator('#xfRotRightBtn').click(); await pg.evaluate("() => xfDone()")
    g = await pg.evaluate(LAYER_GRID)
    # box 3x2 centred (5.5,5) turns into 2 wide x 3 tall; edges snap to whole cells: x 5..6, y 4..6. Clockwise: left column = old bottom row.
    want = {'6,4':'#AA0000','6,5':'#00AA00','6,6':'#0000AA','5,4':'#AAAA00','5,5':'#00AAAA','5,6':'#AA00AA'}
    check('xf: rotate 90 with nearest keeps every pixel (columns become rows)', g == want, g)
    await pg.evaluate("() => undo()")
    await pg.evaluate("() => { xfOpen(); xfFlip('h'); xfDone(); }")
    g = await pg.evaluate(LAYER_GRID)
    check('xf: flip H mirrors in place', g == {'6,4':'#AA0000','5,4':'#00AA00','4,4':'#0000AA','6,5':'#AAAA00','5,5':'#00AAAA','4,5':'#AA00AA'}, g)
    await pg.evaluate("() => undo()")
    await pg.evaluate("() => { xfPrefs.sizeStep = 3; xfOpen(); }")
    await pg.locator('#xfGrowBtn').click()
    check('xf: + grows by the size step in px of width, height follows (ratio locked)', await pg.evaluate("() => XF.st.w === 6 && XF.st.h === 4"))
    await pg.evaluate("() => xfDone()")
    g = await pg.evaluate(LAYER_GRID)
    check('xf: 2x nearest resize doubles each pixel, centre anchored', len(g) == 24 and g.get('3,3') == '#AA0000' and g.get('4,4') == '#AA0000' and g.get('8,6') == '#AA00AA', sorted(g)[:4])
    await pg.evaluate("() => undo()")
    n_undo = await pg.evaluate("() => undoStack.length")
    await pg.evaluate("() => { xfOpen(); XF.st.cx += 4; }")
    await pg.locator('#xfCancelBtn').click()
    check('xf: cancel changes nothing and adds no undo step', await pg.evaluate("() => !XF.open && undoStack.length") == n_undo and await pg.evaluate(LAYER_GRID) == {f'{x},{y}': c for (x, y), c in cols.items()})
    # handle drag: right edge with ratio unlocked -> left edge stays
    await pg.evaluate("() => { xfPrefs.lock = false; xfOpen(); }"); await pg.wait_for_timeout(200)
    p0 = await pg.evaluate("() => { const m = xfViewMetrics(); const [gx, gy] = xfBoxPoint(XF.st, 1, 0); return [m.rect.left + m.ox + gx * m.sc, m.rect.top + m.oy + gy * m.sc, m.sc]; }")
    await pg.mouse.move(p0[0], p0[1]); await pg.mouse.down(); await pg.mouse.move(p0[0] + 3 * p0[2], p0[1], steps=4); await pg.mouse.up()
    check('xf: dragging the right handle widens it, left edge stays put', await pg.evaluate("() => Math.abs(XF.st.w - 6) < 0.01 && Math.abs((XF.st.cx - XF.st.w / 2) - 4) < 0.01 && XF.st.h === 2"), await pg.evaluate("() => XF.st"))
    await pg.keyboard.press('Escape')
    check('xf: Escape cancels', await pg.evaluate("() => !XF.open"))
    # off-canvas content is cut on Done
    await pg.evaluate("() => { xfOpen(); XF.st.cx -= 5; xfDone(); }")
    g = await pg.evaluate(LAYER_GRID)
    check('xf: content pushed off the canvas is cut off on Done', g == {'0,4':'#00AA00','0,5':'#00AAAA','1,4':'#0000AA','1,5':'#AA00AA'}, g)
    check('xf: step prefs remembered', await pg.evaluate("() => JSON.parse(localStorage.getItem(XF_PREFS_KEY)).moveStep === 10"))

async def test_transform_selection_and_kinds(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { xfPrefs = { moveStep: 1, sizeStep: 1, rotStep: 15, interp: 'nearest', lock: true }; }")
    await pg.evaluate(DRAW, [[[x, 10] for x in range(2, 8)], '#123456'])
    # select only x 2..4 of the row
    await pg.evaluate("() => { const m = new Uint8Array(gridW * gridH); for (let x = 2; x <= 4; x++) m[10 * gridW + x] = 1; setSelectionRaw(m, 3, selectionBoundsFromMask(m)); renderLayersPanel(); }")
    check('xf: with a selection the button says TRANSFORM SELECTION', await pg.evaluate("() => { openPanel('layers'); setLayersDrawerMode('full'); renderLayersPanel(); return document.getElementById('layerTransformOpenBtn').textContent.includes('SELECTION'); }"))
    await pg.evaluate("() => { xfOpen(); XF.st.cy += 5; xfDone(); }")
    g = await pg.evaluate(LAYER_GRID)
    check('xf: only the selected pixels move, the rest stays', g == {'2,15':'#123456','3,15':'#123456','4,15':'#123456','5,10':'#123456','6,10':'#123456','7,10':'#123456'}, g)
    check('xf: the selection moves with them', await pg.evaluate("() => wandSelection[15 * gridW + 3] === 1 && !wandSelection[10 * gridW + 3] && wandSelectionCount === 3"))
    await pg.evaluate("() => undo()")
    check('xf: undo restores pixels and selection together', await pg.evaluate("() => wandSelection[10 * gridW + 3] === 1") and len(await pg.evaluate(LAYER_GRID)) == 6 and (await pg.evaluate(LAYER_GRID)).get('3,10') == '#123456')
    await pg.evaluate("() => setSelectionRaw(null, 0, null)")
    # bicubic gives smooth in-between colours, no garbage
    await pg.evaluate("() => { xfPrefs.interp = 'bicubic'; xfOpen(); XF.st.rot = 30; XF.st.w *= 2; XF.st.h *= 2; xfDone(); }")
    g = await pg.evaluate(LAYER_GRID)
    check('xf: bicubic rotate/scale makes smooth edges (partial alpha), valid colours', any(v.startswith('rgba(') for v in g.values()) and all(v.startswith('#') or v.startswith('rgba(') for v in g.values()) and 'NaN' not in ''.join(g.values()), list(g.values())[:3])
    await pg.evaluate("() => undo()")
    # image layer
    ok = await pg.evaluate("""() => { const l = new ImageLayer('img', gridW, gridH); addLayer(l); reindexDom(); setActiveLayer(layers.length - 1);
        const d = l.imageData.data; const i = (3 * gridW + 3) * 4; d[i] = 200; d[i + 3] = 255; l.redrawFromData();
        xfPrefs.interp = 'nearest'; xfOpen(); XF.st.cx += 2; xfDone();
        const j = (3 * gridW + 5) * 4; return [l.imageData.data[i + 3], l.imageData.data[j], l.imageData.data[j + 3], undoStack[undoStack.length - 1].kind]; }""")
    check('xf: image layers transform too', ok == [0, 200, 255, 'image'], ok)
    # reference: lossless params
    import base64
    png = base64.b64decode(await pg.evaluate(REF_PNG))
    await pg.locator('#refInput').set_input_files({'name': 'ref.png', 'mimeType': 'image/png', 'buffer': png}); await pg.wait_for_timeout(700)
    r = await pg.evaluate("() => { const l = activeLayer(); xfOpen(); XF.st.rot = 45; XF.st.cx += 3; xfDone(); return [l.type, l.rotation, l.gx, undoStack[undoStack.length - 1].kind]; }")
    check('xf: reference layers just get new position/rotation (no resampling)', r[0] == 'reference' and r[1] == 45 and abs(r[2] - 3) < 0.01 and r[3] == 'reference', r)
    await pg.evaluate("() => undo()")
    check('xf: reference undo', await pg.evaluate("() => activeLayer().rotation === 0 && activeLayer().gx === 0"))
    # mapart: smooth resampling still ends on map colours
    await mapart_canvas(pg)
    await pg.evaluate(DRAW, [[[x, y] for x in range(10, 20) for y in range(10, 20)], '#DC0000'])
    await pg.evaluate(DRAW, [[[x, y] for x in range(14, 16) for y in range(10, 20)], '#3F6EDC'])
    ok = await pg.evaluate("() => { xfPrefs.interp = 'bilinear'; xfOpen(); XF.st.rot = 20; xfDone(); const allowed = new Set(mapartAllowedHexes()); let n = 0; for (let x = 0; x < gridW; x++) for (let y = 0; y < gridH; y++) { const v = activeLayer().pixelData[x][y]; if (v != null) { n++; if (!allowed.has(v)) return 'bad ' + v; } } return n; }")
    check('xf: mapart results snap to map colours', isinstance(ok, int) and ok > 50, ok)
    check('xf: Vector layers are not offered yet', await pg.evaluate("() => { addVectorLayer(); return xfOpen() === false && !XF.open; }"))

GRID_AT = "([x, y]) => { const r = container.getBoundingClientRect(); return [(x - r.left) / (r.width / gridW), (y - r.top) / (r.height / gridH)]; }"

async def test_wheel_zoom_anchor(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(10); scale = 10; resetCameraPanZoom(); layoutAll(); handleToolBtn('pencil'); }")
    await pg.wait_for_timeout(200)
    x, y = await grid_point(pg, 16, 16)
    await pg.keyboard.down('Space')
    await pg.mouse.move(x, y); await pg.mouse.down(); await pg.mouse.move(x - 140, y - 100, steps=6); await pg.mouse.up()
    await pg.keyboard.up('Space')
    mx, my = await grid_point(pg, 6, 9)
    before = await pg.evaluate(GRID_AT, [mx, my])
    await pg.mouse.move(mx, my); await pg.mouse.wheel(0, -100); await pg.wait_for_timeout(200)
    after = await pg.evaluate(GRID_AT, [mx, my])
    check('wheel zoom: after a Space pan, zooming in keeps the point under the mouse', await pg.evaluate("() => scale") == 12 and abs(before[0] - after[0]) < 0.3 and abs(before[1] - after[1]) < 0.3, [before, after])
    await pg.mouse.wheel(0, 100); await pg.wait_for_timeout(200)
    after2 = await pg.evaluate(GRID_AT, [mx, my])
    check('wheel zoom: zooming out is anchored too', await pg.evaluate("() => scale") == 10 and abs(before[0] - after2[0]) < 0.3 and abs(before[1] - after2[1]) < 0.3, [before, after2])

async def test_mouse_cursor_visibility(pg):
    await new_canvas(pg)
    await pg.evaluate("() => { zoomIndex = ZOOM_STEPS.indexOf(10); scale = 10; resetCameraPanZoom(); layoutAll(); handleToolBtn('pencil'); }")
    x, y = await grid_point(pg, 10, 10)
    await pg.mouse.move(x, y); await pg.mouse.move(x + 3, y + 3)
    check('cursor: pencil on a pixel layer uses the pixel cursor (system pointer hidden)', await pg.evaluate("() => container.classList.contains('pixel-cursor-mode') && getComputedStyle(container).cursor === 'none'"))
    await pg.wait_for_timeout(800)
    check('cursor: with a mouse the pixel cursor stays while hovering', await pg.evaluate("() => pixelCursor.classList.contains('visible')"))
    import base64
    png = base64.b64decode(await pg.evaluate(REF_PNG))
    await pg.locator('#refInput').set_input_files({'name': 'ref.png', 'mimeType': 'image/png', 'buffer': png}); await pg.wait_for_timeout(700)
    await pg.mouse.move(x + 6, y + 6)
    check('cursor: over a reference layer the system pointer shows', await pg.evaluate("() => !container.classList.contains('pixel-cursor-mode') && getComputedStyle(container).cursor !== 'none'"))
    await pg.evaluate("() => { setActiveLayer(0); handleToolBtn('pan'); }")
    await pg.mouse.move(x + 9, y + 9)
    check('cursor: a tool without a pixel cursor shows the system pointer', await pg.evaluate("() => !container.classList.contains('pixel-cursor-mode')"))

async def test_transform_live_preview(pg):
    await new_canvas(pg)
    await pg.evaluate(DRAW, [[[x, y] for x in range(32) for y in range(32)], '#3D7BE5'])
    await pg.evaluate("() => { addPixelLayer(); selectedColor = '#E5533D'; for (let x = 8; x < 20; x++) for (let y = 8; y < 20; y++) plot(x, y); const l = activeLayer(); l.opacity = 0.5; l.blendMode = 'multiply'; l.applyVisualState(); reindexDom(); xfPrefs.interp = 'nearest'; }")
    for rot, interp in ((30, 'nearest'), (15, 'bilinear')):
        same = await pg.evaluate("""([rot, interp]) => { xfPrefs.interp = interp; xfOpen(); XF.st.rot = rot; XF.st.cx += 2;
            const live = xfLiveComposite().getContext('2d').getImageData(0, 0, gridW, gridH).data;
            xfDone(); const real = flattenToCanvas().getContext('2d').getImageData(0, 0, gridW, gridH).data;
            let diff = 0; for (let i = 0; i < live.length; i++) if (Math.abs(live[i] - real[i]) > 1) diff++;
            undo(); return diff; }""", [rot, interp])
        check(f'xf live: preview equals the result after Done, with opacity + blend mode ({interp}, {rot} deg)', same == 0, same)
    keep = await pg.evaluate("() => { xfOpen(); const d = xfLiveComposite().getContext('2d').getImageData(12, 12, 1, 1).data; xfCancel(); return Array.from(d); }")
    check('xf live: the layer keeps its opacity and blend mode in the preview (50% multiply, not plain red)', keep[0] < 120 and keep[2] > 60, keep)
    check('xf live: opacity and blend mode untouched after Done', await pg.evaluate("() => { xfOpen(); XF.st.cx += 1; xfDone(); const l = activeLayer(); return l.opacity === 0.5 && l.blendMode === 'multiply'; }"))

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
