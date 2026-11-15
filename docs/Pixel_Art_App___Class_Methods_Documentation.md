# Pixel Art App --- Class Methods Documentation

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`). Methods of every class, in source order. Top-level functions are in the Functions Documentation parts.

## `Canvas2DImageRenderer`

Only ImageLayer renderer (WebGL2 was removed). Instantiated only by createImageRenderer().

- `constructor(layer)` Stores a reference back to the owning layer, grabs the layer's own canvas element (`layer.el`).
- `resize(w, h)` Sets the canvas element's own `width`/`height` attributes directly.
- `render(imageData)` Resizes first if the incoming `imageData`'s dimensions don't match the canvas's current size.
- `renderFromCanvas(source)` Clears the canvas and draws an arbitrary canvas-like source onto it via `drawImage`.
- `destroy()` An empty no-op.

## `ImageLayer`

Large-canvas raster layer (either side > 999px), backed by a flat Uint8ClampedArray (`imageData`). Does NOT extend Layer: it re-implements the layer contract by hand, so any method generic code calls on layers must be added here too (V1_44_1 added applyVisualState/blendMode after addPixelLayer crashed without them). Ids are random strings, not the shared integer counter. `pixelData` is a Proxy shim over imageData for PixelLayer API compatibility; `window.ImageLayer = ImageLayer` is required (class declarations do not attach to window).

- `constructor(name, width, height)` Builds two separate canvases: `this.el` and `this.cpuCanvas` -- kept deliberately separate, per an in-code comment.
- `_offset(x, y)` Converts grid coordinates to a byte offset into the flat `imageData.data` array (`(y * width + x) << 2`.
- `getPixel(x, y)` Returns `null` for out-of-bounds or fully-transparent pixels.
- `setPixel(x, y, color)` Out-of-bounds writes are silently ignored.
- `captureHistoryTile(x,y)` No-ops unless a tile-mode capture is active.
- `captureHistoryFull()` The whole-buffer counterpart to tile capture: no-ops unless a full-mode capture is active.
- `setPixelData(data)` Writes a grid into imageData (clamped to the overlap), capturing history in full mode. Never replaces the pixelData shim (doing so used to detach the layer from its canvas; fixed V1_45).
- `plot(x, y, color)` setPixel then redrawFromData.
- `redrawFromData()` Immediate re-render via invalidateRenderer; inside bulkPixelWrite it only marks the layer dirty.
- `redraw()` A bare alias for `redrawFromData()`.
- `loadFromImage(img)` Draws an `<img>` directly onto `cpuCanvas` at native `gridW`x`gridH`.
- `getImageData()` A plain getter returning `this.imageData` as-is.
- `setImageData(imageData)` Validates the incoming buffer's dimensions match exactly before accepting it (returns `false`.
- `clear()` Zeroes imageData in place; full-mode history capture first. The path CLEAR and the broom use for ImageLayer.
- `resizeToCanvas(newW, newH)` Resizes by drawing the *old* `cpuCanvas` content onto a scratch canvas at the old size (with `imageSmoothingEnabled =`.
- `flipHorizontal()` Captures a full "before" snapshot if capturing.
- `flipVertical()` The same structure as `flipHorizontal()`, mirroring vertically instead.
- `layoutCSS()` Sets the visible element's CSS width/height from `gridW`/`gridH` times the current zoom `scale`.
- `applyVisualState()` Deliberate copy of Layer.applyVisualState: display from visible and group visibility, opacity times group opacity, mix-blend-mode via cssBlendMode.
- `clone()` New ImageLayer with copied bytes, visible, opacity, color, blendMode.

## `Layer`

Base for PixelLayer, VectorLayer, ReferenceLayer (Mask/Clip via PixelLayer).

- `constructor(type, name)` Assigns a sequential integer id from the shared `nextLayerId` counter (the "normal" id space every non-`ImageLayer`.
- `applyVisualState()` Mask/clip always hidden (composited, not shown); others: display from visible and group visibility, opacity times group opacity, mix-blend-mode.

## `PixelLayer` extends `Layer`

Raster layer for Portrait, Sprite and Pixel Art up to 999px per side. Proxy-tracked array-of-arrays `pixelData` drives undo capture (Option B, dropping the Proxy, is decided but not implemented).

- `constructor(name, w, h)` Calls `super('pixel', name)`, builds the tracked pixel-data Proxy via `makeTrackedPixelData(this, w`.
- `plot(x, y, color)` The choke point for every pixel write: bounds check, Portrait isolation check, lazy image-to-pixel materialise, tracked write, then a 1x1 canvas paint (skipped inside bulkPixelWrite, which redraws once).
- `redrawFromData()` Immediate re-render via invalidateRenderer; inside bulkPixelWrite it only marks the layer dirty.
- `setImageRenderSource(img)` Switches this layer into lazy "image" render mode: stores the source image.
- `switchToPixelRender()` The inverse: clears `renderMode`/`imageSource` back to normal pixel-array mode and redraws.
- `setPixelData(data)` Replaces pixelData wholesale, first capturing every outgoing cell into `_historyCapture.before` (a bulk reassignment bypasses the Proxy). Reads size from the incoming data.
- `resizeToCanvas(newW, newH)` Builds a fresh `newW`x`newH` all-`null` grid, copies over just the overlapping region from the current data (top-left.
- `flipHorizontal()` Builds a fresh mirrored grid by copying each column to its horizontally-reflected position.
- `flipVertical()` The same structure as `flipHorizontal()`, mirroring rows top-to-bottom instead.
- `layoutCSS()` Identical in shape to `ImageLayer.layoutCSS()`: sets CSS width/height from grid dimensions times zoom `scale`.
- `loadFromImage(img)` Forces `renderMode` back to `'pixel'` and clears any `imageSource`.

## `MaskLayer` extends `PixelLayer`

Extends PixelLayer; type `mask`, `hookedTo` = target layer id (must sit directly above its target). Compositing lives in compositeMaskOrClip().

- `constructor(name, w, h)` Calls `super(name, w, h)` (the full `PixelLayer` constructor, including building a real tracked pixel-data Proxy.

## `ClipLayer` extends `PixelLayer`

Extends PixelLayer; type `clip`, stencils through the opaque pixels of the layer below. Same shape as MaskLayer.

- `constructor(name, w, h)` Same as `MaskLayer`'s constructor, except sets `this.type = 'clip'`.

## `ReferenceLayer` extends `Layer`

Guide-only placed image (excluded from flatten/export; eyedropper only). Stores the source image plus a transform (gx, gy, gw, gh in float grid units, rotation, flipH/V) and re-renders from the source every layout, so scaling is lossless.

- `constructor(name, img)` Calls `super('reference', name)`, adds the `reference-canvas` CSS class, stores the source `<img>`.
- `layoutCSS()` Positions and sizes the visible element in CSS pixels from `gx`/`gy`/`gw`/`gh` times zoom `scale`.

## `VectorLayer` extends `Layer`

Stores `splines` ({closed, filled, color, width, points, stops}); the canvas is only a render target. `stops` non-null = gradient spline.

- `constructor(name)` Calls `super('vector', name)`, initializes an empty `splines` array and `draftPreview = null`.
- `layoutCSS()` Branches entirely on the Debug drawer's `debugUnrestrictedVector` toggle.
- `renderUnrestricted()` The debug-only smooth-curve renderer: for each spline, a single point renders as a filled circle.
- `render()` The normal render entry point: clears the canvas.
- `renderGradientFill(sp)` Fills the whole canvas with a linear gradient between the first and last points using the sorted stops (needs 2+ points and 2+ stops). Linear only; radial would be a separate path.
- `rasterizeThresholded(drawFn)` The shared anti-aliasing-defeat mechanism both fill and thick-stroke rendering paths route through.
- `renderSpline(sp, isDraft)` A single point renders as a filled circle, matching `renderUnrestricted()`'s equivalent case.
- `renderSplineBresenham(sp)` The true single-pixel-staircase rasterizer for width-1 committed strokes.

## Rules

- A method that replaces `pixelData` wholesale needs an explicit before-capture (PixelLayer.setPixelData shows the pattern); the Proxy only sees writes through it.
- Adding a method that generic layer code calls? Add it to ImageLayer too; it does not inherit from Layer.
- Keep ReferenceLayer's 4096px / 2x-source buffer cap: past mobile canvas limits the canvas silently stops rendering.
- Keep VectorLayer's width-1 Bresenham path separate from the thresholded path (diagonal staircase consistency).
