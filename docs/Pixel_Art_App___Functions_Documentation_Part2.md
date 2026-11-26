# Pixel Art App --- Functions Documentation Part 2

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`). 486 top-level functions total across Part 1 and Part 2; class methods are in `Pixel_Art_App___Class_Methods_Documentation.md`. Part 1: Camera / Zoom / Pan to Layers & Layer Tree. Part 2: Mask/Clip Layer to ZIP/XML Codec. One line per function: signature, then what it does. Alphabetical within each category. Source is ground truth.


## Mask/Clip Layer

- `compositeMaskOrClip(base, effect)` The actual pixel-level compositing math for a hooked mask or clip layer over its base layer.

## New Canvas Flow

- `closeNewCanvasModal()` Removes the `.open` class from `#new-canvas-modal`, hiding the New Canvas UI.
- `newCanvasCreation()` The New Canvas sheet's "Create Canvas" handler (renamed from `initApp()`.
- `openNewCanvasModal()` Builds the entire New Canvas sheet from scratch on every open.
- `updateNewCanvasImportButton()` See the main documentation's PMD Editor implementation entry for the full behavioral writeup.

## Portrait Mode

- `clampPointToPortraitTile(x,y,originX,originY)` Clamps a point to stay within the same 40x40 tile that `(originX, originY)` belongs.
- `ensurePortraitTilePalette(key)` Returns the palette array for a given tile key.
- `finishPortraitIsolationPick(x,y)` Completes the guided "pick a tile to isolate" flow: resolves the tapped point to a tile key.
- `hidePortraitTileIsolationOverlay()` Hides the tile-isolation dimming overlay element, if it exists.
- `isolationRegionForPoint(x,y)` Rect of (x,y)'s 40x40 tile when Portrait isolation is on, else null. Generalized region helper.
- `isPointOutsidePortraitIsolation(x,y)` The shared boundary-check function: returns `false` immediately if not in Portrait profile.
- `portraitDimensionsCompatible(w, h)` Returns whether a width/height pair is valid for the Portrait 40x40 tile grid.
- `portraitTileCount()` Returns the total number of 40x40 tiles in the current canvas.
- `portraitTileKeyForPoint(x,y)` Returns the tile-key string (`"col,row"`) for a grid point.
- `samplePortraitTilePalettes(img)` The initial palette-population pass run when importing a Portrait spritesheet image.
- `syncPortraitPaletteForPoint(x,y,force=false,resetIsolation=false)` The function that keeps the visible palette panel showing the correct tile's colours.
- `updatePortraitTileControls()` Rebuilds the Portrait-specific controls block prepended to the top of the Layers panel.
- `updatePortraitTileOverlay()` Rebuilds the four dimming-mask rectangles that make up the Portrait tile-isolation overlay.

## Project Save/Load

- `buildFramesFromSaveData(data, onDone)` Builds frames/layers/trees/hooks from save data without touching editor state.
- `currentProjectSaveData(name)` Save data (v7) for the open project, incl. Portrait palettes, active tile and isolation. The one serializer for file export and the gallery.
- `downloadProjectData(data, fileBase)` Downloads save data as `<name>.pxproj.json`.
- `importAsNewProjectFromImage(img, file)` Imports a picked image as a brand-new project.
- `loadProjectFile(file)` Reads a .pxproj.json and opens it via openProjectFromSaveData as a new, unsaved gallery project.
- `openProjectFromSaveData(data, opts, onDone)` Replaces the open project with one built from save data: restores profile, Portrait palettes/active tile/isolation, resets history.
- `openProjectFromStore(id, onDone)` Loads a gallery project (memory or IndexedDB) and opens it; sets the opening guard for the duration; optional onDone.
- `saveProject()` File panel Save: downloads currentProjectSaveData() as `project.pxproj.json`.
- `serializeFramesForSave(framesArr)` Frames -> save shape: serialized layers (hooks as frame-relative indexes) plus serialized layer tree.

## Reference Layer

- `buildReferenceTransformUI(layer)` Builds the small transform-editing panel shown beneath a Reference layer's row when it's.

## Search / Command Palette

- `buildSearchResults(query)` See the main documentation's Search Engine / Command Palette entry for the full algorithm.
- `closeGlobalCommandPalette()` Hides the command palette.
- `fuzzyScore(query,text)` See the main documentation's Search Engine / Command Palette entry for the full four-tier.
- `registerBuiltInCommands()` Populates the entire built-in command registry.
- `registerCommand(id,name,aliases,action,category,hiddenWhen)` Pushes one entry onto the global `commandRegistry` array, defaulting `aliases` to `[]`.
- `renderGlobalCommandResults(query)` See the main documentation's Search Engine / Command Palette entry for the full behavioral.

## Selection

- `animateSelectionAnts(now)` The marching-ants animation loop, throttled to update roughly every 140ms (using a timestamp.
- `applySelectionMask(incoming, mode)` Merges an incoming selection bitmask into the live `wandSelection` according to the combine.
- `buildSelectionBoundary(mask)` Given a Wand-selection bitmask, extracts just the *boundary* pixels as a flat array.
- `clearWandSelection()` Clears the Wand/pixel-mask selection, recording the change as an undoable selection-state.
- `commitInProgressTransform()` ** -- if a Resize/Rotate transform drag is currently live (`window.__selTransformDrag` set).
- `cutSelectionBuffer(layer, sel)` Copies the selection into a buffer and clears it from the layer (bulkPixelWrite); returns the buffer.
- `deleteSelection()` The generic "delete whatever is selected" entry point.
- `deselect()` Clears the rectangular selection, exits "moving selection" mode, clears any Wand selection.
- `drawSelectionAnts()` Renders the marching-ants boundary onto a dedicated overlay canvas.
- `hasWandSelection()` Returns whether a non-empty Wand/pixel-mask selection currently exists (`wandSelection` is set.
- `performDeleteSelection()` Clears the rectangular selection on the active layer inside bulkPixelWrite; one undo transaction.
- `performLassoSelection(points)` Converts a freehand lasso point-path into a rectangular-bitmask selection.
- `performWandSelection(x,y)` Executes an actual Wand-tool selection at a tapped point.
- `recordSelectionUndo(before, after)` Pushes a selection-type undo entry, but only if `before`/`after` are both present.
- `renderWandSelection()` Thin alias that just calls `updateSelectionOverlay()`.
- `resampleRotatedBuffer(buf, angle)` Rotates a cut buffer by angle: grows bounds to fit, inverse-rotates each cell, nearest-neighbour. Returns {out, offsetX, offsetY}.
- `resetSelectionState()` A harder reset than `deselect()`: clears both the Wand mask.
- `sameSelectionSnapshot(a,b)` Deep-equality check between two selection snapshots (as produced by `selectionSnapshot()`).
- `selectionBoundsFromMask(mask)` Computes the tightest rectangular bounding box containing every set bit in a selection mask.
- `selectionContainsDescendantOfSelected(node)` Returns whether a given node's *ancestor chain* contains another already-selected node.
- `selectionHandleHitTest(x, y)` ** -- hit-tests a grid point against the currently active transform mode's handle set (via.
- `selectionHandlePoints(sel, mode)` ** -- returns the handle points for a rectangular selection under a given transform mode.
- `selectionSnapshot()` Captures a lightweight, independent copy of the current selection state.
- `selectProfile(p, forcedWidth = null, forcedHeight = null)` The canonical profile-switch function: normalizes legacy profile name aliases.
- `selectSpriteAnimAnimation(name)` Switches the PMD editor's active animation: shows the missing-name toast.
- `selectSpriteAnimDirection(row)` Sets the PMD sprite editor's active direction row, refreshes the direction-grid UI.
- `selectSpriteAnimFrame(i)` Jumps the PMD sprite editor to a specific frame index, resets the playback tick counter.
- `setPixelSelectionMode(mode)` Sets the pixel-selection combine mode (`'replace'`/`'add'`/`'subtract'`).
- `setSelectionRaw(mask, count, rect)` Low-level setter that directly assigns the Wand mask, its count.
- `setSelectionResampleMethod(v)` ** -- sets `selectionResampleMethod`.
- `toggleMoveSelection()` Toggles "moving selection" mode on/off, syncing the move-selection button's active state.
- `toggleSelectionTransformMode(mode)` ** -- turns one of the three Selection Transform modes (`'lockRatio'`/`'free'`/`'rotate'`).
- `updateSelectionBox()` Positions and sizes the visible rectangular-selection outline element in screen pixels.
- `updateSelectionHandles()` ** -- shows/hides and redraws the Resize/Rotate handle overlay (`#selectionHandlesOverlay`).
- `updateSelectionOverlay()` Redraws the blue Wand-selection tint overlay: hides everything selection-related.
- `updateSelectionToolsVisibility()` Shows or hides the selection-tools UI section based on whether any selection currently exists.
- `updateSelectionTransformButtons()` ** -- syncs the three transform-mode buttons'.
- `updateSpriteAnimFrameListSelection()` The lightweight, non-rebuilding way to update.
- `withinSelection(x, y)` Returns whether a grid point falls inside the current rectangular `selection` bounds.

## Sprite Animation / PMD Editor

- `async canvasToPngBytes(sourceImg)` Image/canvas -> PNG bytes for export.
- `closeSpriteAnimEditor()` Hides the PMD sprite-editor screen and stops its playback animation loop.
- `async exportSpriteAnimZip()` Exports the PMD package zip (AnimData.xml + sheets) with names exactly as imported.
- `async importSpriteAnimZip(arrayBuffer)` Imports a PMD sprite zip: AnimData.xml plus per-animation sheet triplets; names preserved exactly.
- `resetSpriteAnimToastDismissPreference()` Clears the persisted "don't show the missing-animation-name toast again" preference.
- `setupSpriteAnimScrubber()` Wires the scrubber `<input>`'s `input` event to jump to the corresponding frame.
- `spriteAnimActiveAnim()` Returns the raw animation entry for whatever name is currently active.
- `spriteAnimDirectionCount()` Returns the current animation's direction-row count by delegating.
- `spriteAnimDirectionCountFor(a)` Given any animation object, computes its direction-row count from the actual sheet height.
- `spriteAnimEnsurePalette(animName)` Lazily computes and caches (in `spriteAnimProject.palettes`) the 15-colour-capped palette.
- `spriteAnimEnterFrameEditMode()` The PMD editor's entry into real pixel editing for one frame.
- `spriteAnimExitFrameEditMode()` The inverse: reads the temporary layer's `pixelData` back out.
- `spriteAnimFrameCellRect(anim, frameIndex, direction)` Computes the source-pixel rectangle (`sx, sy, w, h`) for one frame cell within a sprite sheet.
- `spriteAnimFrameCount()` Returns the current animation's frame count, i.e. the length of its `durations` array.
- `spriteAnimFrameOverride(animName, dir, frame)` Looks up the manual per-frame override object for a specific animation/direction/frame.
- `spriteAnimOffsetsScratchCanvas()` Lazily creates and returns a shared scratch `<canvas>` element used for offset-marker pixel.
- `spriteAnimReadCenterOffsetMarker(anim, direction, frameIndex)` Reads the head-anchor offset marker's position for a specific frame.
- `spriteAnimResolvedAnim()` Returns the active animation's *resolved* target (following a `CopyOf` alias to the real.
- `spriteAnimToastDismissed()` Reads the persisted "don't show again" preference for the missing-animation-name toast.
- `stopSpriteAnimLoop()` Cancels the sprite-anim playback's `requestAnimationFrame` loop handle, if one is running.
- `toggleSpriteAnimDPad()` Shows/hides the floating d-pad controller.
- `toggleSpriteAnimOffsetsVisible()` Flips the Offsets-layer visibility flag, updates the toggle button's active state.
- `toggleSpriteAnimPlayback()` Flips the play/pause state and updates the play button's icon accordingly.
- `toggleSpriteAnimShadowVisible()` Flips the Shadow-layer visibility flag, updates the toggle button's active state.
- `updateSpriteAnimDPadOpacity()` Applies the d-pad opacity slider (default 50%).
- `updateSpriteAnimToggleButtons()` Syncs both the Shadow and Offsets toggle buttons' `.active` CSS class to match.

## Storage / Persistence

- `autosaveOpenProject()` Saves the open project into the gallery when the page is hidden (visibilitychange). Skipped outside the pixel canvas and during sprite frame editing.
- `broadcastProjectsChanged()` Posts `changed` to other tabs.
- `deleteProjectRecord(id)` Deletes a project from memory and both stores.
- `formatBytes(n)` KB/MB/GB label.
- `getProjectData(id, cb)` cb(data, err): project save data from memory first, else IndexedDB.
- `idbGetAllMeta(db)` Reads every `meta` record (never `data`).
- `async initProjectStorage(force)` Boot entry for the gallery: honours the boot guard, opens IndexedDB, loads project metadata only.
- `isGalleryVisible()` True when `#gallery-screen` is shown.
- `newProjectId()` Time-based numeric id (Date.now()*100 + random) so two tabs cannot collide.
- `openProjectDb()` Opens DB `pixelAppProjects` (stores `meta`, `data`) with an 8s timeout; resolves {db, state, error}, never rejects.
- `persistProject(entry, data)` Writes meta, plus data if given, in one transaction; on failure keeps data in `projectDataMemory` and toasts. data=null = meta-only.
- `projectMetaOf(p)` Picks the metadata fields stored in `meta`.
- `readBootGuard()` Reads the `pixelAppBootGuard` localStorage object ({} on failure).
- `refreshStorageEstimate()` Updates `projectStorageUsage` from navigator.storage.estimate().
- `async reloadProjectListFromDb()` Re-reads metadata after another tab changed storage; re-renders the gallery if visible.
- `renderStorageStatus()` Renders `#galleryStorageStatus`: loading/ready/unsupported/failed/safe text, backup reminder, crashed-project banner.
- `reportStorageWriteError(err)` Toast for a failed write; distinguishes QuotaExceededError.
- `requestPersistentStorage()` Calls navigator.storage.persist() once, after the first successful write.
- `resetProjectStorage()` Deletes the whole database (recovery for an unopenable DB), reopens fresh, keeps memory-only projects. Behind a tap-twice confirm.
- `setupProjectChannel()` BroadcastChannel `pixelAppProjects`: hello/here handshake (warns once about a second tab) and `changed` sync.
- `sortProjectsNewestFirst(list)` Sorts by updatedAt descending, in place.
- `updateBootGuard(patch)` Merges fields into the boot guard.
- `warnOtherTab()` One-time toast that the app is open in another tab.

## Tools: General

- `applyCanvasSizeToolGating()` Greys raster tool buttons via `.size-gated` (not `disabled`, so taps still reach handleToolBtn to explain); if the current tool is gated.
- `handleToolBtn(t)` The single tool-switch entry point: cancels Portrait pick mode, refuses size-gated raster tools, Portrait colorToAlpha fallback.
- `rasterGateToastMessage()` Toast text explaining the raster gate for the current canvas.
- `rasterToolIsSizeGated(id)` True when id is a raster tool and canvas area exceeds the gate (and force-enable is off).
- `renderToolButtons()` Generates every tool button from TOOL_REGISTRY into its `section` container. Run once at load.
- `updateToolVisibility()` The central function keeping tool-related UI honest against the active layer's actual type.

## Tools: Wand / Bucket / Fill

- `confirmWandDelete()` Arms the tap-twice delete confirmation for a Wand selection.
- `performWandDelete()` Deletes every wand-selected pixel on the active layer inside bulkPixelWrite, y-outer loop; one undo transaction, then clears the selection.
- `setBucketTolerance(v)` Clamps and stores a new bucket-fill tolerance value, updates the tolerance label in the UI.
- `setWandTolerance(v)` Same pattern as `setBucketTolerance`, for the Wand tool's own tolerance value/label.
- `toggleBucketMatch()` Flips the bucket tool between fuzzy and exact colour matching.
- `toggleBucketScope()` Flips bucket fill between contiguous and global matching, updates the scope button's label.
- `toggleWandMatch()` Same pattern as `toggleBucketMatch()`, for the Wand tool.
- `toggleWandScope()` Same pattern as `toggleBucketScope`, for the Wand tool's scope.
- `wandColourDistance(a,b)` Computes Euclidean RGB distance between two hex colour strings.
- `wandKey(x,y)` Builds the string key (`"x,y"`) used to address a point in Wand-selection-related maps/sets.
- `wandMatches(c,target)` The Wand tool's colour-match predicate: in exact mode, strict equality; in fuzzy mode.

## UI: Drawers / Panels

- `closeCustomisationSection()` Returns the Customisation panel to its menu.
- `closeDrawer()` Closes whichever side drawer is open: removes `.open` from every `.side-drawer`.
- `mkIosSlider(initialValue, onChange)` iOS-style 0-100 slider (label inside the fill, checker track). Returns {el, setValue}.
- `openCustomisationSection(section)` Opens a Customisation sub-section (tools / checker / gradient).
- `openDrawer(which)` Opens a named side drawer: cancels any in-progress clear-confirmation.
- `toggleDrawer(which)` Opens a drawer if it isn't already the open one, or closes it if it.

## UI: Toasts / Modals / Confirm

- `attachLongPressTooltip(el, text)` Long-press tooltip on an element (native title does not fire on iOS touch).
- `confirmDeleteSelectedItems()` Arms the tap-twice delete confirmation for a multi-select layer-tree deletion.
- `dismissSpriteAnimToast()` Dismisses the "missing animation name" toast; if the "don't show again" checkbox is checked.
- `elementTapTwiceConfirm(btn, idleText, armedText, onConfirm, timeoutMs)` The per-element sibling of the shared `makeTapTwiceConfirm()` pattern.
- `hideAppToast()` Fades out and hides the toast.
- `hideLongPressTooltip()` Removes the tooltip.
- `makeTapTwiceConfirm(opts)` The shared tap-twice destructive-action confirmation factory: returns `{trigger, cancel`.
- `showAppToast(msg, ms)` Timed toast in `#appToast` (default 5s, tap to dismiss); re-showing restarts the timer.
- `showLongPressTooltip(anchorEl, text)` Shows a tooltip bubble above (or below) an element.
- `showSpriteAnimMissingNameToast(names)` Displays the "these animation reference a target that could not be found" toast (see main.

## Uncategorized / Core

- `advanceSpriteAnimPlayback()` The actual per-tick playback logic (called from the `requestAnimationFrame` loop.
- `anchorOffset(oldW, oldH, newW, newH, ax, ay)` Computes the pixel offset to apply when resizing a canvas with a given anchor point (`ax`/`ay`.
- `applyPixelDelta(entry, forward)` Applies one pixel-history entry's sparse delta to a layer, in either direction.
- `beginEdit()` The shared entry point for starting a trackable pixel edit, branching by layer class.
- `bulkPixelWrite(fn)` Runs fn with per-pixel redraws suppressed; each dirtied layer redraws once at the end.
- `cancelClear()` Reverts the Clear button out of its "confirming" state: resets its label back to the default.
- `catmullRomPath(points, closed)` Generates a smooth curve through an arbitrary sequence of control points using Catmull-Rom.
- `catmullRomPoint(p0, p1, p2, p3, t)` Standard Catmull-Rom spline interpolation: given four control points and a parameter `t`.
- `centerCanvasInViewport()` Scrolls the viewport so the canvas is centered both horizontally and vertically.
- `clearDragIndicators()` Removes the `drop-before`/`drop-after`/`drop-inside` CSS classes from every layer row.
- `clearHold()` Cancels the currently-pending long-press timer (`holdTimer`).
- `cloneSpline(sp)` Returns a deep-enough copy of a vector spline object (new `points` array with new point.
- `collectSelectedRootsSorted()` Gets the root-selected nodes (via `getRootSelectedNodes`).
- `commitEdit(pending)` The counterpart to `beginEdit()`, finalizing a tracked pixel edit into an actual undo entry.
- `commitFreehandSpline(layer, points, isShape)` Finalizes a freehand vector-pen stroke into a permanent spline on the layer.
- `commitShape(kind, start, end)` Draws line/rect/ellipse pixels onto the active layer (bulkPixelWrite).
- `continueEditing()` Resumes an already-open project without touching its size: reveals the pixel-canvas screen.
- `copyImageTile(imageData, tileX, tileY, tileSize = PHOTO_HISTORY_TILE_SIZE)` Extracts one tile's worth of pixel bytes out of a full `ImageData` buffer at the given tile.
- `copySafeColours(colours)` Filters an array down to only valid, well-formed 6-digit hex colour strings.
- `crc32(bytes)` Standard CRC-32 checksum, with its lookup table lazily built once.
- `createImageRenderer(layer)` Factory that constructs a `Canvas2DImageRenderer` for a given `ImageLayer`.
- `decodeOffsetMarkers(ctx, cellX, cellY, fw, fh)` Scans a rectangular region of a canvas context for the four PMD offset-marker colours.
- `describeEl(el)` Renders a DOM element as a short `TAG#id.class1.class2` diagnostic string for Debug-log.
- `duplicateSelectedItems()` Duplicates every root-selected node: groups the selection by shared parent first.
- `ellipseOutlinePixels(x0, y0, x1, y1)` Computes the pixel points forming an ellipse outline between two corner coordinates.
- `enforcePixelArtRendererForDimensions()` Re-checks, after any resize or dimension-changing operation.
- `escapeHtml(s)` Escapes `&`, `<`, `>` in a string before it's injected into the DOM as HTML.
- `estimateMemoryBytes()` Claude's own raster-memory tally: sums `width × height × 4` bytes across every.
- `executeClear()` CLEAR button confirm: clears the active pixel-like layer via clearLayerContent in one undo transaction; no-op on vector/reference layers.
- `fallbackProfileForDimensions(w, h)` Always returns `'pixelArt'`; kept as a named function with an explanatory comment noting.
- `flattenToCanvas()` Thin wrapper that flattens the current frame's `layers` array into a single composited canvas.
- `flushRendererInvalidation()` Processes the pending renderer-invalidation queue immediately.
- `generateThumbnailDataURL(framesArr, gW, gH)` Renders frame 0 of a project into a 200x200 thumbnail (nearest-neighbour scaling.
- `getCanvasRenderingMode(width, height)` Returns `'image'` or `'pixel'` depending on whether the given dimensions exceed the image-mode.
- `getCanvasRenderingModeLabel(width, height)` Human-readable version of `getCanvasRenderingMode`.
- `getDropTargetAt(x,y)` Given screen coordinates, finds the nearest ancestor `.layer-row` element under that point.
- `getViewportSize()` Returns the current viewport width/height, preferring the more accurate.
- `goToMainMenu()` Main Menu: closes panels/selection, saves the open project via saveCurrentStateToStore, shows the gallery.
- `handleClearClick()` The Clear button's tap handler, implementing its own two-tap confirm pattern (distinct.
- `handleMainMenuClick()` Logs a trace event and triggers the tap-twice-confirm pattern for returning to the main menu.
- `handleManageClick()` Toggles the palette's "editing" mode, updating both the palette's CSS class.
- `handleStartFreshClick()` The "Start Fresh" button handler: if no project is open, creates a new canvas immediately.
- `hideFloatingBuffer()` Hides the floating selection/move buffer element, if present.
- `hideShapePreview()` Hides the shape-tool live-preview canvas, if present.
- `initSpriteAnimEditor()` The PMD sprite editor's setup entry point: wires the file input, scrubber.
- `invalidateDocumentRender(reason = 'document-state', immediate = true)` The higher-level invalidation entry point above `invalidateRenderer`.
- `invalidateRenderer(layer, reason = 'document-state', immediate = true)` Queues a single layer for re-render; if `immediate` is true, flushes right away.
- `isPixelLike(layer)` Returns whether a layer is one of the "pixel-like" types that support per-pixel editing.
- `layoutAll()` Re-applies size/position styles: container size, checker size/offset, camera transform, every layout-dependent overlay.
- `linePixels(x0, y0, x1, y1)` Bresenham's line algorithm, returning every pixel coordinate along a straight line between two.
- `makeThumbnail(layer, size)` Renders a single layer's own small preview thumbnail.
- `makeTrackedPixelData(layer, w, h, source)` The factory behind `PixelLayer`'s Proxy-based undo-capture mechanism.
- `moveSelectedBlock(direction)` Moves the entire current tree selection up or down as a block.
- `normalizeSel(x0, y0, x1, y1)` Normalizes an arbitrary two-corner selection rectangle into a canonical `{x0,y0,x1,y1}` shape.
- `openSpriteAnimEditor()` Shows the PMD sprite-editor screen and fully refreshes every part of its UI at once before.
- `performDeleteSelectedItems()` The actual multi-select deletion once confirmed.
- `plot(x, y)` The top-level, UI-facing single-point drawing function (distinct.
- `pointInPolygon(px,py,pts)` Standard ray-casting point-in-polygon test against an arbitrary point array.
- `positionFloatingBuffer(gx, gy, w, h)` Positions and sizes the floating selection-move buffer element in screen space.
- `printBuildVersion()` Logs the current `BUILD_VERSION` via `traceLog`.
- `pushUndo(entry)` The single true entry point for adding an entry to the undo/redo history tree.
- `rectOutlinePixels(x0, y0, x1, y1)` Computes the pixel points forming a rectangle's outline between two corners.
- `refreshHookedComposites()` Re-renders every pixel/image layer that has a mask or clip layer hooked directly above it.
- `reindexDom()` Re-orders layer canvases to match the tree; layers in a blended group go into its wrapper, and wrappers are repositioned every call.
- `remapDuplicatedHooks(node,map)` After `duplicateTreeWithRemap` has produced a duplicated subtree plus an old-id-to-new-id map.
- `renderLogToggleButtons()` Syncs the three Debug-drawer log-capture toggle buttons' active states to their corresponding.
- `renderSpriteAnimAnimList()` Rebuilds the PMD editor's animation list, applying the Idle-always-first display sort.
- `resampleFloatingBuffer(buf, newW, newH, method)` ** -- resamples a cut selection buffer to a new pixel size for the Resize transform path.
- `resetCanvasRotation()` Sets cameraRotation to 0 and re-layouts.
- `revealPixelCanvas()` Shows the pixel/vector editor screen (renamed from `revealMainApp()`.
- `rgbaString(r,g,b,a)` Builds a CSS `rgba(...)` string from channel values, clamping each to its valid range.
- `rgbToHex(rgb)` Converts a CSS `rgb(...)`/`rgba(...)` string into a `#RRGGBB` hex string.
- `rgbToHexBytes(r, g, b)` Converts three 0-255 integer channel values into a `#RRGGBB` uppercase hex string.
- `sameImageTile(a,b)` Deep byte-for-byte comparison of two image-tile data objects.
- `saveCurrentStateToStore(existingId, nameOverride)` Saves the open project (fresh thumbnail + save data) into projectStore and IndexedDB; updates in place if existingId. Returns the id.
- `saveImage()` Flattens the current canvas to a single composited image.
- `scheduleHookedCompositeRefresh()` Debounces mask/clip composite refreshes to at most once per animation frame.
- `setLogToggle(kind, on)` Sets one of the three Debug-log capture flags by name.
- `setGridLines(on)` Sets `showGridLines`, syncs `#gridToggleBtn`, redraws the overlay. Called on project open (saved `gridLines`) and new project/import (off).
- `setPenWidth(v)` Sets the vector Pen tool's stroke width and updates its label.
- `setupDigitKeyboardAdvance(root)` Wires a container of digit `<select>` elements.
- `setupDrawingEvents()` The canvas gesture engine: one shared state object for pointer/touch drawing, tools, two-finger pan/zoom/rotate, selection transforms.
- `setupEdgeSwipe(zoneId, drawerName, expectDirection)` Wires a screen-edge touch zone to open a given drawer once a swipe past a fixed 28px threshold.
- `setupKeyboardShortcuts()` Wires desktop keyboard shortcuts and mouse-wheel zoom on the viewport.
- `setupPickers()` Builds the New Canvas / Resize sheet's 4-digit width/height number pickers (a `<select>` per.
- `setupSpriteAnimFileInput()` Wires the PMD sprite package file `<input>`'s change handler.
- `setupSpriteAnimOffsetDrag()` Wires the draggable offset-marker interaction on the PMD editor's preview canvas.
- `setupSpriteAnimOnionListeners()` Wires all four onion-skinning UI fields to update the corresponding `spriteAnimState` values.
- `setupSpriteAnimSpeedListener()` Wires the PMD editor's playback-speed field: on input, updates the speed multiplier.
- `shouldUseImageMode(width, height)` Returns whether either dimension exceeds `IMAGE_MODE_MAX_DIMENSION`.
- `showFloatingBuffer(buf, gx, gy)` Renders a cut/copied selection buffer into the floating-buffer preview canvas at its own.
- `showShapePreview(kind, start, end)` Renders a live preview of an in-progress line/rect/ellipse shape drag onto a dedicated overlay.
- `simplifyPoints(points, epsilon)` The Ramer-Douglas-Peucker path-simplification algorithm.
- `stampFloatingBuffer(layer, buf, sel)` Writes a moved buffer into the layer at sel (bulkPixelWrite).
- `stampResizedBuffer(layer, buf, sel)` Writes an already-resampled buffer into the layer at sel (bulkPixelWrite).
- `startHold(callback)` Arms a 600ms long-press timer that calls `callback` if not cancelled first.
- `startSpriteAnimLoop()` Starts the PMD sprite editor's playback `requestAnimationFrame` loop.
- `toggleGridLines()` Flips the grid overlay on/off via `setGridLines`.
- `toggleLineExtendMode()` Toggles Extend Line mode; entering it also turns off vertex-delete mode.
- `togglePlay()` Toggles flipbook-frame playback: clears any existing playback interval, and if now playing.
- `toggleSelectedVisibility()` Toggles visibility for every root-selected node at once.
- `toggleVertexDeleteMode()` Toggles vertex-delete mode; entering it also turns off line-extend mode (mutually exclusive.
- `traceLog(...args)` The shared trace-logging entry point used throughout the UI-action code.
- `transformActive()` Returns whether transform mode is currently active on a Reference layer specifically.
- `uiAction(fn)` The shared wrapper nearly every button's tap handler goes through.
- `updateCanvasWrapPadding()` Sizes the canvas wrapper's padding to a full viewport-dimension on each side.
- `updateGridOverlay()` Redraws `#gridOverlay`: pixel lines (CSS gradient, 4x+), and in Mapart `.grid-chunk-line` (16 px, 0.5x+) and `.grid-map-line` (128 px, red, always) divs.
- `updateRotationFab()` Shows the reset-rotation FAB when cameraRotation is 3+ degrees off square.
- `updateRotationLabel()` Writes cameraRotation (0-359) to `#rotationLabel`.
- `updateSpriteAnimDirectionGrid()` Rebuilds the PMD editor's direction-selector grid: for the standard 8-row case.
- `updateSpriteAnimOnionFields()` Syncs the PMD editor's four onion-skinning UI fields to the current `spriteAnimState`.
- `updateSpriteAnimScrubberRange()` Sets the PMD editor's scrubber `<input>` min/max/value to match the current animation's frame.
- `updateUI()` A broad, frequently-called UI-sync function distinct from `updateToolVisibility`.
- `updateUndoRedoFabs()` Syncs the enabled/disabled state and opacity of all four undo/redo-related buttons to whether.
- `updateVectorHandles()` Redraws the on-canvas vector point-handle overlay.
- `writeImageTile(imageData, tile, tileSize = PHOTO_HISTORY_TILE_SIZE)` Writes a stored history tile's pixel data back into a full `ImageData` buffer at the tile's.

## Vector Tools

- `activeGradientSpline(layer)` The spline with stops on a vector layer, or null.
- `addVectorLayer()` Adds a new `VectorLayer`, wrapped in a try/catch that shows an alert pointing at the Debug tab.
- `commitGradientSpline(layer, points)` Commits a 2-point gradient spline, replacing any existing gradient on the layer; `replaceSplines` undo; refreshes mask composites.
- `createGradientHolderLayer(pixelLayer)` New vector layer above a pixel layer to hold one gradient (one layer per gradient); undoable.
- `deleteGradientStop(sp, stopIndex)` Deletes a stop by index; blocked below 2 stops.
- `deleteVectorPoint(layer, hit)` Deletes one point from a vector spline (`hit` identifies.
- `findNearestSpline(layer, x, y)` Spline whose path (segments, not just points) is nearest (x,y); used by Move Line (vmove).
- `findNearestVectorEndpoint(layer, x, y)` Like `findNearestVectorPoint` but restricted to just each spline's two true *endpoints*.
- `findNearestVectorPoint(layer, x, y)` Searches every point of every spline on a vector layer for whichever is closest to a given.
- `gradientStopsBarPositionFromClientX(clientX)` Client x over the stop bar -> 0-1 position.
- `handleGradientStopsBarPointerDown(e)` Bar press: delete in Delete Points mode, grab an existing marker, else insert.
- `handleGradientStopsBarPointerMove(e)` Drags the grabbed bar marker.
- `handleGradientStopsBarPointerUp(e)` Ends a bar drag; one undo entry if changed.
- `hitTestGradientLinePosition(sp, x, y)` Projects a tap onto a gradient backbone; 0-1 or null.
- `hitTestGradientStop(sp, x, y)` Index of the stop near a canvas point on the backbone (44pt-style radius), or -1.
- `hitTestGradientStopsBarMarker(sp, clientX)` Index of the stop marker near a client x on the bar, or -1.
- `insertGradientStop(position)` Adds a stop at position 0-1 (colour per the new-stop source); one `replaceSplines` undo entry.
- `interpolateHexColor(a, b, t)` Linear blend of two #rrggbb colours at t.
- `renderGradientStopColorSourcePicker()` Syncs the new-stop colour source buttons.
- `renderGradientStopsBar()` Shows/redraws the gradient stop bar (`#gradientStopsBar`) with markers.
- `saveGradientNewStopColorSource()` Persists to `pixelAppGradientNewStopColorSource`.
- `setGradientNewStopColorSource(v)` Sets new-stop colour source ('selected' | 'interpolate'), persists, syncs picker.
- `toggleGradientAddStopMode()` Toggles the Add Stop sub-mode (exclusive with Delete Points / Extend Line).
- `updateGradientBackboneOverlay()` Draws gradient backbone lines and stop markers into `#gradientBackboneOverlay`.

## ZIP/XML Codec

- `buildAnimDataXml()` Serializes the in-memory sprite-animation project back into `AnimData.xml` text.
- `async deflateRaw(bytes)` DEFLATE compress via native CompressionStream.
- `async inflateRaw(bytes)` DEFLATE decompress via native DecompressionStream.
- `parseAnimDataXml(xmlText)` Parses `AnimData.xml` via the browser's native `DOMParser`.
- `async readZip(arrayBuffer)` Parses a zip central directory -> {name: Uint8Array}; handles STORE and DEFLATE. Throws on invalid zips.
- `async writeZip(entries)` Builds a DEFLATE zip from {name: Uint8Array}, entries in insertion order.

## Reference layers and thumbnails (V2_4)
- `ReferenceLayer.drawSource()` Copies the image into its canvas once at native size (capped at `REFERENCE_MAX_DIM`).
- `ReferenceLayer.isPixelated()` Applies `sampling` (auto/pixel/smooth) for the current zoom; `layoutCSS` sets `image-rendering` from it.
- `ReferenceLayer.setActualSize()` 1 image px = 1 cell, whole-cell centred position, rotation 0.
- `ReferenceLayer.drawInto(ctx, smoothing)` Draws it with its transform into a grid-sized context (gallery thumbnail, eyedropper composite).
- `ReferenceLayer.sampleAt(x, y)` Exact [r,g,b,a] under a grid cell, undoing rotation/flip; null outside.
- `drawImageFitted(ctx, src, sw, sh, dx, dy, dw, dh)` Aspect-fit draw: halving downscale with high-quality smoothing, nearest-neighbour when enlarging.
- `makeThumbnail(layer, cssSize)` Layer thumbnail at cssSize x DPR over a checker.

## Mapart colour methods and eyedropper sampling (V2_5)
- `setMapartColourMethod(id)` / `toggleMapartSnapToasts()` / `syncMapartPrefsUI()` App-wide prefs; method change clears the snap caches.
- `mapartMetric(r, g, b)` A colour in the chosen method's space; `mapartSnapRGB` compares palette values from it.
- `colourLab(r, g, b, d50)` sRGB to CIE L*a*b* (D65 or D50). `colourDeltaE2000(p, q)` CIEDE2000.
- `colourHctPoint(r, g, b)` [L*, a', b'] (CAM16-UCS M' at hue h) for HCT distance; `colourHct` gives Material hue/chroma/tone.
- `mapartColourName(hex)` "normal White Wool"-style name for toasts.
- `setEyedropSampleSize(n)` / `renderEyedropSampleRow()` Sample size pref and its button row. `averageCanvasColour(canvas, x, y, n)` Alpha-weighted N x N average or null.

## Transform screen (V2_6)
- `xfLiveComposite()` Live preview frame (real compositing). `xfComposeResult(s)` / `xfSnappedState(st)` Result pixels shared by preview and Done. `xfSourceFor(l)` Preview override hook.
- `zoomAtClientPoint(clientX, clientY, dir)` One wheel zoom step keeping the canvas point under the mouse fixed.
- `xfOpen()` Lifts the active layer's pixels (or selected pixels) and opens `#xfScreen`; false + toast if nothing to transform.
- `xfDone()` / `xfCancel()` / `xfClose()` Apply (one `layerTransform` undo step) / discard / hide.
- `xfResample(st, src, sw, sh, interp, mask)` Inverse-mapped nearest/bilinear/bicubic into a canvas-sized RGBA buffer (+ transformed selection mask).
- `xfNudge(dx, dy)` / `xfStepSize(sign)` / `xfStepRotate(sign)` / `xfFlip(axis)` / `xfReset()` Step edits.
- `xfFieldChanged(id)` Typed X/Y/W/H/degree and step boxes. `xfSyncUI()` / `xfSyncFields()` Refresh the bar.
- `xfPointerDown/Move/Up`, `xfWheel` Handles, move, rotate, pinch (piece or view), Space pan, zoom. `xfFocusView()` Zooms in on small pieces.
- `xfBoxPoint(st, sx, sy)` / `xfToLocal(st, gx, gy)` Box geometry. `xfLayerRGBA(layer)` RGBA of a pixel-like layer.
- `buildTransformOpenRow()` Layer settings TRANSFORM (SELECTION) button.

## Thumbnail privacy (V2_5)
- `openThumbPrivacySheet(id, onReady)` Builds the stored project's frames and opens the per-layer/group thumbnail opacity sheet.
- `renderThumbPrivacyList()` / `updateThumbPrivacyPreview()` / `resetThumbPrivacySheet()` Sheet rows (frame 1, top first, no mask/clip rows), live preview, reset to 100%.
- `closeThumbPrivacySheet()` Writes `thumbOpacity` back into the save data (by layer index / tree position), syncs the open project if it's the same one, stores the new card image.
- `thumbnailFromBuiltFrames(built, data)` Card image from built frames at the project's own size.
- `projectHasThumbOpacity(frames)` Any layer/group below 100% (drives the reminder toast).

## Background fill (V2_3)
- `setBackgroundColor(c, record)` Sets `backgroundColor` (Mapart-validated), optional undo step, ends pick mode, refreshes fill and UI.
- `updateBackgroundFill()` Shows/sizes `#backgroundFill` as `#container`'s first child.
- `updateBackgroundUI()` Syncs `#bgSwatchColours`, `#layersBgSwatch`, pick button/hint, NONE visibility.
- `toggleBackgroundPickMode()` / `exitBackgroundPickMode()` Pick-from-swatches mode; exit reopens `backgroundPickReturnPanel` if set.
- `openBackgroundPickerFromLayers()` Opens Colours in pick mode, returns to Layers after the pick.
- `resetBackgroundForNewProject()` Mapart default or none.
- `mapartValidBackground(c)` Allowed map colour for `c` (default if null).

## Mapart (V2_2)
- `syncMapartPalette(force)` Enters/leaves the locked map palette (stash and restore the previous one); `force` rebuilds after a staircase change.
- `updateMapartPaletteUI()` Shows the staircase row, hint and live off-shade count; hides picker-related rows.
- `mapartAllowedHexes()` The 61 or 183 allowed hexes (cached with their Lab values). `mapartResetPaletteCache()` clears that and `mapartSnapCache`.
- `mapartLab(r,g,b)` mapartcraft's default colour space. `mapartSnapRGB(r,g,b)` nearest allowed colour, cached. `mapartSnapColor(c)` any stored colour -> allowed hex or null.
- `mapartSnapLayerInPlace(layer)` Snaps a whole PixelLayer (materialises lazy image layers first); no history.
- `mapartCountOffShade()` / `mapartConvertToFlat()` Count / convert light and dark shades on every pixel layer; the convert pushes one `pixelsMulti` entry.
- `toggleMapartStaircase()` / `resolveMapartStaircaseOff(choice)` The toggle and the convert / keep / cancel choice.
- `mapartDimensionsCompatible(w,h)`, `mapartClampToMaps(px)` Whole-map size rules. `profileToolFallback()` Portrait or Mapart tool redirects.
