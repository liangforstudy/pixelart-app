# Pixel Art App --- Functions Documentation Part 1

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`). 486 top-level functions total across Part 1 and Part 2; class methods are in `Pixel_Art_App___Class_Methods_Documentation.md`. Part 1: Camera / Zoom / Pan to Layers & Layer Tree. Part 2: Mask/Clip Layer to ZIP/XML Codec. One line per function: signature, then what it does. Alphabetical within each category. Source is ground truth.


## Camera / Zoom / Pan

- `applyCameraTransform()` Writes translate(pan) rotate(cameraRotation) scale(cameraScale) to the container (origin centre).
- `applyPanelVisibility()` Shows/hides each bottom-bar panel tab (`#tab-<name>`) based on the corresponding boolean.
- `checkerSquareScreenPx()` Canvas checker square in screen px: 8 canvas px, floored at 4 screen px below 0.5x zoom.
- `clampPanScrollWithinEdgeMargin(value, maxScroll)` Clamps a scroll value so at least `MIN_CANVAS_PEEK` pixels of the canvas always remain visible.
- `closePanel()` Closes whichever floating panel is open: removes `.open` from every `.floating-panel`.
- `computeFitToScreenZoomIndex(w, h)` Computes which `ZOOM_STEPS` index best fits a canvas of the given dimensions into the current.
- `openPanel(name)` Opens a named floating panel: cancels any in-progress clear-confirmation first.
- `reanchorCameraPanAfterZoomSnap(gesture)` After a pinch snaps `scale`, re-solves cameraPanX/Y from the gesture's anchor so the point under the fingers stays put.
- `renderFramesPanel()` Rebuilds the flipbook Frames strip UI from scratch: one button per frame.
- `renderPanelManager()` Rebuilds the panel-visibility management list: one row per panel definition with a label.
- `resetCameraPanZoom()` Resets camera pan and scale, not rotation (zoom buttons use it).
- `savePanelVisibility()` Serializes the `panelVisibility` object to `localStorage` under `pixelAppPanelVisibility`.
- `setAllPanelTabsVisible(visible)` Bulk sets every non-fixed panel tab's visibility flag to the given value, persists the change.
- `setPanelTabVisible(name, visible)` Sets one panel's visibility flag, persists it, syncs its tab's DOM visibility.
- `togglePanel(name)` Opens a panel if it's not the currently-open one (logging via `traceLog`).
- `updateZoomLabel()` Writes the current zoom level into `#zoomLabel`.
- `zoomIn()` Next ZOOM_STEP; resets camera pan/scale (keeps rotation); re-layouts.
- `zoomOut()` Previous ZOOM_STEP; resets camera pan/scale (keeps rotation); re-layouts.

## Canvas Resize

- `applyCanvasResize(newW,newH,ax=.5,ay=.5)` Performs an actual canvas resize: clamps both dimensions to 1-2000. Since V2_1 a thin wrapper that turns the anchor into an offset and calls `applyCanvasResizeOffset`.
- `applyCanvasResizeOffset(newW,newH,offX,offY)` (V2_1) The real resize: the old drawing's top-left lands at (offX, offY); negative offsets crop top/left. Same size with a shift is allowed. One `canvasResize` undo entry.
- `openResizeFor(kind,returnTo)` (V2_1) Every Resize button goes through this: kind `auto`/`screen`/`sheet`, returnTo `gallery`/`editor`. Portrait/Sprite always get the sheet.
- `enterResizeScreen(returnTo)` / `exitResizeScreen()` / `rsConfirm()` / `rsDiscard()` (V2_1) Resize screen lifecycle. `rsConfirm` uses `elementTapTwiceConfirm` when `rsCroppedPixelCount()` > 0; from the gallery it calls `goToMainMenu()` to save.
- `rsApplyHandleDrag`, `rsApplyDrawDrag`, `rsSnapSize` (V2_1) Rectangle maths: whole pixels, 1-2000 per side, lock ratio, snap to `RS_COMMON_SIZES`.
- `closeResizeCanvasSheet(returnToGallery)` Closes the resize modal.
- `openResizeCanvasSheet(returnToGalleryOnCancel)` Opens the resize modal, seeding it with the current dimensions.
- `restoreCanvasResizeState(state)` The inverse of `applyCanvasResize`, used by undo/redo: restores grid dimensions.
- `setResizeDimension(which,v)` Writes a clamped (1-2000) width/height into the resize modal's dataset and its input.
- `snapshotCanvasResizeState()` Captures a full, independent copy of every frame's every layer's raw pixel data (deep-copied.

## Colour / Palette

- `applyAllCheckerProfiles()` Applies every screen's saved checker profile (canvas, PMD preview, gallery cards, sliders).
- `applyCheckerProfile(els, profileKey, screenKey)` Applies a checker profile's colours as CSS custom properties on element(s).
- `applyImportedSwatchArray(raw)` Parses and applies a JSON swatch-array import: accepts either a plain array.
- `cleanSwatchList(arr)` Sanitizes an arbitrary array down to a valid, de-duplicated swatch list.
- `closeSwatchArrayMenu()` Removes the swatch-array context menu element and its backdrop from the DOM entirely.
- `converterRgbToHSV(r, g, b)` r,g,b 0-255 -> {h 0-360, s 0-100, v 0-100}.
- `async copySwatchHexToClipboard()` Copies the swatch hex; temporary button-label feedback.
- `countCustomSwatches()` Counts real user swatches in the palette DOM, explicitly excluding the transparency swatch.
- `createSwatch(color)` Adds (or re-selects) a swatch; enforces the 15-colour cap for Portrait tiles and sprite palette editing.
- `exitSwatchEditMode()` Leaves swatch edit mode and hides its backdrop (also called by closePanel).
- `exportSwatchArray()` Exports the current palette as a downloadable JSON file: in Portrait mode.
- `getSwatchArray()` Reads the currently-displayed palette swatches back out of the DOM into a plain array.
- `handleSwatchClick(c, isT = false)` The palette swatch tap handler: sets the selected colour (or `null` for the transparency.
- `importSwatchArrayFile()` Resets the hidden swatch-array file input's value (so re-picking the same file still fires.
- `openGlobalCommandPalette()` Opens the command palette (lazy-built, z-index 3000), focuses its input, shows top commands.
- `openSwatchArrayMenu()` Builds and shows a small centered popup menu for the swatch-array feature.
- `parseHexToRgbBytes(hex)` #RRGGBB -> [r,g,b] or null.
- `parseStoredColor(c)` Parses a stored colour value (which could be `null`/transparent, a `#RRGGBB` hex string.
- `performColorToAlpha(x,y)` The actual Colour-to-Alpha execution once a target pixel is tapped.
- `renderCheckerProfilePicker()` Builds the Customisation panel checker picker (one row per screen).
- `replaceVisiblePalette(colours)` The shared function behind loading a Portrait tile's palette.
- `saveCheckerSettings()` Persists checkerboard settings to `pixelAppSettingsCheckBoard`.
- `setCheckerCustomColor(screenKey, slot, hex)` Sets colour a/b of a screen's custom checker pair; applies live.
- `setCheckerProfile(screen, profileKey)` Sets one screen's checker profile, persists, re-applies.
- `setupPaletteDragEvents()` Wires the palette's swatch drag-to-reorder gesture globally (on `window`.
- `updateColorPickerAvailability()` Disables the colour picker and dims its wrapper once the current palette (Portrait tile.
- `updateColorToAlphaTargetLabel()` Updates the Colour-to-Alpha tool's status label to show either the currently-sampled target.
- `updateSwatchValueDisplay()` Refreshes the hex/RGBA/HSV+A strip for selectedColor (called from updateUI).

## Colour Tools

- `colorToAlphaPixel(c,target)` The actual per-pixel Colour-to-Alpha math: parses both the candidate pixel.

## Cursor

- `hideCursor()` Clears the pending cursor-hide timer and removes the `.visible` class from the pixel cursor.

## Debug System

- `applyDebugDrawerSplit()` Applies the saved controls/log split height to the Debug drawer.
- `clearDebugLog()` Empties `debugLogEntries` in place (`.length = 0`) and re-renders the Debug drawer's log view.
- `async exportLogToClipboard()` Copies the Debug log to the clipboard; temporary button feedback.
- `pushDebugLog(kind, args, category)` The actual writer behind all Debug-drawer logging.
- `refreshDebugStats()` Rebuilds the Debug stats readout (incl. saved-project count and storage usage) and syncs its sliders.
- `renderDebugLog()` Rebuilds the Debug drawer's log view from `debugLogEntries`.
- `setRasterToolGateThresholdPx(px)` Sets and persists the raster-gate area threshold (clamped).
- `setupDebugDrawerSplitHandle()` Wires the drag handle that resizes the Debug drawer split (persisted to `pixelAppDebugDrawerSplitPct`).
- `toggleDebugUnrestrictedVector()` Flips the `debugUnrestrictedVector` flag, persists it, syncs the toggle button.
- `toggleForceEnableRasterTools()` Toggles and persists the raster-gate override.

## Frames

- `addFrame(duplicate)` Adds a new flipbook frame, either as a fresh single-`PixelLayer` frame or (if `duplicate`).
- `deleteFrame(idx)` Removes a frame by index, tears down its layers' DOM elements first.
- `renderSpriteAnimFrame()` The PMD editor's actual preview-canvas renderer: shows an empty-state hint.
- `renderSpriteAnimFrameList()` The full rebuild of the PMD editor's frame list: clears.
- `setupSpriteAnimFrameDataFieldListeners()` Wires all five of the PMD editor's per-frame metadata fields to their respective update paths.
- `switchFrame(idx, preserveSelection=false)` Switches the active flipbook frame: tears down the current frame's layer DOM elements.
- `updateSpriteAnimFrameDataFields()` Syncs the PMD editor's Frame/Duration/Flip/Offset-X/Offset-Y fields to the current frame.
- `updateSpriteAnimFrameReadout()` Writes the "current / total" frame-count text for the PMD sprite editor.

## Gallery / Hub

- `beginGalleryRename(e)` Context-menu Rename: opens the native rename modal for the target project.
- `closeGalleryCtxMenu()` Closes the gallery's project context menu (removes `.open` from both the menu.
- `hideGallery()` Hides the gallery screen element via `display: none`.
- `openGalleryCtxMenu(id, e)` Opens the gallery's per-project context menu for a given project id.
- `renderGallery()` Rebuilds the gallery: status line, New Canvas card, one card per project (lazy thumbnails, long-press menu, tap to open).
- `showGallery()` Shows the gallery screen and hides both the init/splash screen and the pixel-canvas screen.
- `startNewProjectFromGallery(w, h)` Creates and opens a brand new project at the given dimensions directly from the gallery (as.

## History / Undo-Redo

- `applyHistoryEntry(entry, forward)` The single dispatcher that both `undo()` and `redo()` funnel through.
- `cloneLayerForHistory(layer)` Clones a layer for storage in a history entry.
- `commitEditAndSelection(pending, beforeSelSnap, afterSelSnap)` commitEdit pixel diff plus selection before/after in one `selectionTransform` undo entry.
- `detachHistoryNode(node)` Removes a node from the history tree's parent-child linkage (unlinks it from its parent's.
- `discardRedoHistory()` Clears the entire redo stack: for each discarded entry.
- `estimateHistoryEntryBytes(entry)` Computes the memory-budget byte estimate for one history entry.
- `historyEntryLabel(entry, index)` Builds the human-readable label shown in the Undo History panel for one entry.
- `jumpToHistoryNode(target)` Moves the history cursor to an arbitrary tree node, not just one step forward/back.
- `pruneHistoryLimit()` Evicts the oldest undo entries (from the front of `undoStack`) while either the action-count.
- `redo(nodeOverride)` The counterpart to `undo()`: pops the most recent entry off `redoStack` (or.
- `renderUndoHistory()` Rebuilds the Undo History panel's list: a status line showing current memory usage vs. budget.
- `resetHistory()` Fully resets the undo/redo system: empties both stacks, zeroes the memory counter.
- `setHistoryMemoryBudgetMiB(mb)` The Debug drawer slider's handler: clamps the requested MiB value to the allowed range.
- `undo()` Pops the most recent entry off `undoStack`, applies its "before" state.

## Import / Export

- `async copyToClipboard()` Copies the flattened canvas PNG to the clipboard (long-press on Export PNG).
- `exportSpritesheet()` Flattens every frame into one wide horizontal strip canvas.
- `handleImportImageClick()` The Hub's Import Image button handler: if no project is currently open (`frames.length ===`.
- `openImportSheet()` Builds the "Import Image" sheet: a short usage hint.
- `setupImportImageInput()` Wires the hub's shared image-file input's `change` handler.
- `triggerSpriteAnimImport()` Programmatically clicks the hidden PMD sprite-package file `<input>`.

## Layers & Layer Tree

- `activeLayer()` Resolves the currently-active layer object: prefers looking it up by `activeLayerId` if set.
- `activeLayerHasLiveHook()` Returns whether the currently-active layer has a mask/clip layer "hooked" onto it directly.
- `addClipLayer()` Adds a new clip layer via the shared `addHookedLayer('clip')` path.
- `addEmptyGroup()` New empty group at the active insertion point, made active; undoable (`Add group`).
- `addHookedLayer(kind)` Adds a new mask or clip layer, hooked onto the currently active layer.
- `addLayer(layer)` The low-level layer-insertion primitive nearly every "add X layer" function calls.
- `addMaskLayer()` Adds a new mask layer via the shared `addHookedLayer('mask')` path.
- `addPixelLayer()` The "Add Layer" button's actual handler: chooses `ImageLayer` vs `PixelLayer` using the same.
- `applyGroupBlendMode(group)` Ensures a group has a `blendMode` value (defaulting to `'source-over'`/Normal).
- `applyGroupVisualState(group)` Recursively propagates a group's visibility/opacity down through its entire subtree.
- `beginTreeDrag(node,row,event)` The low-level pointer-driven drag-and-drop implementation for reordering layer/group rows.
- `canDropNodes(nodes,target,mode)` Returns whether a drag-drop of `nodes` onto `target` is legal: false if there's no target.
- `captureTreeState()` Deep-clones the active frame's entire layer tree (recursively, preserving group metadata.
- `clearLayerAt(i)` Per-row broom: vector layers empty their splines (`clearVectorLayer` undo); pixel-like layers clear via clearLayerContent.
- `clearLayerContent(layer)` Clears one layer to transparent: the layer's own clear if it has one, else a null grid via setPixelData.
- `clearLayerTreeSelection()` Empties the `selectedNodeIds` set, does not re-render.
- `clearTreeSelection()` Calls `clearLayerTreeSelection()` and re-renders the layers panel.
- `cloneLayer(l)` The general-purpose layer duplicator, branching by type.
- `collectNodeIds(node, out)` Recursively collects a node's own id and every descendant's id into a flat array.
- `collectTreeNodes(nodes,out)` Recursively flattens an entire layer tree into a flat array of every node, depth-first.
- `createBaseRasterLayer(name, w, h)` The canonical layer-class selector: Portrait and Sprite profiles always get `PixelLayer`.
- `createGroupFromSelected()` Wraps either the current multi-selection or, if nothing is multi-selected.
- `cssBlendMode(blendMode)` Maps stored 'source-over' to CSS 'normal'; other modes pass through.
- `cycleGroupColor(groupId)` Cycles a group's colour tag through a fixed 10-entry palette (including `null` for "no.
- `cycleLayerColor(layerId)` Same cycling pattern as `cycleGroupColor`, applied to an individual layer's colour tag instead.
- `deleteGroup(node,btn)` Deletes a group node: if the group has children.
- `deleteLayer(i, btn)` Deletes a layer by index: removes it from the tree and DOM, and if it was the active layer.
- `duplicateTreeWithRemap(node,map)` Recursively duplicates a subtree, appending " copy" to names.
- `ensureFrameLayerTree(frame)` Lazily builds a frame's `layerTree` from its legacy flat `layers` array if the tree doesn't.
- `findGroupNode(nodes, groupId, parent)` Thin alias for `findNode(nodes, groupId, parent)`.
- `findLayerById(frameIndex,layerId)` Looks up a layer object by id within a specific frame's flattened `layers` array.
- `findLayerNode(nodes, layerId, parent)` Alias for `findNode(nodes, 'layer-' + layerId, parent)`.
- `findNode(nodes, id, parent)` The core recursive tree-search function nearly every other tree-lookup helper.
- `flattenGroupSubtreeToCanvas(groupNode, gW, gH)` Wrapper: flattenTreeToCanvas over a group's children.
- `flattenLayersToCanvas(layerTree)` Wrapper: flattenTreeToCanvas for a layer tree at canvas size (PNG export, spritesheet).
- `flattenLayerTree(nodes, out)` Recursively flattens a layer tree into the flat `layers`-array shape.
- `flattenTreeToCanvas(nodes, gW, gH, smoothing)` The tree-aware compositor behind every flatten: nesting, group opacity/blend, per-layer blend, mask/clip; reference layers excluded (guide-only).
- `flipActiveLayerH()` Flips the active layer horizontally, branching on *capability* rather than *type*.
- `flipActiveLayerV()` The vertical counterpart to `flipActiveLayerH()`, identical structure and reasoning.
- `focusLayerSearch()` Expands layer search and focuses its input (native keyboard).
- `galleryFlattenLayers(layerTree, gW, gH)` Wrapper: flattenTreeToCanvas with smoothing for thumbnails and gallery export.
- `getActiveParentGroup()` Resolves whichever group node new layers/groups should currently be inserted.
- `getNodeById(id)` Looks up a tree node by id within the active frame's `layerTree`, returning `null` if not found.
- `getNodePathText(node)` Builds the human-readable "Group / Subgroup / Layer Name" breadcrumb string for a node.
- `getNodeStack(nodes, targetId, path)` Recursively finds a target node and returns the full ancestor chain leading to it.
- `getOrCreateGroupBlendWrapper(groupId, blendMode)` Returns a group's wrapper div (isolation:isolate + mix-blend-mode), creating it once; reindexDom repositions it every call.
- `getRootSelectedNodes()` Walks the active frame's tree and collects every *topmost* selected node.
- `groupBlendWrapperId(groupId)` DOM id of a group's blend wrapper.
- `importImageAsNewLayer(img, file, importBtn)` The "add an imported image onto the currently-open canvas as a new pixel layer" path.
- `insertNodeForActive(node)` Inserts a new tree node at the correct position relative to whatever's currently active.
- `isNodeInside(node,possibleAncestor)` Returns whether `node` is a descendant of `possibleAncestor`.
- `isNodeSelected(node)` Returns whether a tree node's id is present in the `selectedNodeIds` multi-select set.
- `jumpToTreeNode(node)` Navigates the Layers panel to a specific node.
- `makeGroupNode(name)` Constructs a fresh group-node object with default visibility/opacity/blend-mode.
- `makeLayerNode(layer)` Wraps a raw `Layer` object into a tree node shape (`{kind:'layer', id:'layer-N', layer}`).
- `mergeSelectedGroups()` Merges 2+ selected groups into one new "Merged Group".
- `mkLayerIconBtn(text, onClick)` Factory for a small icon-style button used in layer-row UI; sets class, text.
- `nodeId(node)` Returns a tree node's canonical id string -- `'layer-' + layer.id` for layer nodes.
- `openPixelLayerImport()` Sets `pendingImportKind = 'pixel-layer'` and clicks the hub's hidden image-input element.
- `parentOfNode(node)` Returns a tree node's parent node by searching the active frame's `layerTree`.
- `performTreeDrop(nodes,target,mode)` Executes a drag-and-drop reorder once validated (`canDropNodes`).
- `pixelLayerFromImage(name, img, w, h)` Converts an `<img>` into a new layer sized exactly `w × h`.
- `pixelLayerFromImagePreserveCanvas(name, img)` The "import onto existing canvas" variant of the above (used by `importImageAsNewLayer`).
- `pruneStaleGroupBlendWrappers(activeGroupIds)` Removes wrappers whose group is gone or back to Normal.
- `pushTreeOperation(label,before)` Captures the current tree state as `after`, and pushes a `{type:'tree', label, before`.
- `readDigitGroup(id)` Reads a 4-digit numeric input group (four `<select>` elements sharing a container id) back.
- `removeNodeFromTree(node)` Finds a node's location in the active frame's tree (via `findNode`).
- `renderLayerFromDocumentState(layer)` The actual "redraw this layer's on-screen canvas from its authoritative data" function.
- `renderLayerSearchResults(query)` See the main documentation's Search Engine / Command Palette entry (this is the layer-only.
- `renderLayersPanel()` The single largest UI-construction function tied to the Layers panel.
- `renderRawPixelLayer(layer)` Renders a `PixelLayer`'s raw `pixelData` array directly onto a freshly created canvas.
- `reorderLayerTreeNode(node, direction)` Moves a node up or down one position among its siblings (`direction` is `+1`/`-1`).
- `resizeImageLayerAnchored(layer,newW,newH,dx,dy)` Resizes an `ImageLayer` in place, anchored per the given offset (`dx`/`dy`.
- `resizePixelLayerAnchored(layer,newW,newH,dx,dy)` The `PixelLayer` equivalent of the above: builds a fresh array-of-arrays of the new size.
- `restoreTreeState(state)` The inverse of `captureTreeState()`, used by undo/redo for tree-type entries.
- `selectAllTreeNodes()` Clears the current multi-select, then selects every top-level node in the active frame's tree.
- `selectTreeNode(node, on=true)` Adds or removes a node from the multi-select set -- but with two guard conditions.
- `serializeLayer(l)` Converts one live layer object into a plain, JSON-serializable shape for project save.
- `serializeLayerTree(nodes, frameLayers)` Recursively serializes an entire layer tree into a plain structure for save.
- `setActiveLayer(idx)` The canonical "make this layer active" function.
- `setDigitGroup(id, val)` The inverse of `readDigitGroup`: writes an integer into a 4-digit `<select>` group.
- `setupLayerFileInputs()` Wires the two remaining file inputs not covered by `setupImportImageInput`.
- `syncActiveLayersFromTree()` Re-derives the flat `f.layers`/`layers` alias from the authoritative `layerTree` (via.
- `toggleLayerSearch()` Expands/collapses layer search; collapsing clears the query and results.
- `toggleLayerSelectionMode()` Flips multi-select mode for the layers panel on/off.
- `toggleLayerThumbSize()` Flips between small/large layer thumbnails, syncs the toggle button's active state.
- `ungroupSelected()` Dissolves every selected group (root-level selections only.
