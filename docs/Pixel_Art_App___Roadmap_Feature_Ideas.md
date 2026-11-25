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
| 9 | Solid background fill (document setting) | Done V2_3 |
| 10 | Checkerboard colour profiles | Done V1_39 (8-canvas-px squares V1_44_2) |
| 11 | SVG export for vector layers | Open |
| 12 | Transform: selection / layers / masks | Selection resize + rotate done V1_40-V1_41_3; Transform screen Default mode V2_6; Free, Mesh, vector open |
| 13 | Blend modes (group + layer) | Done Sessions 7a-7d |
| 14 | Raster tool gating on huge canvases | Done; toast + tappable greyed buttons V1_44_1 |
| 15 | Expand canvas by selecting outside it | Done V2_1 as the resize screen (choosing how it's opened is still being tried out) |
| 16 | Swatch raw values (hex/RGBA/HSV+A) + copy hex | Done |
| 17 | Standalone gallery for exported JSON files | Idea only |
| 18 | Nudge menu (18a) / nudge transformation (18b) | 18b done in the Transform screen V2_6 (arrows, typed steps); 18a idea only |
| 19 | Feather for Bucket fill edges and Wand selections | Idea only |
| 20 | Line Extraction (lines from a flattened colour image, offline) | Researched V2.1 (method proven on 8 images in a Python test bench); passes, presets, Advanced and cockpit mode decided; not built |
| 21 | Vector tracing of extracted lines into VectorLayer splines | Idea only; prototype in `experiments/` first |
| 22 | App-wide onboarding (tutorials for the whole app, like #20's) | Idea only; after the app is polished |
| 23 | Mirror mode (symmetry drawing) with a freely adjustable mirror line | Idea; next up for planning |

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
- Built V2_3: Layers "Background" tile and a Colours-panel BACKGROUND row, kept in sync. Mapart always has one (default white carpet `#DCDCDC`, map colours only).
- Distinct from item 10's solid checker profile (display-only, never exported).

### 11. SVG export
- Vector layers only. Reads `VectorLayer.splines` (incl. gradient `stops`) and emits path data from the same Catmull-Rom math the renderer uses, so the two can't drift.
- Output flattened; the live project untouched (read-only export). Entry point in the File panel.

### 12. Transform -- remaining
- Built V2_6: Transform screen "Default" mode (section 3.14 of the handoff) for pixel/image/mask/clip/reference layers and selections.
- Free mode: corner distort (homography); a "mirror corners" switch gives Photoshop-style Perspective. Same maths either way.
- Mesh mode: puppet warp (pins you drag to bend the art).
- Movable anchor point (Paint.NET style) or a 3x3 anchor picker like the Resize sheet; today the anchor is the centre (handles anchor the opposite side).
- Keeping content pushed off the canvas: part of a future smart-object layer; today it is cut off on Done.
- Vector layer transform (move the spline points, lossless).
- Rotate snap-angle slider (rotate is freeform today).
- Shelved "Free Transform": decided single offset rotate handle at one corner; undecided whether Lock/Free resize merge (touch has no modifier key) and whether rotate stays a separate mode.
- Selection transform limits: rectangular selections only; nearest-neighbour only (bilinear/bicubic options present but disabled); negative size mirrors.

### 14. Raster gate -- open question
- Should the area threshold also pick storage (PixelLayer vs ImageLayer), or stay UI-only with storage on the 999px-per-side rule? Undecided. Worth re-measuring now that bulk writes are batched (V1_44).

### 15. Expand canvas by selecting outside it -- built V2_1 as the resize screen
- Built as its own screen (`#resizeScreen`) with its own rectangle and its own viewer (flattened current frame + its own pinch/zoom), not with the selection tool, so selection clamping was left alone. "Selection bounds liftable past the canvas" stays open separately.
- Rectangle: drag edges/corners, drag inside to move, drag outside to draw a new one. Bigger adds space, smaller crops. Lock ratio; snap to common sizes (the dragged side snaps, the locked side follows and the info line says when it's off a common size).
- Confirm crops with a second tap when opaque pixels would be cut off (counted on the current frame). Discard changes nothing. From the gallery both return to the hub (Confirm saves); from the File panel both return to the editor.
- Pixel Art only. Portrait and Sprite use the number sheet.
- New Canvas (V2_1): for Pixel Art the sheet has no size boxes; Create Canvas makes a blank 32x32 and opens the resize screen (`returnTo 'new'`). Confirm rebuilds the blank canvas at the chosen size (right layer type, no undo entry); Discard returns to the hub and creates nothing. Portrait and PMD keep the size boxes.
- Being tried out (Customise > Resize Canvas), then two get removed: A) NUMBERS button inside the screen (stays either way), B) both items in the long-press menu and File panel, C) setting for what Resize Canvas opens by default.

### 17. Standalone gallery for exported JSON
- If built: one HTML page rendering thumbnails with a trimmed copy of `flattenTreeToCanvas`, folder via file picker / drag-drop, or `npx serve`. Rejected: Windows thumbnail provider (native DLL, second renderer to keep in sync). Fallback: Tauri.

### 18. Nudge
- 18a: 4 arrow buttons + step size (1/10/50). Undecided: move the outline or the pixels (Move Sel mechanism); placement; configurable steps. Check `moveSelectedBlock` first.
- 18b: +/- steps on an active transform with a choosable anchor incl. centre (centre-anchored resize doesn't exist; `computeTransformPreviewRect`'s anchor table).

### 19. Feather
- Soft edges for Bucket fills and Wand selections; feathered selections erase proportionally.
- An earlier attempt exists (`bucket_projectname_colourtool_fix_2`, branch `feather-colourtool-fix-2`: 0-20 px sliders). That algorithm was excluded on purpose in later handoffs; treat it as a reference, not a base. New engine needs the usual research and agreement first.

### 20. Line Extraction -- researched V2.1, not built
Pull line art out of a flattened, coloured image (an anime frame, a coloured sketch) onto a new transparent layer, so you can colour underneath. Fully offline: plain pixel maths on a canvas, no server, no AI.

**How other apps do it (researched 2026-11-15)**
- MediBang (iOS) Line Extraction = a Levels filter on brightness: Shadow (black point), Halftone (midtone gamma), Highlight (white point). Pixels between the two points stay grey, so dark fills come through as lines. That's why it looks "grayscale and not grayscale at the same time".
- Clip Studio: Edit > Convert brightness to opacity (white -> transparent; all editions); Layer Property > Expression colour Gray/Monochrome with thresholds (PRO/EX); Layer Property > Extract line (EX only): edge-based, with Threshold of edge, Threshold of fill black and Correction line width.

**Measured on the test images**
- Quaxly anime frame: outlines are dark grey, brightness ~80-120, never black; the hat's shaded band is ~130, mouth 163, hat 170, background stripes 194-208. Only 10-20 levels separate lines from the darkest fill, so no Levels setting removes the band without breaking thin lines (best compromise ~ Shadow 90 / Highlight 140-150).
- Frog character sheet: sketchy pencil lines, weak contrast; Levels loses many inner contours.

**Method that worked (build these as passes)**
1. **Ink pass ("darker than surroundings")** -- background estimate = grey closing of brightness (max filter then min filter, ~7 px): thin dark lines vanish, big fills stay. Ink strength = background - pixel, ramped between ~12 and ~45 levels. Removes dark fills that Levels can't (Quaxly's hat band); keeps sketchy inner lines (frog). Weak spots: solid dark areas keep only their outline; sharp colour boundaries (green/cream belly edge) can show as faint lines; watch the image border (a stray dashed line appeared at the left edge).
2. **Shapes pass (eyes)** -- dark mask (brightness < ~150), erode ~3 px so thin lines vanish, label connected pieces, keep cores of 20-2,500 px (Quaxly: 4 kept, the 6,880 px hat band skipped), grow them back inside the dark mask, then either trace a 2 px outline or fill them solid (EX's "threshold of fill black"). Composite on top of pass 1 (max). Side effect seen: a few extra edges (hat band top edge, inside the ear, inner mouth).
3. **Clean-up + smoothing** -- drop line pieces under ~12 px; then at 4x: blur slightly, re-sharpen with a smoothstep ramp, box-downsample. Removes stair-steps, grey fuzz and specks and gives anti-aliased, ink-like edges. Trade-off: line weight becomes even (taper mostly lost); strong settings can merge details closer than the blur size.
4. **Output** -- a new layer with real alpha (alpha = line strength). Option: black lines, or keep each line's original colour (neither MediBang nor CSP offers this directly; colours come from antialiased line pixels, so they're slightly mixed with the neighbouring fill).

**Update after testing 8 images (2026-11-15): the Shapes pass as built**
- Test set: Quaxly (anime frame), frog sketch sheet, Dogday and a purple cat (flat reference sheets, the cat with dark-purple lines), Greninja (clean single character), Buizel (4-view sheet), two busy Snivy room scenes. One set of settings for all eight; no per-image tuning.
- The first Shapes pass (single "darker than 150" level, grow back "as far as the dark area goes") broke four ways: a fill sitting right at the level (Buizel's orange at 151) flickered into hundreds of blotches; eyes touching face lines grew along the lines over the whole face; one level can't fit both dark-blue eyes on white (Quaxly) and black eyes on purple fur (the cat, whose fur is ~128); bigger "surroundings" windows made boxy shapes around back-view heads.
- **Method that works on all eight:** try several darkness levels (150, 110, 70) and keep a blob if it passes at any of them (the idea behind MSER). At each level: erode 3 px (thin lines vanish), keep cores of 20 px up to ~0.55% of the image area (scales with image size), grow back by exactly 3 px inside the dark mask (can't leak along touching lines), then keep a blob only if it is (a) at least 50 levels darker than a ring just outside it, (b) still under 3x the size limit, and (c) at least 25 levels below the level it was found at (a fill hovering on the level, like Dogday's red ear at ~110, is rejected).
- Results: all six character images clean (eyes, dark paws, zipper teeth, fur tufts, text); the two busy scenes work for the characters but the rooms come out cluttered (wood grain, window grids, shadows), and dark frame edges / vignettes turn into black shapes. Solid black boxes (Dogday's #202020 swatch) come out empty.
- **Known trade-off (Quaxly):** the inner mouth and the right edge of the hat are colour borders with little or no ink. The first, leaky Shapes pass found them by accident (it outlined every dark-ish area); the fixed pass doesn't. A quick colour-border (gradient) pass found them only as dotted pieces and also picked up the hat highlight and background stripes -- not good enough yet.

**Passes (decided 2026-11-15): all of these, each with its own on/off and sliders**
1. Ink (drawn lines) -- on by default.
2. Shapes (eyes, pupils, noses) -- on by default; outline or fill.
3. **Outline mid-dark areas** -- off by default; a level slider. Brings back the old "outline dark-ish areas" behaviour on purpose (Quaxly's mouth and hat band); needs care on images like Buizel.
4. **Outline colour areas** -- off by default ("colouring book"): group similar colours into areas and trace their borders, for anime frames without full outlines. Slowest pass; also outlines highlights, stripes and shading.
- Order and merging: passes run in that order, from most to least trustworthy, and each later pass only fills gaps -- it skips places where a strong line already exists, so edges never double up.
- Clean-up + smoothing run after all passes.

**Controls: three levels (decided 2026-11-15)**
1. **Presets (simple users):** e.g. *Clean line art* (passes 1+2), *Anime frame* (1+2+3), *Sketch* (1, gentler strength), *Colouring book* (1+2+4). One tap; this is all most people need.
2. **Advanced section:** the sliders for every pass, compact (name, value, per-slider reset), grouped by pass. Changing a slider after picking a preset shows the preset as "modified", with a reset-all button.
3. **Cockpit mode (a toggle inside Advanced):** the *same* panel and the same controls -- not a second panel. Advanced is the compact view (for when you know what each slider does); cockpit mode expands every pass and slider in place with:
   - a plain-language explanation of what it does and which problem it fixes (e.g. "Darkness levels: which darknesses count as a shape. Add a lower level if black eyes on dark fur go missing.");
   - a small live example: a tiny generated sample (from the tutorial's sample generator) showing that slider's effect as you drag, next to the real preview;
   - long-press for the longer explanation (existing long-press tooltip system).
   Cockpit mode on/off is remembered (localStorage, try/catch).
- Apple HIG touch targets (44 pt) for every slider, toggle and reset; panels scroll rather than shrinking controls.

**Timings (Python test bench, not the app)**: Levels ~2-4 ms; Ink pass ~0.3-0.7 s at 703x656 / 1152x918; smoothing ~0.46 s at 703x656. Canvas JS should allow a live preview.

**Planned UI (to agree before building)**
- Mode: *Levels* (MediBang-style Shadow / Halftone / Highlight) or *Ink* (line width, strength).
- Shapes pass: on/off, dark level, blob size range, outline or fill.
- Clean-up: speck size; Smoothness slider (low = keeps the original wobble, high = cleaner even lines).
- Colour: black / original colours. Output to a new layer above the source; the source layer is untouched.
- Undecided: entry point (Layers panel action on a layer? File > Import with extraction?), whether to run on the active layer only or the flattened frame, live preview cost on large ImageLayer canvases (>999 px), and whether it needs a Web Worker.
- Tests: a new `line-extraction` group with small synthetic images (thin line + dark fill + dark blob) and pixel-count checks; no copyrighted frames in the repo.

**Tutorial (requested 2026-11-15)**
- A guided tutorial that teaches the Line Extraction tools step by step on sample artworks: what each pass does, which slider fixes which problem (dark fill showing as lines -> Ink mode; eyes as broken rings -> Shapes pass; jaggies -> Smoothness), before/after at each step. Reuse the long-press tooltip and drawer systems; tap-twice confirm only where something is destructive.
- **Samples generated in the app (default):** an algorithm draws each sample from a seed: line art with known thickness, a dark fill close to line darkness (the Quaxly hat-band problem), thick dark shapes (eyes), weak pencil-like lines (the frog problem), colour fills and optional JPEG-like noise. Always works offline, adds almost nothing to the file size, no copyright questions, and every lesson can show exactly the problem it teaches. The same generator feeds the `line-extraction` test group, so the tutorial's samples are also the regression images.
- **Fetched samples (optional extra):** `liangforstudy/pixelart-app` is private, so its files can't be downloaded by the app without a login. Fetching would need a public home: a separate public repo (e.g. `pixelart-app-samples`) or GitHub Pages, MIT or CC-licensed artwork the user owns or may share -- never anime frames or other copyrighted art. If the fetch fails (offline, blocked), show an in-page message ("couldn't download the sample artworks") and fall back to the generated samples; the rest of the app keeps running.
- **Decided (2026-11-15):** the tutorial never takes over. Opening the tool lets you use it right away; a small, out-of-the-way popup (doesn't cover the canvas or block input) points at the **Tutorials** tab, saying the tutorial is there to watch or rewatch, with a dismiss button. Dismissed is remembered (localStorage, try/catch). Tutorials live in a new Tutorials tab on the bottom bar (see #22), right after Customise and before History/Debug.
- Undecided: whether lesson progress is remembered, and the lesson list.

### 21. Vector tracing of extracted lines -- idea
- Turn item 20's lines into strokes with tapering ends, so they look hand-drawn and scale without blur. Steps: centre-line (skeleton) of each line, join pieces into strokes, fit curves, estimate width along the stroke for taper.
- Output must be the existing `VectorLayer.splines` format (Catmull-Rom, pen width, gradient stops) so traced art opens as a normal, editable vector layer -- the one authoritative spline representation from "Keep flexible".
- Licence: Potrace (the best-known tracer) is GPL, which conflicts with this repo's MIT licence. Write our own; don't copy GPL code.
- Prototype as a standalone page in `experiments/` on the item 20 test images first; plan the in-app version (entry point, sliders, tests) once it works.

### 22. App-wide onboarding -- idea, after polishing
- Same approach as #20's tutorial, for the whole app: short guided lessons per system (drawing tools, layers, fill, selection, resize screen, gallery, Portrait, sprite animation, ...), on generated sample artworks where a canvas is needed.
- Timing: build after the app is polished, so lessons don't have to be rewritten as the UI keeps changing.
- **Tutorials tab** on the bottom bar (`#floatingBar`), right after Customise and before the optional History tab and Debug. It lists every tutorial (#20's included) and can replay any of them. Bottom bar scrolls rather than shrinking buttons (principle 18), so one more tab is fine.
- Same rule as #20: tools are usable right away, never blocked by a tutorial; a small out-of-the-way popup points at the Tutorials tab.
- **Dismissing the popup hides it for that one tool only** (decided 2026-11-15).
- **Tutorial settings** (inside the Tutorials tab): turn tutorial popups off for one tool or for all tools, and bring them back (one tool or all). Saved in localStorage (try/catch); if storage is unavailable, popups just show again next session.
- Undecided: lesson list and order, a one-time app welcome on first launch, whether tutorials need tests in their own group (likely yes: each lesson's steps must still match the UI).

### 23. Mirror mode -- idea, next up for planning
- Symmetry drawing: whatever you draw on one side of a mirror line is drawn mirrored on the other side at the same time.
- **The mirror line can be adjusted freely:** drag it to move it anywhere (also outside the canvas), drag an end handle to turn it to any angle. Handles are 44 pt touch targets; a second finger never moves the line by accident (pinch/pan as usual).
- Snapping while dragging: canvas centre, horizontal / vertical / 45 degrees, and pixel positions -- the line can sit **on a pixel's centre** (that pixel column is shared, odd-width symmetry) or **between two pixels** (even-width symmetry). The difference matters in pixel art, so the line shows which one it is.
- Pixel-perfect at 0 / 45 / 90 degrees. At other angles the mirrored stroke is drawn by mirroring the stroke's path and then drawing it (reuse `linePixels`), not pixel by pixel, so a mirrored line has no gaps.
- The line is an overlay: never artwork, never exported (principle 15). Saved with the project (line position/angle and on/off), like gridW/profile.
- One stroke plus its mirror = one undo entry (principle 14). All writes still go through `PixelLayer.plot()` (isolation, history).
- Tools to mirror: pencil, brush, soft brush, both erasers, line, rect/ellipse, fill (the mirrored tap point fills too). Undecided: gradient, selection tools, vector layers (mirror the spline points?), Portrait (isolation already blocks writes outside the active tile).
- Undecided: where the toggle lives (Tools panel? View panel? a button on the canvas?); a lock so the line can't be moved by mistake; more than one line later (horizontal + vertical = 4-way, radial / kaleidoscope with N copies).
- Tests: a new `mirror` group -- mirrored pixel positions for on-centre vs between-pixel lines, a stroke at an odd angle has no gaps, one undo removes both halves, line moves with real drags, a second finger doesn't move it.

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
