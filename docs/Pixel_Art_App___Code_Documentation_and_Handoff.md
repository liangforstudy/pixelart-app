# Pixel Art App --- Code Documentation & Handoff

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`).

`Pixel_art_app_core_code_philosophy.md` is authoritative over this document. Its central rule applies to everything here: no engine or algorithm is authoritative because it already exists; changing or adding one needs research (incl. a web search), pros/cons, agreement, and a lighter/faster check. This file records what exists, why, and what bit us.

## 0. Doc set and reading order

1. `Pixel_Art_App___Fix_List.md`, `Pixel_Art_App___Roadmap_Feature_Ideas.md`, `Pixel_Art_App___Renamed_Identifiers_and_Migration.md` -- read together, first.
2. This document.
3. Reference only (look up, don't read front to back): `Pixel_Art_App___DOM_Structure_and_Hooks.md`, `Pixel_Art_App___Functions_Documentation_Part1.md`/`Part2.md`, `Pixel_Art_App___Class_Methods_Documentation.md`.
4. Optional: `Pixel_Art_App___Build_History.md`, `Pixel_art_app_bugs_squashed_V1.md` (narratives).

Docs describe the code; the HTML is ground truth. LLM-written docs (these included) are not authoritative where they disagree with source. Checking these files costs fewer tokens than searching past chats, so keep them accurate. Cap: all docs together under 130 KB, no padding.

## 0.1 Working rules

- Plan in sessions before restructuring or roadmap work: in scope, deferred, systems touched. Get it confirmed before code.
- Full scope is expected; don't offer reduced-scope versions.
- After changing the HTML, ask whether to overwrite or bump the version before delivering. The file name never changes: it is always `Pixel_Art_App.html`, and each version is a commit on `main` (see the README, which wins over this doc). Bump `BUILD_VERSION` inside the file and name the commit after it (`V2.0: ...` for `V2_0`). Underscores for minor fixes (`V2_0_1`).
- Run `tests/run_tests.py` before every commit (see `tests/README.md`). Add a test for each new feature.
- Ask before removing ambiguous code. Dead-function scan: list top-level names, count occurrences, inspect count <= 1 by hand.
- Fix List: only explicitly requested items; don't propose additions.
- Verify every change: `node --check` on the script, function inventory diff, duplicate-id check, every `getElementById` target resolves. Behaviour: Playwright against the real file (below). `_perftest` builds for perf experiments outside the numbered lineage.
- Testing targets: iOS Safari (primary), w3schools run preview, desktop Edge/Chrome for DevTools.

## 1. Current state

**Purpose:** single-file HTML/CSS/JS pixel-art and sprite editor, iOS-Safari-first, MediBang Paint alternative. Three areas: pixel/vector canvas editor, Portrait 40x40 tile mode, PMD sprite-animation editor. A separate large-image editing app (ImageData pipeline, workers, tiled processing, colour-to-alpha, blur) is scoped (v0.1 doc) but not built.

**Recent builds**
- **V1_44** -- `bulkPixelWrite()`: loops of plot() redraw once instead of once per pixel. Fixed a full-canvas wand-delete freeze on ImageLayer (637k full-layer renders; now ~0.3s for 1.07M px). Wrapped: wand delete, rect delete, cut/stamp, resize stamp, shapes, brush stamps, stroke interpolation, bucket (both modes).
- **V1_44_1** -- ImageLayer got `applyVisualState`, `blendMode`, clone of blendMode (Add Pixel Layer crashed on >999px canvases). Raster gate: buttons greyed via `.size-gated` (still tappable) and a toast explains why; `showAppToast()` added.
- **V1_44_2** -- canvas checkerboard is 8 canvas px per square (floor 4 screen px below 0.5x zoom), matching Paint.NET/MediBang.
- **V1_44_3** -- canvas rotation persisted. `canvasRotation` was write-only (the release parked the angle there and zeroed `cameraRotation`, so every twist snapped back). `cameraRotation` is now the only rotation state; live snap within 3 degrees of 90s; `resetCameraTransform` became `resetCameraPanZoom` (zoom no longer straightens the canvas).
- **V1_45** -- `reanchorCameraPanAfterZoomSnap()`: pinch release no longer shifts the canvas (4.4 grid cells before, 0 after, any rotation). CLEAR and the per-row broom work on ImageLayer (`clearLayerContent()` prefers `layer.clear()`); `ImageLayer.setPixelData` rewritten against imageData.
- **V1_46** -- built-in on-screen keyboard and numeric keypad removed (iOS 16px focus-zoom fixed by 16px fields). Native inputs everywhere; the one remaining keydown listener is app shortcuts.
- **V1_47** -- IndexedDB gallery (section 3.4); one save format for file and gallery; Fix List 1, 2, 7 fixed; autosave on page hide.
- **V2_2** -- Mapart profile (section 3.11): whole-map canvases (128 px maps, up to 7x7), locked Minecraft map palette, staircase toggle, import snapping.

**Known open**
- Option B (drop PixelLayer's Proxy, keep both classes) decided, not implemented. A full-canvas PixelLayer bulk edit still builds a large string-keyed history Map + changes array (slow and memory-heavy on iOS near 999x999; won't hang).
- History is linear; whether to reintroduce branching is open (memory cost is per-entry size, not tree topology).
- Canvas size clamp 1-2000; raising to 4096 is a stretch goal (touch both clamp sites; don't merge with ReferenceLayer's unrelated 4096 buffer cap).
- Headless Playwright can't reproduce iOS Safari touch/memory behaviour; real-device checks still decide.

## 2. Principles

1. **Single file.** One HTML file, opens directly, no build step. CDN libraries are allowed for hard problems (e.g. 3D). **No new code comments (decided 2026-11-15):** don't write comments in new or changed code; explain the code in these docs instead. Leave existing comments alone unless the code around them changes (then update or remove them so they don't go stale).
2. **Touch-first, desktop-compatible.** Comfortable targets (44pt for handles), every operation reachable by touch; keyboard shortcuts are extras. iOS: native `confirm()` and `title` tooltips are unreliable (use tap-twice confirm and long-press tooltips).
3. **Document state > rendering > camera.** Document state is authoritative. Pan/zoom/rotate are presentation only: never document edits, undo entries, or layout rebuilds mid-gesture.
4. **Profiles:** Pixel Art (default), Portrait, Sprite, Mapart. `'photo'`/`'standard'` are legacy aliases normalized to `pixelArt`. Storage class is chosen by size, not profile: both sides <= 999 -> PixelLayer, else ImageLayer (Pixel Art only; Portrait, Sprite and Mapart always PixelLayer).
5. **Preserve entered dimensions** when switching profiles in New Canvas; validate at create/import.
6. **Pixel data is explicit**, separate from rendering, compositing, selection and overlays.
7. **Strokes are interpolated** between pointer events (`linePixels`); reuse it rather than re-inventing line walking.
8. **Tool semantics:** Pencil always 1px hard. Brush sized, optional soft. Soft Brush falloff. Hard Eraser removes pixels and selects the transparent swatch. Soft Eraser reduces alpha, doesn't select transparent. Choosing the eyedropper returns to the previous tool.
9. **Selection is data** (rect, wand mask, lasso; add/subtract; tolerance; contiguous/global). Marching ants and blue tint are visualization only and never become artwork.
10. **Colour-to-alpha** solves per channel for the minimum foreground alpha that explains the pixel over the sampled background (not exact-match fill). Hidden in Portrait.
11. **Layers vs groups:** `frame.layerTree` (groups hold children) is authoritative; `frame.layers` is a derived flat alias via `flattenLayerTree`.
12. **Portrait tiles are regions** of one document (`portraitTileKeyForPoint`), each with its own 15-colour palette. Isolation dims other tiles and blocks writes outside the active tile (`isPointOutsidePortraitIsolation`, called in `PixelLayer.plot()` and by the cursor).
13. **Import preserves information:** don't resize the canvas unexpectedly, keep transparency, name imports after the project. Portrait import only when both sides are multiples of 40, else fall back.
14. **History entries own their state** (sparse pixel deltas, tiles, snapshots; never live references to mutable objects). One user operation = one entry. Selection changes are history.
15. **Overlays never become artwork:** selection, ants, cursor, isolation, reference layers, future 3D.
16. **Performance:** no per-pixel DOM, no full rebuilds per pointer move, no huge allocations mid-gesture, typed arrays where sensible, deferred init that can't race a button.
17. **UI reflects real state:** a control is shown/enabled only when its prerequisites hold, and disabled means genuinely unavailable.
18. **Bottom bar scrolls** horizontally rather than shrinking buttons. The Panel tab is a panel-visibility manager.
19. **Hub stays focused** on projects; profile choice lives in New Canvas.
20. **3D is a separate subsystem**; **PSD and future formats never silently drop** unsupported data.
21. **Trace the runtime path.** Controls or classes existing is not a feature working.

## 3. Systems

### 3.1 Rendering and camera
- Canvas 2D only (WebGL2 removed: no benefit for a plain texture sample, 5-10x memory, iOS resize leak). ImageLayer renders through `Canvas2DImageRenderer`.
- Camera state: `cameraPanX/Y`, `cameraScale` (fluid during pinch), `cameraRotation` (persistent), applied by `applyCameraTransform()` on `#container` (origin centre). `scale` (document zoom, a `ZOOM_STEPS` value) is applied by `layoutAll()`.
- Two-finger gesture (`startTwoFingerGesture`/`updateCanvasPanZoomRotate` in `setupDrawingEvents`): anchor = the grid point under the finger midpoint, captured in untransformed local space; every move re-solves pan so it stays under the fingers. Rotation snaps to 90s within `ROTATION_SNAP_DEGREES` (3). On release: effective zoom snaps to the nearest `ZOOM_STEPS`, `cameraScale` folds to 1, rotation normalizes to 0-360, then `layoutAll()` and `reanchorCameraPanAfterZoomSnap()` keep the anchor fixed.
- Hit testing (`getPosFromClient`) inverts the same transform (rotation, cameraScale, scale), so drawing stays accurate while rotated.
- `bulkPixelWrite(fn)`: depth-counted; while open, `redrawFromData()` on either layer class only marks the layer dirty and `PixelLayer.plot` skips its 1x1 canvas paint; each dirty layer redraws once on exit (in `finally`).
- Checkerboard: shared `.checkerboard-bg` rule with CSS custom properties; per-screen profiles; canvas square size from `checkerSquareScreenPx()`.

### 3.2 Layers and data model
- PixelLayer: Proxy-tracked array-of-arrays; the Proxy costs ~7x vs no Proxy (benchmark 1000x700: 186ms vs 26ms; flat typed array 17ms). ImageLayer: flat `Uint8ClampedArray`, ~7x faster on large canvases.
- `window.ImageLayer = ImageLayer` is required; before V1_25 every size check read `undefined` and all canvases silently used PixelLayer. When it was fixed, ImageLayer paths ran at scale for the first time, which surfaced a string of latent ImageLayer bugs (V1_44 to V1_45).
- ImageLayer doesn't extend Layer; see the Class Methods rules.
- Mask/Clip: PixelLayer subclasses with `hookedTo`; must sit directly above their target and move with it as a pair. Vector layers can be masked.
- Blend modes: 16 CSS modes (`BLEND_MODE_OPTIONS`). Per layer: `mix-blend-mode` on the canvas. Per group: member canvases move into a `.group-blend-wrap` div with `isolation:isolate` + `mix-blend-mode`; `reindexDom()` repositions wrappers every call.
- `flattenTreeToCanvas()` is the single compositor (export, spritesheet, thumbnails, gallery export); reference layers are excluded.
- ReferenceLayer: source image + transform, re-rendered every layout (non-destructive, smart-object-like), but guide-only.
- Gradients: a gradient is a vector spline with `stops`; one gradient per dedicated holder layer (it fills the whole canvas); backbone and stop markers draw in `#gradientBackboneOverlay` so masks never hide them.

### 3.3 History
- `undoStack`/`redoStack`, linear. Caps: `MAX_UNDO` 40 and `HISTORY_MEMORY_BUDGET` (default 64 MiB, 8-512, persisted in `debugOptions`); `pruneHistoryLimit()` drops oldest first. A big fill can evict older entries; check that before assuming undo registration broke.
- Entry types: `pixels` (sparse deltas), `imageTiles` (64x64 tiles), `imageFull`, `canvasResize`, `selection`, `selectionTransform`, `tree`, layer add/delete, `addSpline`/`removeSpline`/`editSplinePoints`/`clearVectorLayer`/`replaceSplines`.
- `beginEdit()`/`commitEdit()` wrap raster operations: PixelLayer via Proxy capture into a Map; ImageLayer via tile capture, switching to full mode for whole-layer operations (`clear`, `setImageData`, `setPixelData`, flips).
- Undo History panel rows route through `jumpToHistoryNode` (tree bookkeeping is live even though history is linear).
- Tree operations: `captureTreeState()` before, `pushTreeOperation(label, before)` after.

### 3.4 Persistence (V1_47)
- **Save format** (`currentProjectSaveData`, v7): name, gridW/H, profile, active frame/layer, frames (serialized layers + tree, hooks as frame-relative indexes), `portraitTilePalettes`, `portraitActiveTileKey`, `portraitTileIsolation`. Raster layers are PNG data URLs; vector layers are splines; reference layers are source image + transform. The same format is used by file export (`saveProject`, gallery Save File), file import (`loadProjectFile`), and the gallery.
- **Loading** (`openProjectFromSaveData` over `buildFramesFromSaveData`): builds off-screen, then swaps state; resets history and selection; fit-to-screen zoom; guarded Portrait overlay creation. An unreadable layer image becomes a blank layer (reference dropped) with a toast, instead of hanging.
- **Gallery store:** `projectStore` holds metadata only; project data lives in IndexedDB `pixelAppProjects` (`meta` + `data`), or in `projectDataMemory` when storage is unavailable or a write failed. Boot reads `meta` only, so gallery size can't exhaust memory at startup; thumbnails lazy-load.
- **Saves:** Main Menu (`goToMainMenu`), autosave on `visibilitychange` hidden (not during PMD frame editing), rename (meta only), duplicate (deep copy of data), delete.
- **Crash guards** (`pixelAppBootGuard`): startup sets `bootsUnfinished` and clears it 2.5s after the gallery settles or on `pagehide`. Still set at next launch means a crash, which gives sticky safe mode (storage not read) until Try Again / Reset Storage. `openingProjectId` works the same way per project; the gallery then names that project and offers Save as file / Delete / Dismiss.
- **Failure modes handled:** no IndexedDB, open error or 8s hang, read failure, quota exceeded (toast, keeps data in memory), DB closed by another tab (versionchange), second tab (warning + sync), unopenable DB (Reset Storage deletes the DB and keeps memory-only projects).
- **Durability:** IndexedDB is a cache (Safari clears it after 7 days unvisited; quota eviction is origin-wide). `.pxproj.json` is the backup; the gallery says so.
- localStorage keys: see the Renamed Identifiers doc.

### 3.5 Tools
- `TOOL_REGISTRY` (20 tools, with category and section) drives button generation, `PIXEL_ONLY_TOOL_IDS`, `VECTOR_ONLY_TOOL_IDS`, `RASTER_TOOL_IDS`.
- `handleToolBtn()` is the only tool-switch entry point.
- Pixel/vector smart switch restores `lastPixelTool`/`lastVectorTool`.
- Raster gate: area > `rasterToolGateThresholdPx` (default 1,000,000) disables raster tools (tappable, toasts); force-enable and threshold live in Debug. Separate from the 999px storage rule.
- Selection transform: Resize (lock / free) and Rotate on rectangular selections; live preview on `#floatBuffer`, commit on release (Rotate waits for `#rotateConfirmBtn`; tool switch, re-grab or undo cancels). One `selectionTransform` undo entry.

### 3.6 Portrait
- 40x40 tiles, 15 colours per tile; the palette follows cursor position.
- Isolation enforced in `PixelLayer.plot()` and the vector Pen path; the cursor respects it.
- The palette DOM order is synced back to `portraitTilePalettes` on drag.
- The isolation overlay is lazily created; every activation path must guard-create it.

### 3.7 PMD sprite editor
- Separate peer screen. Reads/writes Multi Sheet packages: `AnimData.xml` + `{Name}-Anim/Offsets/Shadow.png`.
- Grid: columns = frames, rows = 1 or 8 directions, both from sheet size / FrameWidth/Height. Durations in 1/60s ticks. `CopyOf` aliases resolved in two passes.
- Offsets colours: black head, green body, red right hand, blue left hand.
- Names are exported byte-for-byte as imported.
- Hand-written ZIP (`readZip`/`writeZip`) over native Compression/DecompressionStream; DEFLATE export.
- Editing: `spriteAnimEnterFrameEditMode` snapshots editor globals, extracts one frame into a PixelLayer, and shows the pixel canvas with a Done button; exit writes back and restores. 15-colour cap per whole Anim sheet (`spritePaletteEditActive`).
- Offset markers are draggable on the preview. Onion skinning is edit-time only.
- Layout: controls drawer (onion, playback), floating scrubber and d-pad, tab bar.

### 3.8 Search and command palette
- `fuzzyScore`: exact 1200 > prefix 850 > substring 650 > ordered subsequence (20 per char) > -1.
- `buildSearchResults` merges layer-tree nodes (best of name / path / text) and `commandRegistry` entries (name + aliases; `hiddenWhen` excludes), top 30.
- The layer search covers layers only; the command palette (z 3000) covers both. Empty query shows the first 20 commands.

### 3.9 Debug
- `#debugDrawer` (z 9000, above the palette); reachable from the Hub, the canvas and the PMD screen.
- Stats: profile, size, render mode, zoom, frames/layers, undo depth, history MiB, raster estimate, saved projects + storage usage, DPR.
- Log: 300 entries; TOUCH/JS/TRACE toggles; capture-phase listeners installed first.
- New debug toggles follow the existing pattern: module flag, toggle function syncing `.active`, persist in `debugOptions`, re-layout if it affects rendering.

### 3.11 Mapart (V2_2)
- Canvas = whole Minecraft maps of 128x128 px, 1-7 per side (896 px max keeps it PixelLayer). New Canvas takes the size in maps; the resize screen is off; the number sheet and `applyCanvasResizeOffset` round to whole maps.
- `MAPART_DATA`: 61 colour sets for Minecraft 26.2, each `[id, dark, normal, light, [[block, survivalTier, anarchyTier], ...]]` (tier 0 = not survival-friendly, null = unknown). Generated by script from mapartcraft's `coloursJSON.json` and the reviewed tier sheet; regenerate rather than hand-edit.
- Palette: staircase off = the 61 normal shades, on = all 183. `syncMapartPalette` stashes the previous palette on entering Mapart and restores it on leaving; it is called from `selectProfile` and `openProjectFromSaveData`. Picker, Manage Colours and swatch-array import are hidden; `createSwatch` snaps instead of adding; `replaceVisiblePalette` refuses outside `mapartBuildingPalette`.
- Colour matching = mapartcraft's default ("Better Colour", `mapartLab`, ported exactly incl. its `/12` linear segment and 2.55 L scale), squared distance, cached per distinct RGB in `mapartSnapCache` (cleared when the palette changes). A test pins picks against mapartcraft's own code.
- `PixelLayer.plot()` snaps every Mapart write (alpha < 0.5 becomes empty), so every tool stays on-palette. Imports bypass `plot()`, so `importAsNewProjectFromImage` and `importImageAsNewLayer` call `mapartSnapLayerInPlace`. A Mapart import must be whole maps; otherwise it opens as Pixel Art with a toast (same rule as Portrait).
- Staircase off with light/dark pixels present asks first: convert (one `pixelsMulti` history entry across layers) or keep and flag (hint shows the live count).
- Soft brush, soft eraser and colour to alpha are hidden (`MAPART_TOOL_FALLBACK`). Vector layers are not snapped yet.
- Saved: `mapartStaircase` in the project data.

### 3.12 Layers drawer
- `#panel-layers` is still panel `'layers'` (openPanel/closePanel), restyled as a frosted right-side drawer. No `#panelBackdrop` for it, so the canvas stays usable.
- Modes: `strip` (thumbnails only) and `full` (`#layersTopPane` settings + icon row, `#layersSplitHandle`, `#layersListPane`). Prefs in `layersDrawerPrefs` (`pixelArtLayersDrawerPrefs`): mode, returnAfterStroke, glass (40-100), split (15-85).
- A pointerdown on `#viewport` adds `.stroke-hidden`; when the last pointer lifts it comes back (and re-renders thumbnails) or closes, per returnAfterStroke.
- Selected layer/group settings (title, bin, broom, mask/clip move buttons, opacity, blend, reference transform) render into `#layerSettingsPane`, not into the list. Rows hold only colour tag, thumbnail, eye, name, badge.
- Drag to reorder (`beginTreeDrag`): 280 ms hold, floating `.layer-drag-ghost`, slot rects cached at drag start, rows slide with transforms, non-passive `touchmove` blocks iOS scroll, `pointercancel` restores everything, auto-scroll near the pane edges, 380 ms hover over a group's middle drops inside. Nothing re-renders until the drop; one undo step via `performTreeDrop`. Visual order is the reverse of array order: "above row X" = mode `after`, "below row X" = mode `before`.
- Debug: `openDrawer('debug')` no longer closes panels and `openPanel` keeps Debug open. `#debugFab` (z 9500) is always reachable.

### 3.10 Text input
- Native keyboard only (V1_46). Fields are 16px to stop iOS focus-zoom. Number fields use `inputmode="numeric"`.

## 4. Danger zones

- **Mapart writes:** anything that writes `pixelData` directly instead of `plot()` must snap in Mapart (`mapartSnapLayerInPlace`), or off-palette colours get in.

- **Choke points:** every pixel write must reach `PixelLayer.plot()` (isolation, lazy materialise, undo). The global `plot()` wrapper is not the choke point; tools call `layer.plot()` directly.
- **Proxy capture:** only writes through the Proxy are captured. Any wholesale `pixelData` replacement needs explicit before-capture (see `PixelLayer.setPixelData`).
- **ImageLayer parity:** it doesn't inherit from Layer. Grep what generic code calls on layers when adding features; copying a PixelLayer method without adapting it caused the V1_45 CLEAR crash and canvas detachment.
- **Bulk writes:** inside `bulkPixelWrite` the visible canvas is stale; read `pixelData`/`imageData`, never `layer.el`/`layer.ctx`.
- **One source of truth:** `canvasRotation` (V1_44_3) and the gallery's live `frames` references (V1_47) were second copies that drifted. Don't add parallel state.
- **Camera math:** pan is solved in rotated screen space against the current scale. Anything that changes `scale` after a gesture must re-anchor (`reanchorCameraPanAfterZoomSnap`). Don't `layoutAll()` mid-gesture.
- **Lazy init:** `#portraitTileIsolationOverlay` must be guard-created on every canvas-activation path (it silently no-oped on the import path once).
- **One-time positioning:** a helper that creates-and-positions once won't re-position when neighbours change (group blend wrappers stuck at `#container`'s first child). Re-run placement every call.
- **DOM vs data:** DOM edits (drag-reorder, inline edits) need an explicit write-back to the backing array, or the next re-render discards them.
- **Memory:** a large canvas isn't cheap just because Canvas 2D displays it. Mobile canvases past size limits stop rendering silently (ReferenceLayer cap). History budget evictions look like broken undo.
- **Storage:** never make IndexedDB the only copy; never clear-then-write; keep boot reading metadata only; clear crash guards only on success or `pagehide`.
- **Overlay canvases:** setting `canvas.width/height`, even to the same value, clears the canvas. Guard resizes in anything called per pointer move.
- **Flip buttons:** `pointerup` on purpose.
- **Confirmations:** `makeTapTwiceConfirm` / `elementTapTwiceConfirm` only; `confirm()` is a regression.
- **HTML vs JS escapes:** a JS-style unicode escape (backslash-u-2190) typed into raw HTML renders as those literal characters, not an arrow; in markup use the actual character.
- **One-finger pan:** `clampPanScrollWithinEdgeMargin` keeps a sliver visible; load-bearing, not dead code.

## 5. Verification harness

- **Static:** extract the inline script and run `node --check`; compare function inventories before and after (added/removed/duplicates); check duplicate ids and unresolved `getElementById` targets (9 known unresolved as of V1_47).
- **Behavioural:** Playwright + Chromium (`/opt/pw-browsers`). Serve over HTTP for IndexedDB tests. Drive real mouse events for tools; use synthetic `TouchEvent`s for pinch/twist.
- **Useful probes:** layer pixel counts (`pixelData` or `imageData` alpha), canvas alpha at a point (catches stale canvases), undo stack deltas, `bulkPixelWriteDepth` back to 0, grid point under the finger midpoint across pinch release, reload persistence. To fake a crash for the guard tests, stub `updateBootGuard` before navigating.
- **Limits:** no iOS touch semantics, memory pressure or Safari storage policy; real-device checks remain the final word.
