# Pixel Art App --- DOM Structure & Hooks

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`).

Part A: what exists and how it nests (by id; line numbers omitted because they go stale). Part B: what wires it. For what a function does, see the Functions docs.

# Part A. DOM structure

## Direct children of `<body>`

Screens (one visible at a time, except PMD frame editing, which shows `#pixel-canvas-screen` over `#sprite-anim-screen`):

- **`#gallery-screen`** (z 1100) -- `#gallery-header` (title, `#hubVersionLabel`, `#hubDebugBtn`, `#hubSpriteEditorBtn`), **`#galleryStorageStatus`** (storage state, backup reminder, recovery buttons; rendered by `renderStorageStatus()`), `#gallery-grid` (rebuilt by `renderGallery()`).
- **`#sprite-anim-screen`** (z 1150) -- `#sprite-anim-header` (back/title/import/export), `#spriteAnimFileInput`, `#sprite-anim-body` (`#spriteAnimListsRow`, `#spriteAnimPreviewWrap`, `#spriteAnimFrameDataSection`, `#spriteAnimEditSection`, `#spriteAnimLayerToggles`), floating `#spriteAnimScrubRow` (z 850, play + readout), floating `#spriteAnimDPadController` (z 860, `#spriteAnimDirectionGrid` + opacity slider), `#spriteAnimTabBar` (z 900: Controls / D-pad / Debug).
- **`#init-screen`** (z 1000) -- profile buttons, `#w-group`/`#h-group` digit pickers, import/start-fresh, `#hubImageInput`.
- **`#pixel-canvas-screen`** -- see below.

Modals / overlays: `#spriteAnimToast` (1400), **`#appToast`** (1450, timed toast), `#new-canvas-modal` (1150, `#new-canvas-sheet` rebuilt on every open), `#gallery-ctx-backdrop` (1190) + `#gallery-ctx-menu` (1200; rename/duplicate/resize/export/save-file/delete), `#gallery-rename-modal` (1800), `#resize-canvas-modal` (1850), `#drawerBackdrop` (945; 8999 with `.debug-open`), `#spriteControlsDrawer` (onion + playback), `#debugDrawer` (9000: `#debugDrawerControls` with `#buildVersionLabel` + `#debugStats`, `#debugDrawerSplitHandle`, `#debugLogPane`/`#debugLog`).

## `#pixel-canvas-screen`

- `#viewport` > `#canvasWrap` > **`#container`** (`.canvas-container .checkerboard-bg`; the camera transform target; every layer canvas lives here, or inside a `.group-blend-wrap` div for groups with a blend mode). Container children in stacking order: `#canvas-safety-overlay` (100), `#floatBuffer` (150), `#shapePreview` (160), `#gridOverlay` (170), `#vectorHandlesOverlay` (175), `#gradientBackboneOverlay` (176), `#selectionOverlay` (177), `#wandSelectionOverlay` (178), `#selectionHandlesOverlay` (179), `#selectionBox` / `#rotateConfirmBtn` / JS-created `#portraitTileIsolationOverlay` (180), `#pixel-cursor` (200).
- `#panelBackdrop` (800), `#swatchEditBackdrop` (840), `#leftEdgeZone`/`#rightEdgeZone` (940).
- `#toolsDrawer` (`.side-drawer`, 950): tool rows generated from `TOOL_REGISTRY` into `#toolRow-*` containers, `#pixelToolsSection` (brush controls, bucket/wand/colour-to-alpha controls, selection tools incl. transform buttons), `#vectorToolsSection` (sub-mode row, `#gradientStopsBar`), `#flipToolsSection`.
- Floating panels (`.floating-panel`, 850, mutually exclusive with drawers): `#panel-view`, `#panel-colors` (`#palette`, `#swatchValueStrip`), `#panel-layers` (`#framesSection`, selection toolbar/actions, `#layerSearchShell`, `#layerSearchResults`, `#layersList`), `#panel-panel`, `#panel-customisation` (menu + tools/checker/gradient sections), `#panel-history`, `#panel-file`.
- `#floatingBar` (900): `#tab-tools`, `#tab-view`, `#tab-colors`, `#tab-layers`, `#tab-file`, `#tab-panel`, `#tab-customisation`, `#tab-history`, `#tab-debug`.
- `#undoFab`/`#redoFab` (780), `#rotationResetFab` (870), `#portraitIsolationHint` (870), `#spriteAnimFrameEditDoneBtn` (1200).

## JS-created elements
- `#portraitTileIsolationOverlay` -- lazily, guarded `if (!getElementById(...))` at every canvas-activation path (incl. `openProjectFromSaveData`). A new activation path must include the guard.
- `#globalCommandPalette` (3000) with `#globalCommandInput`/`#globalCommandResults`, built on first open.
- Swatch-array menu + backdrop (2000 / 1999).
- `.long-press-tooltip` (2000), `.group-blend-wrap` divs.
- Storage-status buttons (`#storageRetryBtn`, `#storageResetBtn`, `#crashedSaveBtn`, `#crashedDeleteBtn`, `#crashedDismissBtn`), rebuilt on each render.

## Z-index tiers
Container overlays 100-200 < FABs 780 < panel backdrop 800 < swatch-edit backdrop 840 < panels / PMD scrub 850 < d-pad 860 < hints 870 < tab bars 900 < edge zones 940 < drawer backdrop 945 < drawers 950 < flip buttons 960 < init 1000 < gallery 1100 < new-canvas / PMD screen 1150 < ctx menu 1190-1200 < toasts 1400-1450 < rename 1800 < resize 1850 < swatch menu / tooltip 1999-2000 < command palette 3000 < Debug 8999/9000. Grep before relying on this.

# Part B. Hooks

## Conventions
- Most buttons: inline `onclick="uiAction(fn)"`. `uiAction` cancels an armed CLEAR and Main Menu confirm first.
- Not wrapped: `#clearBtn` (`handleClearClick`, own two-tap), `#mainMenuBtn`.
- Tool buttons: generated with `data-tool` and routed through `handleToolBtn()`. Tools: eyedrop, colorToAlpha, pan, pencil, brush, softBrush, hardEraser, softEraser, bucket, vgradient, wand, lasso, select, line, rect, ellipse, vpen, vshape, vedit, vmove.
- Destructive actions: `makeTapTwiceConfirm` (stable id) or `elementTapTwiceConfirm` (dynamic element). Never native `confirm()` (zero calls remain).
- Flip buttons use `pointerup`, not `click`, on purpose (click+touchend double-dispatch). Don't "simplify".

## Window / document listeners
| Target | Event | Purpose |
|---|---|---|
| window | error, unhandledrejection | Debug JS log |
| document | touchstart, click (capture) | Debug TOUCH log (capture phase so stopPropagation can't hide taps) |
| window | keydown | `setupKeyboardShortcuts`: undo/redo, Ctrl/Cmd+K palette (the only keydown listener since V1_46) |
| `#viewport` | wheel (non-passive) | zoom |
| `#viewport` + window | mouse/touch start/move/end/cancel | `setupDrawingEvents()` gesture engine; one shared state object, treat as a unit |
| `#viewport` | scroll | FAB positions |
| window, visualViewport | resize | FABs + canvas-wrap padding |
| document | visibilitychange | `autosaveOpenProject()` when hidden |
| window | pagehide | clears boot/opening crash guards (a crash never fires it) |
| BroadcastChannel `pixelAppProjects` | message | two-tab warning + gallery sync |
| backdrops | touchstart/mousedown | close panel / drawer |
| `#leftEdgeZone`/`#rightEdgeZone` | touch | edge-swipe drawers |

## Mapart (V2_2)
`#panel-colors` > `#mapartPaletteRow` (above `#palette`): `#mapartStaircaseBtn`, `#mapartPaletteHint`, `#mapartStaircaseOffBox` (`#mapartStaircaseOffCount` + convert/keep/cancel). `#palette.mapart-locked` hides delete badges. Hub `#profileRow` and the New Canvas sheet have a `mapart` profile button.

## Gallery
- Cards: long-press opens the context menu; tap opens (`openProjectFromStore`, guarded against double taps). New Canvas card: long-press imports an image, tap opens the modal.
- Context menu: rename (pointerup > native modal, persists meta), duplicate (deep copy of save data), resize (opens the project, then `openResizeFor()`: the resize screen or the sheet, per `resizePrefs`; a second `#ctx-resize-numbers` item when `resizePrefs.both`), export PNG (builds frames off-screen), save file (downloads stored save data), delete (removes from memory and IndexedDB).

## Resize screen (V2_1)
`#resizeScreen` (z 1160: above the editor and gallery, below the sheet at 1850) holds `#rsCanvas` (pointer + wheel listeners from `setupResizeScreen()`) and `#rsBar` (`#rsSize`, `#rsDetail`, `#rsLockBtn`, `#rsSnapBtn`, `#rsNumbersBtn`, `#rsResetBtn`, `#rsDiscardBtn`, `#rsConfirmBtn`). State lives in `RS`. Entry buttons: New Canvas `#newCanvasCreateBtn` (Pixel Art; `#newCanvasSizeBox` hidden), `#ctx-resize`, `#ctx-resize-numbers`, File panel `#fileResizeBtn` / `#fileResizeNumbersBtn`. Preferences: Customise > `#customisationSection-resize` (`#resizePrefOpensBtn`, `#resizePrefBothBtn`), saved in localStorage `pixelArtResizePrefs`.

## Resize modal
`input` > `setResizeDimension`; `blur` restores the dataset value; anchor grid click sets the anchor; apply > `applyCanvasResize`, or with `dataset.target='rect'` (opened by NUMBERS on the resize screen) it moves `RS.rect` instead. Fields are native `inputmode="numeric"` (built-in keypad removed V1_46).

## Debug drawer
REFRESH STATS, PRINT VERSION, RESET PROJECT STORAGE (tap twice), UNRESTRICTED VECTOR, history-budget slider, raster-gate slider + force-enable, log toggles (touch/js/trace), COPY LOG, CLEAR LOG, split handle.

## Restructuring notes
- Screens borrow from each other (PMD frame edit reveals the pixel canvas on top); don't assume strict exclusivity.
- Keep Debug's capture listeners on `document` and installed first.
- `#portraitTileIsolationOverlay` creation is still duplicated across activation paths; centralizing it into one helper would remove the risk.
