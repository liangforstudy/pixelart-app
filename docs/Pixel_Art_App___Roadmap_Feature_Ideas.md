# Pixel Art App --- Roadmap / Feature Ideas

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`).

New capability only (defects go in the Fix List). Nothing here is scheduled until agreed. Plan in sessions before building any item.

## Status

| # | Item | Status |
|---|---|---|
| 1 | Gradients: move-whole-spline (1a), gradient tool (1b), stop editing (1c) | Done V1_38-V1_42; radial not built |
| 2 | User-rearrangeable tool buttons | Open (registry-driven generation done) |
| 3 | PMD editor: editing vs playback kept separate | Decided, no work needed |
| 4 | Portrait: reference another project's grid | Open |
| 5 | PMD layout: drawers + floating controls | Done (controls drawer, floating scrubber + d-pad, tab bar with Debug) |
| 6 | PSD import/export | Open |
| 7 | IndexedDB project persistence | Done V1_47 |
| 8 | glTF/GLB 3D viewer layer | Open |
| 9 | Solid background fill (document setting) | Open |
| 10 | Checkerboard colour profiles | Done V1_39 (8-canvas-px squares V1_44_2) |
| 11 | SVG export for vector layers | Open |
| 12 | Transform: selection / layers / masks | Selection resize + rotate done V1_40-V1_41_3; layer/mask open |
| 13 | Blend modes (group + layer) | Done Sessions 7a-7d |
| 14 | Raster tool gating on huge canvases | Done; toast + tappable greyed buttons V1_44_1 |
| 15 | Expand canvas by selecting outside it | Open |
| 16 | Swatch raw values (hex/RGBA/HSV+A) + copy hex | Done |
| 17 | Standalone gallery for exported JSON files | Idea only |
| 18 | Nudge menu (18a) / nudge transformation (18b) | Idea only |
| 19 | Feather for Bucket fill edges and Wand selections | Idea only |

## Open items

### 1. Gradients -- remaining
- Radial gradients: separate render path from `renderGradientFill` (linear only).
- Undecided loose end: on the stop bar in Delete Points mode, missing a marker inserts a stop instead of doing nothing.

### 2. Rearrangeable tool buttons
- `renderToolButtons()` already builds all 20 tools from `TOOL_REGISTRY` into per-section containers.
- Undecided: are tool-adjacent controls (Delete Pts, Ext Line, pen width, Move Sel/Delete/Deselect) rearrangeable too (registry must grow), and is rearranging across sections or within one?
- Needs a persisted arrangement key; visibility/gating logic must not depend on DOM order. Home: Customisation panel > Customize Tools (placeholder exists).

### 4. Portrait: reference another project's grid
- Toggleable, read-only overlay of another Portrait project's grid, picked from the gallery.
- Distinct from ReferenceLayer (arbitrary image). V1_47 makes this easier: `getProjectData()` + `buildFramesFromSaveData()` read a project without opening it.

### 6. PSD import/export
- Principle: never silently drop data the editor can't edit; unsupported PSD features become placeholder/reference info.
- CDN library allowed (e.g. ag-psd). Needs a documented mapping for mask/clip `hookedTo` vs PSD layer masks/clipping groups, and for blend modes with no PSD equivalent.

### 8. glTF/GLB viewer layer
- Separate subsystem (own model data, camera, transform, visibility, opacity); never converted into pixel artwork. Support both `.glb` and `.gltf`.
- CDN three.js acceptable. WebGL was removed from ImageLayer for memory/iOS resize leaks: scope the context to this subsystem and test iOS memory on resize.
- Layer-tree presence like ReferenceLayer (positionable, non-pixel).

### 9. Solid background fill
- Decided: document-level setting (like gridW/profile), not a layer node. Painted above the checkerboard, below all layers, in live view and in flatten/export/thumbnails. One new save-data field. UI: button under the Mask/Clip row in Layers.
- Distinct from item 10's solid checker profile (display-only, never exported).

### 11. SVG export
- Vector layers only. Reads `VectorLayer.splines` (incl. gradient `stops`) and emits path data from the same Catmull-Rom math the renderer uses, so the two can't drift.
- Output flattened; the live project untouched (read-only export). Entry point in the File panel.

### 12. Transform -- remaining
- Layer/mask transform: extend ReferenceLayer-style fields (`gx/gy/gw/gh/rotation/flipH/flipV`). Check it inside a blended group.
- Rotate snap-angle slider (rotate is freeform today).
- Shelved "Free Transform": decided single offset rotate handle at one corner; undecided whether Lock/Free resize merge (touch has no modifier key) and whether rotate stays a separate mode.
- Selection transform limits: rectangular selections only; nearest-neighbour only (bilinear/bicubic options present but disabled); negative size mirrors.

### 14. Raster gate -- open question
- Should the area threshold also pick storage (PixelLayer vs ImageLayer), or stay UI-only with storage on the 999px-per-side rule? Undecided. Worth re-measuring now that bulk writes are batched (V1_44).

### 15. Expand canvas by selecting outside it
- Main canvas only (not Portrait). Needs selection bounds that can exceed the canvas; don't deepen existing clamping.

### 17. Standalone gallery for exported JSON
- If built: one HTML page rendering thumbnails with a trimmed copy of `flattenTreeToCanvas`, folder via file picker / drag-drop, or `npx serve`. Rejected: Windows thumbnail provider (native DLL, second renderer to keep in sync). Fallback: Tauri.

### 18. Nudge
- 18a: 4 arrow buttons + step size (1/10/50). Undecided: move the outline or the pixels (Move Sel mechanism); placement; configurable steps. Check `moveSelectedBlock` first.
- 18b: +/- steps on an active transform with a choosable anchor incl. centre (centre-anchored resize doesn't exist; `computeTransformPreviewRect`'s anchor table).

### 19. Feather
- Soft edges for Bucket fills and Wand selections; feathered selections erase proportionally.
- An earlier attempt exists (`bucket_projectname_colourtool_fix_2`, branch `feather-colourtool-fix-2`: 0-20 px sliders). That algorithm was excluded on purpose in later handoffs; treat it as a reference, not a base. New engine needs the usual research and agreement first.

## Item 7 (IndexedDB) -- what shipped, what didn't
- Shipped: `meta`/`data` split (boot reads metadata only; 300 projects / ~120 MB boots in ~0.4s headless); boot and project-open crash guards with sticky safe mode; every open/read/write error-checked with in-memory fallback; Reset Storage (gallery + Debug); quota-aware write errors; `storage.persist()`; two-tab warning + list sync; time-based ids; autosave on page hide; backup reminder in the gallery.
- Not built: "export all projects" backup action; storage-usage warning thresholds; autosave on a timer (only on page hide and Main Menu).
- Constraint: Safari clears site storage after 7 days without a visit and quota eviction is origin-wide, so IndexedDB is a cache; `.pxproj.json` export is the backup.

## Keep flexible
- Layer kinds that aren't pixel-backed (Reference today; 3D later).
- Project-level settings as fields alongside gridW/profile (item 9).
- One authoritative spline representation read by renderer and any exporter (item 11).
- Selection bounds liftable past the canvas (item 15).
- Screen-agnostic drawer/floating-control system (the PMD screen already reuses it).
