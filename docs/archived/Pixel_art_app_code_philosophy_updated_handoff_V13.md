# Pixel Art App --- Code Philosophy & Handoff

## App Purpose

The app is intended as a **MediBang Paint alternative for iOS**, with a focus on providing a lightweight, responsive drawing and image-editing experience.

## Purpose

This project is a touch-first, single-file pixel-art editor built around
a layered Canvas 2D rendering model.

The code has evolved incrementally, through real testing, bug reports,
and architectural rewrites. The guiding idea is:

> **Keep the editor understandable, make touch interaction the primary
> interface, preserve existing behavior, and make the underlying state
> explicit enough that future changes can be traced and tested.**

This document is the handoff/reference document for future development.

## Current Build Status — V13

The current build is `Pixel_art_app_V13.html.txt`.

V12 introduced the **Document state → Renderer invalidation → Render** architecture. Document state remains authoritative, while Canvas 2D/WebGL2 act as rendering targets.

V13 is based on V12 and restores the **Portrait opacity slider behaviour from V11**, because V12's renderer-invalidation changes caused the slider to be rebuilt during interaction. V11 remains the clean historical reference for this specific slider behaviour.

Important regression note:

- Do not replace V12's rendering architecture merely to fix the Portrait opacity slider.
- For the Portrait opacity slider, preserve the V11 interaction pattern: update the Portrait tile opacity state and overlay directly while the slider is being dragged, without rebuilding/replacing the slider control on every movement.
- V12 remains the architectural base for the renderer invalidation pipeline.

It describes both the design philosophy and the important architectural
decisions that should not be accidentally lost when a new build is
produced.

------------------------------------------------------------------------

## 1. Single-file, self-contained application

The application is intentionally packaged as one HTML file.

That means:

-   HTML, CSS, JavaScript, and application data/logic live together.
-   The app can be opened directly in a browser.
-   External build tooling is avoided where practical.
-   New features should not unnecessarily introduce external runtime
    dependencies.
-   Comments are valuable because the HTML file is also the portable
    source code.

The project has grown substantially beyond its original size, so
organization, comments, syntax checking, and careful incremental changes
are increasingly important.

**Do not casually replace working systems with simplified
demonstrations.** A new build must preserve previously implemented
behavior unless the change explicitly supersedes it.

------------------------------------------------------------------------

## 2. Touch-first, desktop-compatible

Touch interaction is the primary design target.

Important consequences:

-   Buttons need comfortable touch targets.
-   iOS/Android behavior must not depend on mouse-only interaction.
-   Important operations need on-screen controls.
-   Touch drawing must remain responsive.
-   Desktop keyboard shortcuts are conveniences, not replacements for
    touch controls.
-   Desktop may expose more controls when there is enough space.
-   The mobile bottom bar has a fixed number of visible buttons
    depending on available screen space and can scroll horizontally to
    expose additional panels/tools.

The editor is intended to feel natural on both an iPhone and desktop.

------------------------------------------------------------------------

## 3. Canvas 2D is the rendering foundation

The fundamental Canvas 2D setup is:

``` js
this.el = document.createElement('canvas');
this.ctx = this.el.getContext('2d');
```

Canvas is primarily a rendering surface.

Editable artwork state should remain distinguishable from:

-   Canvas rendering,
-   layer compositing,
-   selections,
-   marching ants,
-   cursors,
-   tile-isolation overlays,
-   UI,
-   and other temporary visual effects.

This distinction is essential for reliable undo/redo and future
transformations.

------------------------------------------------------------------------

## 4. Separate artwork representations by profile

The editor has four user-facing canvas profiles:

**Photo \| Pixel Art \| Portrait \| Sprite**

The order is intentional.

### Pixel Art

Pixel Art is the **default profile**.

It remains optimized around explicit pixel-art data and the existing
pixel-layer architecture.

The current conceptual boundary is:

-   Pixel Art: up to 999 px on either side.
-   Larger canvases are not treated as Pixel Art.

The 999 px rule is a profile distinction, not merely a browser safety
limit.

### Photo

`photo` is the canonical internal name.

Older internal/profile names such as `standard` or `image` should be
treated as legacy aliases where compatibility is needed, but new code
should use `photo` everywhere, including debug output.

Photo mode is intended for substantially larger images and is the place
where optimized image-backed representations can be introduced.

A safety ceiling is still appropriate to prevent accidental
browser-memory disasters. The current policy is a maximum of 4096 × 4096
for non-Pixel-Art canvases unless deliberately changed later.

### Portrait

Portrait uses a 40 × 40 tile grid.

For larger Portrait spritesheets:

``` text
80 × 80

┌────────┬────────┐
│ 40×40  │ 40×40  │
├────────┼────────┤
│ 40×40  │ 40×40  │
└────────┴────────┘
```

Each 40 × 40 tile has an **independent 15-colour palette**.

Colours may be numerically identical between palettes. Shared colours do
not mean the palettes are linked.

Tile palettes are selected according to pixel/cursor position.

A Portrait import is accepted only when both dimensions are compatible
with the 40 × 40 grid. A non-compatible Portrait import falls back
silently to the standard/default behavior rather than forcing invalid
Portrait state.

### Sprite

Sprite remains a separate profile and should preserve its existing
profile-specific behavior.

------------------------------------------------------------------------

## 5. Preserve dimensions when switching profiles

When switching between profiles in the New Canvas UI:

-   The entered width and height are preserved.
-   Switching profiles should not unexpectedly overwrite the user's
    dimensions.
-   Pixel Art remains the default when opening New Canvas.
-   Profile-specific validation occurs when creating/importing rather
    than destructively rewriting the user's entered numbers.

------------------------------------------------------------------------

## 6. Pixel data is explicit

Pixel-like layers store editable pixel data.

The editor therefore has a distinction between:

-   editable pixel data,
-   Canvas 2D rendering,
-   compositing between layers,
-   selections,
-   and visual overlays.

This separation supports:

-   undo/redo,
-   bucket fill,
-   Wand selection,
-   Lasso selection,
-   masks,
-   clipping,
-   imported images,
-   colour-to-alpha/background removal,
-   and future transformations.

------------------------------------------------------------------------

## 7. Continuous strokes are intentional

Drawing is not implemented as independent dots.

Pointer/touch movement can arrive with gaps between events. The stroke
system therefore interpolates between the previous and current pointer
positions and paints the pixels along that path.

Conceptually:

``` text
previous pointer position
        ↓
current pointer position
        ↓
interpolated line
        ↓
brush/pencil/eraser coverage
        ↓
painted pixels
```

This is required for fast finger strokes to remain continuous.

The same continuous-stroke foundation should be reused by tools that
need it instead of independently reinventing line interpolation.

------------------------------------------------------------------------

## 8. Drawing tools and their semantics

The visible tool names are part of the user-facing API.

### Pencil Tool ✏️

The Pencil Tool is the hard, pixel-oriented drawing tool.

It should behave like a pencil rather than a soft brush.

### Brush Tool 🖌️

The Brush Tool is a size-adjustable drawing tool.

It supports:

-   adjustable size,
-   hard/normal behavior,
-   and a soft mode.

### Soft Brush

Soft Brush uses a falloff rather than simply drawing a solid hard-edged
pixel region.

### Hard Eraser

Hard Eraser removes pixels directly.

Selecting the Hard Eraser also selects the transparent swatch because
transparency is the semantic equivalent of the operation.

### Soft Eraser

Soft Eraser changes alpha gradually.

It **does not** select the transparent swatch because it is not
identical to hard transparency replacement.

### Colour tool

Selecting the colour tool from another drawing tool should automatically
return to the Pencil Tool for drawing, rather than leaving the user in
an ambiguous drawing state.

------------------------------------------------------------------------

## 9. Selection is data, not merely a visual effect

Selections use a dedicated selection representation.

Relevant selection concepts include:

-   rectangular selection,
-   Wand selection,
-   Lasso selection,
-   additive/subtractive selection,
-   tolerance,
-   contiguous/global matching,
-   selection counts,
-   selection bounds,
-   selection undo/redo,
-   blue selection highlighting,
-   marching ants,
-   and future feather/edge-processing experiments.

The selection overlay is only a visualization.

**Marching ants are not the selection data.**

Likewise, blue selection highlighting must never become part of the
editable artwork.

------------------------------------------------------------------------

## 10. Wand and bucket selection/fill semantics

The Wand and Bucket systems should expose the concepts users expect from
established paint editors.

Both can have:

-   tolerance,
-   contiguous/global behavior.

The exact matching algorithm should be documented when changed.

Tolerance must account for the fact that source pixels are not
necessarily perfectly black/white or exact copies of one another.

------------------------------------------------------------------------

## 11. Colour-to-alpha / background removal

Colour-to-alpha is a distinct operation from ordinary selection
feathering.

The intended use case is similar to
green-screen/blue-screen/background-removal processing:

Given a target background colour, pixels that are close to that colour
become transparent according to their colour distance.

The algorithm should not assume:

``` text
background = exact #FFFFFF
foreground = exact #000000
```

Instead it must account for near-colours and intermediate pixels.

For example:

``` text
A = 100% black / 0% white
B = 80% black / 20% white
C = 60% black / 40% white
D = 40% black / 60% white
E = 20% black / 80% white
F = 0% black / 100% white
```

Selecting white should cause the white/background contribution to become
transparent while preserving the foreground contribution.

This should be treated as colour-to-alpha/background removal, not as a
simple exact-colour flood fill.

------------------------------------------------------------------------

## 12. Layers and groups are separate concepts

A layer is an editable/renderable object.

A group is a tree node containing children.

Conceptually:

``` text
Group
├── Layer
├── Layer
└── Group
    └── Layer
```

Groups are not duplicated layer stacks.

This supports:

-   nested groups,
-   group opacity,
-   group visibility,
-   group selection,
-   block movement,
-   group deletion,
-   masks,
-   references,
-   and future PSD-style hierarchy preservation.

------------------------------------------------------------------------

## 13. The layer tree is authoritative

The layer tree represents stacking and nesting.

A flattened `layers` collection may exist for compatibility or linear
rendering operations, but it must not become a competing source of
truth.

> **The tree is authoritative for hierarchy.**

Future layer operations should modify the authoritative tree and then
update any derived/flattened representations.

This rule is particularly important for history restoration.

------------------------------------------------------------------------

## 14. Portrait tiles are regions, not separate documents

Portrait tiles share one document and one layer hierarchy.

A tile is **not a layer**.

All tiles continue to be affected by:

-   layer visibility,
-   layer opacity,
-   groups,
-   masks,
-   and other layer behavior.

Tile isolation is a viewing/editing aid.

The optional "hide other tiles" behavior should hide the other tile
artwork/checkerboard visually while editing the current tile, without
turning the tiles into separate documents or breaking layer semantics.

------------------------------------------------------------------------

## 15. Import/export should preserve information

When importing:

-   Do not unnecessarily change canvas dimensions.
-   Preserve transparency.
-   Preserve useful source information.
-   Apply profile-specific rules only when the profile requires them.
-   Imported images used as pixel layers should preserve the existing
    canvas size when that is the relevant operation.
-   New-project image imports can size the canvas to the imported image
    where the profile permits it.

Imported image naming should follow the project name so that the project
and its exported image remain naturally associated.

Portrait spritesheets may contain multiple 40 × 40 tiles, each with its
own palette, while the whole spritesheet can still be exported as one
combined image.

------------------------------------------------------------------------

## 16. History is a document-state system, not merely two buttons

The application previously used a simple `undoStack` / `redoStack`
model.

That architecture caused desynchronization problems as the editor
accumulated:

-   layers,
-   groups,
-   selections,
-   imports,
-   masks,
-   frame changes,
-   and other state.

The intended architecture is now a **history tree**.

Conceptually:

``` text
                 B ── C ── D
                /
A ────────────
                \
                 E ── F
```

The user can move backward to an earlier state and then continue from
there without destroying the abandoned branch.

### Required behavior

-   Undo moves to the previous history node.
-   Redo moves toward a selected future child/branch.
-   A new edit after undo creates a new branch.
-   Existing future branches remain available.
-   Undo History is a view of the same authoritative history model.
-   Clicking an earlier history entry should restore that state.
-   Clicking a greyed/future entry should restore the selected future
    state, Paint.NET-style.

The history UI must not maintain an independent copy of document
history.

------------------------------------------------------------------------

## 17. History entries must own their state

History entries must not contain live references to mutable editor
objects when those objects can subsequently change.

A historical state must be immutable or otherwise independently
restorable.

For state-based entries, the conceptual model is:

``` text
before
after
```

For command/reversible-operation entries, the command must own enough
information to reliably apply and reverse itself.

This is especially important for:

-   groups,
-   nested layers,
-   duplication,
-   deletion,
-   reordering,
-   masks,
-   selections,
-   imports,
-   and future PSD structures.

------------------------------------------------------------------------

## 18. One user operation should produce one history transaction

Complex user actions should normally appear as one logical history
entry.

For example:

``` text
Select four layers
        ↓
Create group
```

should undo as one action.

Likewise:

``` text
Drag selected layers as a block
```

should not create hundreds of tiny history entries.

The history UI should describe user actions, not low-level pointer
events.

------------------------------------------------------------------------

## 19. History must include selections

Selection creation/modification is document state from the user's
perspective.

Therefore actions such as:

-   Wand selection,
-   Lasso selection,
-   rectangular selection,
-   additive selection,
-   subtractive selection,

must be represented in history when they are intended to be undoable.

A selection undo must restore the correct selection state without
accidentally deleting or hiding the only artwork layer.

Selection restoration must also avoid unrelated side effects such as
destructive deselection caused by frame switching.

------------------------------------------------------------------------

## 20. Rendering and editing remain separate

The visual stack contains things such as:

``` text
Artwork
Selection highlight
Marching ants
Cursor
Tile isolation overlay
Reference layers
UI
```

These remain conceptually separate.

An overlay must never accidentally become editable artwork.

This is especially important for:

-   selections,
-   marching ants,
-   cursor rendering,
-   tile isolation,
-   masks,
-   reference layers,
-   and future 3D references.

------------------------------------------------------------------------

## 21. Performance philosophy

Performance matters particularly on mobile.

Avoid:

-   one DOM element per pixel,
-   unnecessary full-canvas rebuilding,
-   repeated allocation of huge arrays during pointer movement,
-   expensive work every animation frame,
-   unnecessary duplication of image data,
-   whole-document snapshots when a compact reversible operation is
    sufficient.

Prefer:

-   typed arrays where appropriate,
-   compact selection structures,
-   cached render state,
-   incremental updates,
-   Canvas 2D for large pixel operations,
-   image-backed buffers for large Photo-mode artwork,
-   deferred/non-critical initialization,
-   progressive visual loading.

The editor should remain responsive on mobile even with large canvases
and selections.

------------------------------------------------------------------------

## 22. Profile-specific optimization is intentional

Pixel Art and Photo mode should not be forced through identical data
structures merely for conceptual purity.

Pixel Art benefits from:

-   explicit pixel data,
-   palette-aware behavior,
-   discrete tools,
-   and pixel-level operations.

Photo mode can benefit from:

-   RGBA image buffers,
-   Canvas/ImageData operations,
-   fewer per-pixel JavaScript objects,
-   and more efficient large-image rendering.

The architecture should share behavior where useful without forcing the
least efficient representation onto every profile.

------------------------------------------------------------------------

## 23. Progressive initialization

The Pixel Art Hub should become visually usable as early as practical.

Secondary/debug systems can initialize later where safe.

The principle is:

> **Show the user something useful quickly, then progressively
> initialize secondary systems.**

However, deferred initialization must not create race conditions where a
button appears ready but its underlying system does not exist yet.

------------------------------------------------------------------------

## 24. UI state must reflect actual application state

Controls such as:

-   Undo,
-   Redo,
-   History,
-   layer movement,
-   selection operations,
-   tool-specific controls,
-   colour picker availability,
-   Portrait tile controls,
-   and profile-specific controls

must be enabled, disabled, shown, or hidden according to actual state.

The UI must not merely look correct.

A control should not be visible when its prerequisites are absent, and a
disabled state should correspond to a real inability to perform the
operation.

------------------------------------------------------------------------

## 25. The bottom bar is responsive

On iPhone-sized screens, only a limited number of panel buttons should
be visible at once.

On desktop, more buttons can appear.

The bottom panel bar should therefore be horizontally scrollable rather
than shrinking every button until the labels become unusable.

The panel-management architecture is intended to eventually support
panels such as:

-   Navigator,
-   History,
-   Brush Presets,
-   Animation/Timeline,
-   Reference Controls,
-   3D Reference Controls,
-   and other dockable/editor panels.

For now, the panel button is primarily a **panel-management menu** where
the user chooses which panels are visible.

------------------------------------------------------------------------

## 26. Keep the Hub focused

The Hub should not contain redundant profile-selection controls when the
same choice belongs in New Canvas.

The profile selector belongs in the **New Canvas** flow.

The Hub should remain focused on project/gallery navigation.

This prevents two different profile-selection systems from becoming
contradictory.

------------------------------------------------------------------------

## 27. 3D references are a separate subsystem

A future 3D reference layer is possible, but it should not contaminate
the pixel-art rendering model.

A 3D reference should be treated as a reference/editor subsystem with
its own:

-   model data,
-   camera,
-   transform,
-   visibility,
-   opacity,
-   and controls.

It should not be converted into editable pixel artwork merely to make it
fit the existing layer system.

------------------------------------------------------------------------

## 28. PSD and unsupported data

PSD support should preserve layer hierarchy where possible.

Unsupported PSD features should preferably be represented as
reference/placeholder information rather than silently destroyed.

The philosophy is:

> **Do not throw information away just because the editor cannot
> currently edit it.**

This principle also applies to future file formats and reference layers.

------------------------------------------------------------------------

## 29. Debugging and handoff discipline

Every generated build should be treated as a real software build, not
just a code snippet.

Before handing off a build:

1.  Check JavaScript syntax.
2.  Check that major referenced functions exist.
3.  Check that UI controls have corresponding handlers.
4.  Avoid accidentally reverting unrelated features.
5.  Preserve existing terminology and profile names.
6.  If an architectural rewrite occurs, update this handoff document.
7.  Explicitly list known incomplete systems instead of implying they
    are implemented.

### Important lesson from previous builds

A feature can exist in HTML/CSS and still be functionally absent.

For example, Brush size/softness controls can remain in the UI while the
drawing path continues using the old hard brush implementation.

Therefore:

> **Do not consider a feature implemented merely because its controls or
> class definitions exist. Trace the actual runtime path.**

------------------------------------------------------------------------

## 30. Known architectural danger zones

These areas deserve extra caution:

### History ↔ layer tree

History restoration must restore the authoritative layer tree rather
than merely a flattened `layers` array.

### History ↔ selection

Selection restoration must not accidentally clear selection because
another state-changing function happens to run during restoration.

### Profile ↔ import

Import behavior differs by profile. Do not apply Portrait palette rules
to Photo or Pixel Art.

### Tile isolation ↔ layers

Tile isolation is visual; layers remain shared.

### Tool UI ↔ drawing engine

Changing a tool label or adding a slider does not automatically change
the drawing algorithm.

### Canvas size ↔ data representation

Changing canvas dimensions must update the authoritative artwork
representation and all derived rendering state together.

### Large images ↔ memory

Never assume a large canvas is cheap merely because Canvas 2D can
display it.

------------------------------------------------------------------------

# Current Development Direction

The project is moving toward a state-driven editor architecture:

``` text
                    Document State
                         │
             ┌───────────┴───────────┐
             │                       │
         Layer Tree              Artwork Data
             │                       │
             └───────────┬───────────┘
                         │
                  History Engine
                         │
             ┌───────────┴───────────┐
             │                       │
         Undo / Redo            History UI
```

The important rule is:

> **There should be exactly one authoritative representation of each
> piece of document state.**

UI, flattened lists, rendering, history, and debug information should
derive from that state rather than becoming competing copies.

------------------------------------------------------------------------

# Current Feature/Architecture Checklist

## Established direction

-   [x] Single-file HTML application
-   [x] Touch-first UI
-   [x] Canvas 2D rendering
-   [x] Continuous pointer-stroke interpolation
-   [x] Layer/group hierarchy
-   [x] Portrait 40 × 40 tile model
-   [x] Independent 15-colour Portrait palettes
-   [x] Profile distinction: Photo / Pixel Art / Portrait / Sprite
-   [x] Pixel Art as default profile
-   [x] Responsive mobile/desktop bottom panel bar
-   [x] Pencil / Brush / Soft Brush / Hard Eraser / Soft Eraser concepts
-   [x] Tool-specific size/softness controls
-   [x] Selection as actual state rather than merely a visual overlay
-   [x] Marching ants treated as visualization
-   [x] Bucket/Wand tolerance and contiguous/global concepts
-   [x] Colour-to-alpha/background-removal direction
-   [x] History-tree direction
-   [x] Undo History panel direction
-   [x] Large-image optimization direction for Photo mode

## Progress in the current restoration pass

The following items have now been implemented in the current build, subject to real-device testing:

-   [x] Pencil / Brush / Soft Brush / Hard Eraser / Soft Eraser reference restored.
-   [x] Colour-to-Alpha/background-removal reference restored.
-   [x] Photo / Pixel Art / Portrait / Sprite profile routing restored.
-   [x] Pixel Art uses `PixelLayer`; Photo uses `ImageLayer` rather than the old image-backed PixelLayer workaround.
-   [x] Colour Match tool added for exact sampled-colour replacement, including one undo transaction.
-   [x] History changed from retained branching to linear undo/redo for memory safety.
-   [x] Pixel history changed from full-grid snapshots to sparse changed-pixel deltas.
-   [x] History received a byte-based memory budget plus an action-count safeguard.
-   [x] Photo/ImageLayer history changed to 64 × 64 RGBA tile snapshots for localized edits, with full-image snapshots reserved for operations that affect most/all of the image.
-   [x] Photo history is bounded separately so large image edits cannot grow history without limit.
-   [x] JavaScript syntax checks were run before publishing the latest restoration builds.
-   [x] WebGL2 vs Canvas 2D research completed; no WebGL2 rewrite has been applied yet. Proposed direction: keep Pixel Art Canvas 2D, and consider a WebGL2 renderer for Photo mode behind a renderer abstraction.

Important: these are implementation claims, not a substitute for real-device behavioral testing. In particular, large Photo-mode history and cross-frame behavior still need testing on the target browsers/devices.

## Still requiring careful implementation/testing

-   [ ] Complete verification of every document-mutating operation in
    the history engine
-   [x] Linear undo/redo behavior replaces the previous retained branch-history approach.
-   [ ] Complete verification of undo/redo behavior under all combinations of undo/redo/new edits
-   [ ] Canvas resize history
-   [ ] Layer reorder history
-   [ ] Full mask semantics
-   [x] Core Colour-to-Alpha implementation restored.
-   [ ] Colour-to-Alpha edge-case verification across layer types and large images
-   [ ] Indexed colour export/import
-   [ ] 3D reference layer
-   [ ] Dockable editor panel system
-   [ ] Animation/timeline system
-   [ ] Full PSD feature preservation
-   [ ] Large Photo-mode stress testing on real iOS/Brave/Safari targets
-   [ ] Cross-frame history stress testing with the new memory-bounded model

------------------------------------------------------------------------

# Current backlog / next passes

## High priority

1. **History correctness audit** — verify every document-mutating operation participates in the new linear, memory-bounded history model.
2. **Canvas resize history** — make resize undoable without creating excessive full-image memory pressure.
3. **Layer reorder history** — verify tree/layer operations and their undo/redo interactions.
4. **Photo stress testing** — progressively test large images, many edits, many layers, and long sessions on iOS/WebKit and Chromium/Brave.
5. **Cross-frame history testing** — verify frame switching, undo/redo, duplication, deletion, and history isolation.
6. **Full mask semantics** — implement/verify masks as document state rather than treating them as ordinary pixel layers.

## Medium / future

7. **Indexed colour export/import**.
8. **3D reference layer**.
9. **Dockable editor panel system**.
10. **Animation/timeline system**.
11. **Full PSD feature preservation**.
12. **Photo renderer architecture** — introduce a renderer abstraction; investigate WebGL2 for Photo mode with Canvas 2D fallback. Keep the document/image data independent of GPU resources.
13. **Photo tiling as a rendering/data architecture** — potentially extend the 64 × 64 tile model beyond undo history if profiling shows it improves iOS responsiveness and memory usage.
14. **Memory diagnostics** — expose current raster/history/tile estimates in the debug UI to help identify browser memory pressure.
15. **Potential product split** — eventually consider separate Photo Editor and Pixel Art Editor shells while sharing low-level document utilities. Do not split prematurely while core history/profile behavior is still being stabilized.

# Guiding Principle

The project has repeatedly grown by fixing real bugs and adding features
from actual use.

The overarching philosophy is therefore:

> **Make the editor behave like a real pixel-art application, but keep
> the implementation understandable enough that a future change can be
> traced back to the underlying state it modifies.**

Touch-first. Performance-conscious. State-driven.
Information-preserving. Incremental. Heavily commented. And, above all,
**tested against the actual behavior rather than the existence of code
that appears to implement it.**


------------------------------------------------------------------------

# 31. Current Source-of-Truth and Restoration Rules

## Current source of truth

The authoritative current codebase is:

`Pixel_art_app_restored_regressions_colour_match_photo_pixel_tools_alpha_profiles_history_memory_safe_photo_tiles.html`

Do **not** replace it wholesale with an older build.

Older HTML builds are reference implementations only. They may be consulted when a feature is confirmed to have disappeared, but their unrelated behavior must not automatically be copied forward.

> **Current build is authoritative. Older builds are evidence/reference material.**

If an older implementation cannot be transplanted safely without inventing or substantially rewriting behavior, **do not improvise a replacement just to make the feature appear complete**. Document the required implementation here instead.

## Recommended historical reference builds

The user has already saved the useful historical builds. The main references are:

- `Pixel_art_app_history_engine_v5_tools.html`
  - history architecture and tool-era reference
- `Pixel_art_app_photo_pixelart_profiles_v3.html`
  - Photo / Pixel Art / Portrait / Sprite profile architecture
- `Pixel_art_app_image_mode_optimized_v2.html`
  - optimized large-image/ImageLayer reference
- `Pixel_art_app_pencil_brush_eraser.html`
  - Pencil / Brush / Soft Brush / Hard Eraser / Soft Eraser reference
- `Pixel_art_app_colour_to_alpha_new.html`
  - Colour-to-Alpha/background-removal reference

Do not require the next chat to receive every intermediate regression build.

------------------------------------------------------------------------

# 32. Confirmed Missing / Incomplete Systems

These were identified by comparing the current source-of-truth build with the historical builds.

## 32.1 Canvas resize + anchor

Required behavior:

- Long-press a project/canvas in the Pixel Hub.
- Open a context menu.
- Choose Change Canvas Size.
- Enter width and height.
- Choose an artwork anchor using edge/corner buttons.
- Resize the authoritative artwork representation.
- Preserve artwork relative to the selected anchor.
- Update all derived rendering state.
- Create one logical history transaction.

Anchor grid:

```text
TOP-LEFT       TOP-CENTER       TOP-RIGHT
CENTER-LEFT    CENTER            CENTER-RIGHT
BOTTOM-LEFT    BOTTOM-CENTER    BOTTOM-RIGHT
```

Example:

- Increasing width with LEFT anchoring keeps the left edge fixed and adds space to the right.
- Increasing width with RIGHT anchoring keeps the right edge fixed and adds space to the left.
- Resizing smaller crops according to the selected anchor.

Do not copy an old flat-layer implementation blindly if the current layer-tree architecture differs.

## 32.2 History branch UI / tree integration

The intended architecture is a history tree:

```text
A ── B ── C
     \
      D ── E
```

Required behavior:

- Undo moves to the previous node.
- Redo follows the selected future child/branch.
- Editing after undo creates a new branch.
- Existing future branches remain available.
- Clicking an earlier entry restores that state.
- Clicking a greyed/future entry restores that state, Paint.NET-style.
- The History panel is only a view of the authoritative history tree.
- The UI must not maintain a second history representation.

Do not resurrect the old independent `undoStack`/`redoStack` architecture merely to make the buttons work.

### History memory rule

Unreachable history nodes should become eligible for cleanup when no branch/path references them.

Identical states should not be blindly deduplicated if doing so destroys meaningful branch identity or transitions.

Prefer structural sharing / immutable snapshots where practical.

## 32.3 Brush-control runtime wiring

The current build may contain the visual controls while still missing complete runtime wiring.

Required controls:

- Brush size
- Brush softness
- Soft Eraser size
- Soft Eraser softness

The complete path must be:

```text
slider input
  ↓
tool setting state
  ↓
drawing engine
  ↓
brush coverage/falloff
  ↓
pixel modification
  ↓
history transaction
  ↓
render
```

A slider changing only a label is incomplete.

The historical `bindRange()` behavior should be used as reference if it can be safely recovered.

## 32.4 Image Mode / ImageLayer integration

The policy is:

```text
width <= 999 AND height <= 999
    → Pixel rendering/profile path

width > 999 OR height > 999
    → Photo/Image rendering path
```

This is a rendering/data architecture distinction, not merely a debug label.

Photo/Image mode should use image-backed data for large artwork rather than expanding the entire image into expensive per-pixel JavaScript structures.

Document/profile mode and renderer are separate concepts.

Future zoom optimization may change the renderer/detail strategy without changing the document's Photo/Image mode.

Do not repeatedly convert a large image between ImageLayer and PixelLayer just because zoom changes.

## 32.5 Profile normalization

Canonical user-facing profiles:

```text
Photo | Pixel Art | Portrait | Sprite
```

Canonical internal Photo name:

`photo`

Legacy aliases:

- `standard`
- `image`

may be accepted for compatibility but should normalize to `photo`.

## 32.6 Command search registry

The older command-search architecture used a software command registry based around:

`SOFTWARE_SEARCH_ITEMS`

Each command can have:

- display name
- aliases/search terms
- action

Search should be able to combine software commands with layer/group results where appropriate.

Important searchable concepts include:

- background removal
- colour to alpha
- green screen
- blue screen
- Pencil
- Brush
- Soft Brush
- Hard Eraser
- Soft Eraser
- Undo
- Redo
- panels/history

Recover the exact historical registry if possible rather than creating a second competing search architecture.

## 32.7 Old Wand feather algorithm

The old feather implementation is intentionally **excluded** from restoration.

Do not silently reintroduce it unless the user explicitly requests it again.

------------------------------------------------------------------------

# 33. Regression-Prevention Procedure

Before producing another build:

1. Start from `Pixel_art_app_restored_regressions.html`.
2. Read this handoff.
3. Identify the exact feature being changed.
4. Search historical builds only for confirmed missing/reference implementations.
5. Do not replace the current build wholesale.
6. Verify both UI presence and runtime implementation.
7. Syntax-check every JavaScript block.
8. Check that important controls have handlers.
9. Check that handlers reach the actual state mutation/drawing/history path.
10. Check that unrelated features remain present.
11. If something cannot be safely restored, document it here instead of inventing a fragile replacement.
12. Update this handoff whenever architecture changes.

A feature is not considered implemented merely because:

- a button exists,
- CSS exists,
- a class exists,
- a function has the expected name,
- or the debug menu displays a mode.

> **Trace the actual state mutation, rendering, and history path before declaring a feature restored.**

------------------------------------------------------------------------

# 34. Handoff Build Selection

For a new development chat, provide:

1. `Pixel_art_app_restored_regressions.html` — current source of truth.
2. This updated handoff `.md` — architecture and restoration requirements.
3. Historical reference builds only when a specific missing implementation needs investigation.

Do not hand over every intermediate build unless investigating a particular regression.

The next chat must preserve the rule:

> **Current build is authoritative; historical builds are reference material, not replacement codebases.**


## Build naming convention

Starting with the next published build, HTML deliverables use the short versioned naming scheme:

- `Pixel_art_app.html.txt` — base/unversioned name when appropriate.
- `Pixel_art_app_V1.html.txt`
- `Pixel_art_app_V2.html.txt`
- and so on, incrementing the version number for each subsequent published build.

Avoid embedding long lists of restored features or implementation details in the filename. Those details belong in this handoff/readme.

### Current V1 UI cleanup

The four profile buttons that were previously displayed in the **Pixel Art Hub header** (Photo, Pixel Art, Portrait, Sprite) were removed because the profile selection belongs in the New Canvas flow. The profile buttons inside the New Canvas sheet remain.
