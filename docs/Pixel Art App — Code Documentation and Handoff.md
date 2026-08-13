# Pixel Art App --- Code Philosophy, Handoff & Code Documentation

## Read `Pixel_art_app_core_code_philosophy.md` first — this document is subordinate to it

**`Pixel_art_app_core_code_philosophy.md` is authoritative over this entire document.** This is an explicit, deliberate authority statement from the person, not an informal preference — read that file first, in full, before this one. Anything in this document that reads as an architecture principle, an established/current direction, or any other authoritative-sounding claim is subordinate to that document and is overridden wherever the two disagree. This document's actual role is handoff/build-history/code-documentation value only — the record of what changed, when, and why — not the source of truth for what the app fundamentally is or how decisions about it should be made. In particular, that document's central rule — no engine or algorithm is authoritative just because it's already in the codebase; every one must be researched, its advantages/disadvantages compiled (including a real web search, not just reasoning from the existing code), agreed on by both the person and Claude, and checked for whether it can be made lighter/faster (with the tradeoff/reference-check nuance described there) — applies to everything in this file's sections 1–30 too, retroactively. Those sections describe decisions already made; they are not exempt from being revisited under that process.

The companion `Pixel_art_app_bugs_squashed_V1.md` document is optional reading, not part of the required sequence — see the core philosophy document's own note on this.

## App Purpose

The app is intended as a **MediBang Paint alternative for iOS**, with a focus on providing a lightweight, responsive drawing and image-editing experience.

## Purpose

This project is a touch-first, PC compatible, single-file pixel-art editor built around
a layered Canvas 2D rendering model.

The code has evolved incrementally, through real testing, bug reports,
and architectural rewrites. The guiding idea is:

> **Keep the editor understandable, make touch interaction the primary
> interface, preserve existing behavior, and make the underlying state
> explicit enough that future changes can be traced and tested.**

This document serves two roles at once, and both are load-bearing:

1. **Handoff/reference document** — architecture philosophy, current build status, regression history, and restoration rules for carrying context between development sessions.
2. **Code documentation** — the authoritative explanation of how specific systems in the current build actually work (e.g. the Debug System in section 35, the camera/pinch-zoom math in section 36, Portrait-mode tool restrictions in section 37.6–37.8). When a section describes a function, variable, or mechanism by name, treat it as documentation of the live code, not just historical notes — it should stay in sync with the actual build the same way a code comment would.

When updating this file after a change to the app, update both roles: log *what changed and why* (handoff) and, if the change touches a system this document already explains, update that explanation too so it keeps describing the real code (documentation). A stale explanation of working code is as much a bug as a stale comment in the source file.

## Companion document: Bugs Squashed

As of this update, bug fixes are tracked in a **separate companion file**, `Pixel_art_app_bugs_squashed_V1.md`, not in this document's chronological session sections. This document is now forward-looking about bugs *only* in the sense that it captures the durable lessons/best-practices/danger-zones a bug taught (see section 30, "Known architectural danger zones") — not the bug narrative itself (what broke, how it was found, what fixed it). That full story lives in the companion file. If you're looking for "what bugs have been fixed," go there first; if you're looking for "what should I watch out for because of a past bug," section 30 here is the place. Section 0 of the companion file is a pointer-only index of everything found before it existed (nothing before that point was duplicated or deleted from this document — it's still here, in its original chronological section, exactly as before).

## Why this document (and its companion) exist as files, not just chat history

The person has explicitly confirmed, from their own usage, that **looking something up in this file costs meaningfully fewer tokens than searching past conversations for the same information.** This is a real, load-bearing reason these documents exist and get kept accurate, not just a nice-to-have: every session should default to checking this file (and the Bugs Squashed companion) *before* reaching for a past-conversation search, and every session should write findings down here precisely enough that a future session never needs to search chat history to recover them. A vague or stale entry here doesn't just risk being wrong — it risks forcing an expensive chat-history search later that a clear entry would have avoided entirely. This is one more reason accuracy passes on this document (like the one in `V1_26`/`V1_27`/`V1_28` that caught the stale WebGL2/checklist/backlog claims) are worth doing regularly rather than only when something visibly breaks.

## Current Build Status — V1_28

The current development/reference build is `Pixel_art_app_V1_28.html`.

Build lineage: Claude's `Pixel art app v1_3.html` → camera-architecture work in `V1_3_camera` → restored two-finger twist rotation in `V1_4_camera` → `V1_5` (renamed from the `V1_4_camera` line; see Debug System, section 35) → `V1_6` (pinch-zoom anchor fix; see section 36) → `V1_7` (eight-item fix/feature pass; see section 37) → `V1_8_portraits` (Portrait-mode search filtering, per-tile palette ordering/export fixes, tile-isolation freeze; see section 38) → `V1_9` (colour/tool-selection UX fixes, full confirm()→tap-twice migration, dead-code sweep; see section 39) → `V1_10` (fit-to-screen on new/opened canvas, one-finger pan edge clamp, function-naming cleanup pass; see section 40) → `V1_21_wip` (structural-reorganization prep: split the two-purpose image-import function, a further dead-function scan, WebGL2 image renderer removed entirely, adjustable history-memory budget; see section 41, particularly 41.5–41.9 — note the version number jump, per the person's own numbering for the planned large reorganization) → `V1_22` (Debug drawer reachable from the Hub, raised above every overlay including the search palette; see 41.10–41.11) → `V1_23` (flip buttons show a "loading" state around their otherwise-unbreakable synchronous operation, one-undo-step behaviour preserved; see 41.12) → `V1_24` (flip/undo bug root-caused but explicitly deprioritized, ImageLayer/PixelLayer collapse scoped and planned, `work`→`runOperation` rename, overall roadmap/priority order and hard plan-expiry deadline recorded; see sections 42–43) → `V1_25` (flip/undo bug's true root cause found and FIXED — `window.ImageLayer` was never actually being set, a `class`-vs-`window` misconception corrected from an earlier session; static build-version display added; see 44.1–44.2) → `V1_26` (permanent flip-button response timing via `traceLog`, an active "PRINT VERSION" Debug-drawer button, two new bugs investigated and explicitly held — Portrait tile isolation not blocking input, Resize-Cancel not exiting the project; see 44.3–44.4) → `V1_27` (Portrait tile isolation now actually blocks drawing outside the isolated tile, fixed at the true low-level choke point `PixelLayer.plot()` rather than any of the higher-level wrapper functions that turned out to bypass each other; see the Bugs Squashed companion doc entry 1.1 and danger-zones section 30) → `V1_28` (New Canvas sheet hint text removed entirely, pixel-cursor now also respects Portrait tile isolation via a shared boundary-check function, flip's loading-state UI removed and `runWithLoadingButtonState` marked stale rather than deleted, and a second real undo bug found and fixed — `PixelLayer.setPixelData()`'s bulk property reassignment silently bypassed Proxy-based undo-capture entirely, affecting flip *and* both "clear layer" paths on any small canvas; confirmed dead-code sweep clean; see Bugs Squashed entries 1.2–1.3 and danger-zones section 30).

**No new numbered build after `V1_28` yet.** This update is documentation-only: section 42.2's `ImageLayer`/`PixelLayer` question was resolved from "collapse, not started" to "declined a full collapse; decided on the narrower Option B (remove `PixelLayer`'s Proxy, keep both classes)" -- based on a follow-up benchmark isolating the Proxy's cost from the array-of-arrays shape's own cost. Option C was explicitly declined outright; Option D was reserved specifically for the future vector-layer/spline-editing undo system, contingent on that feature being approved, not for this. See section 42.2 for the full updated writeup. B itself has not been implemented yet -- this session only locked the decision, it did not start the work.

The older V1–V13 builds remain useful as **historical regression references**. They are not automatically valid development bases.

### Current rendering direction

The project now separates the following concepts:

```text
Document state
      ↓
Renderer invalidation
      ↓
Canvas 2D rendering
      ↓
Camera presentation
      ↓
Screen
```

Document state remains authoritative. Zooming, panning, and rotating the view are camera/presentation operations and should not become document edits, undo entries, or reasons to rebuild the entire document layout.

### Current camera work

`V1_3_camera` introduced a presentation camera for two-finger canvas interaction.

`V1_4_camera` restores the two-finger twist rotation that regressed in `V1_3_camera`.

`V1_6` fixed a pinch-zoom centering bug: zoom was anchoring on the canvas center instead of the finger midpoint. See section 36 for the root cause and fix.

The intended two-finger gesture is:

```text
two-finger midpoint movement → pan
two-finger distance change   → zoom
two-finger angle change      → rotation
```

These values should change continuously while the gesture is active. Normal zoom/rotation snapping, if retained, should occur on release rather than repeatedly during the gesture.

### Important limitation

The camera architecture is **not yet considered completely finished**.

Some older layout-based scaling still exists. The long-term goal is to keep camera scale/pan/rotation separate from document dimensions and avoid unnecessary `layoutAll()` work during camera-only interaction.

### Large-canvas crash investigation

A major motivation for the camera architecture was a browser-tab refresh/crash observed while using the Wand tool on a roughly **1.017-million-pixel canvas** and then pinching to zoom out.

The intended behaviour build did not reproduce the crash.

The working architectural hypothesis is that camera-only interaction should not repeatedly resize/re-layout the large document while fingers are moving.

**Update (V1_7, iOS Brave):** re-tested — Wand tool on a ~1.017-million-pixel canvas, then pinch-to-zoom-out. No crash/tab-refresh observed. This is one confirmed data point supporting the architectural hypothesis above, on the specific browser the original crash was most concerning for. Still not yet tested on iOS Safari, and a single clean run doesn't rule out a timing-dependent or memory-pressure-dependent recurrence — treat as encouraging, not closed.

### Portrait opacity overlay root cause

A previous Portrait opacity-view bug was traced to lazy DOM initialization, not merely renderer invalidation.

`#portraitTileIsolationOverlay` is lazily created. Four canvas-activation paths created it, but the image-import activation path did not.

`updatePortraitTileOverlay()` safely returned when the element was missing, so the update silently became a no-op.

Leaving and re-entering the canvas appeared to fix the problem because re-entry used an activation path that created the missing element.

Rule:

> Every path that can make a canvas active, including image import, must guarantee that the Portrait isolation overlay exists before attempting to update it.

This is a concrete regression reference and should not be “fixed” by adding unrelated renderer rebuilds.

### Portrait opacity slider

V11 remains the historical clean reference **for the Portrait opacity slider only**.

Do not use V11 as a general development base. Restore only the specific slider behaviour when necessary.


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

## 3. Rendering architecture: Canvas 2D and camera presentation

The fundamental Canvas 2D setup is:

``` js
this.el = document.createElement('canvas');
this.ctx = this.el.getContext('2d');
```

Canvas 2D is the only rendering path for every raster layer type, at every canvas size. A WebGL2 image renderer previously existed for the large-canvas (`ImageLayer`, >999px) tier and was removed entirely in `V1_21_wip` after investigation found its shader did nothing WebGL is actually good at (a plain, unfiltered texture sample -- no blending/filtering work), and that WebGL2 contexts measurably cost more memory than Canvas2D for the same canvas dimensions, with a documented iOS Safari memory-leak-on-resize risk -- the opposite of the crash-safety property it had been assumed to provide. See section 41.7 for the full investigation. `ImageLayer` and `PixelLayer` remain two separate classes -- a full collapse into one was considered and declined; see section 42.2 for the narrower, decided fix (removing `PixelLayer`'s Proxy-based change tracking specifically, keeping both classes and both data shapes as they are).

The renderer is not the authoritative artwork storage.

The current architecture should be understood as:

- Pixel Art → `PixelLayer` / Canvas 2D.
- Image/Photo → `ImageLayer` with CPU-side editable image data, rendered via Canvas 2D (`Canvas2DImageRenderer`).
- Camera → presentation transform applied after rendering.

The goal is to keep document state, rendering, and camera presentation separate.

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

The editor has **three** user-facing canvas profiles, selectable from the New Canvas sheet's profile buttons:

**Pixel Art \| Portrait \| Sprite**

A fourth, older concept -- **Photo** -- is not a live, selectable profile. `selectProfile()` coerces both `'photo'` and the older `'standard'` name into `'pixelArt'` immediately on entry (`if (p === 'standard' || p === 'photo') p = 'pixelArt';`), and the New Canvas sheet only ever renders three profile buttons (`pixelArt`, `portrait`, `sprite` -- confirmed directly against the markup, not assumed). Treat `'photo'`/`'standard'` purely as legacy internal aliases that get normalized away, not as a real fourth profile a person can actually choose. This corrects an earlier version of this section that described Photo as a real, distinct profile with its own conceptual space -- that description was aspirational/historical, not accurate to any recent build.

### Pixel Art

Pixel Art is the **default profile**.

It remains optimized around explicit pixel-art data and the existing
pixel-layer architecture.

The current conceptual boundary is:

-   Pixel Art canvases whose width **and** height are both ≤999px use `PixelLayer` (an explicit, per-cell pixel array).
-   Any canvas where either dimension exceeds 999px uses `ImageLayer` (a CPU-side `ImageData` buffer) instead, still under the Pixel Art profile -- this is not a separate "Photo" profile, just a different internal data representation chosen automatically by size. See `IMAGE_MODE_MAX_DIMENSION` (=999) and `shouldUseImageMode()`.

The 999 px rule is a data-representation distinction (which layer class gets used), not a profile distinction and not merely a browser safety limit. `ImageLayer` was previously paired with a WebGL2 renderer option; that renderer was investigated and removed entirely (section 41.7) once found to provide no real benefit -- Canvas2D is the only renderer for both layer classes now (section 3). A full collapse of `PixelLayer`/`ImageLayer` into one class was considered and declined -- see section 42.2 for the narrower, decided fix (`PixelLayer`'s Proxy-based change tracking is being removed, but both classes and both data shapes stay as they are).

**Real dimension ceiling, as of the current code:** canvas width/height (new-canvas creation and resize) are both clamped to **1–2000px** uniformly, regardless of profile or which layer class a given size will end up using -- see the number-picker and resize-sheet clamps (`Math.max(1, Math.min(2000, ...))`). There is no separate, larger ceiling for big canvases; 2000 is the real number enforced right now. A `4096` constant does exist elsewhere in the file, but it governs a `ReferenceLayer`'s on-screen rendering resolution cap (avoiding wasted pixels past ~2x the source image's zoom, and staying under real mobile canvas-size limits) -- an unrelated, rendering-only concern, not a canvas-creation dimension limit for any profile.

**Planned, not yet implemented:** raising the real creation/resize ceiling to **4096×4096** is a person-confirmed stretch goal (per section 43.2's tier list). This is a genuine change to the 2000px clamps above, not something already true of the current code -- when this is picked up, update the two `Math.min(2000, ...)` clamp sites (the number-picker and the resize sheet) together, and re-check the `ReferenceLayer` rendering cap noted above, since it already uses the number `4096` for an unrelated purpose and the two should not be conflated or accidentally merged into one constant without checking both call sites still make sense at the new value.

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

Portrait tile isolation (dimming all but the active tile) genuinely blocks drawing outside the isolated tile as of `V1_27`/`V1_28` -- both the actual pixel write (`PixelLayer.plot()`) and the cursor preview (`updateCursor()`) share one boundary-check function, `isPointOutsidePortraitIsolation()`. Before `V1_27` this was purely visual and did not block anything -- see the Bugs Squashed companion doc, entries 1.1–1.2, if working on anything touching this area.

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

It should always be **1px**.

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

## 13. The layer tree

The layer tree represents stacking and nesting.

A flattened `layers` collection may exist for compatibility or linear
rendering operations, but it must not become a competing source of
truth.

> **The tree is for hierarchy.**

Future layer operations should modify the tree and then
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

### Engine/algorithm decisions need the process in the core philosophy doc

**See `Pixel_art_app_core_code_philosophy.md` for the full rule.** No engine, data structure, or algorithm in this codebase is authoritative just because it's already implemented — every one should be understood as a decision that was made, not a fact about how the app must work, and any new one (or any proposal to change an existing one) needs real research (including a web search for how comparable tools solve the same problem), a genuine advantages/disadvantages compilation, agreement between the person and Claude, and an explicit check for whether a lighter/faster version exists. The WebGL2 renderer (added on an unverified crash-prevention assumption, later found to cost more memory than the Canvas2D alternative with a real iOS leak risk) and the `PixelLayer` Proxy-based change-tracking (never benchmarked against the alternative until directly asked) are the two concrete cases that motivated writing this rule down explicitly -- both are described in more detail elsewhere in this section and in section 41.7/42.2.

### History ↔ layer tree

History restoration must restore the authoritative layer tree rather
than merely a flattened `layers` array.

### History ↔ selection

Selection restoration must not accidentally clear selection because
another state-changing function happens to run during restoration.

### Profile ↔ import

Import behavior differs by profile. Do not apply Portrait palette rules
to Pixel Art (including large, `ImageLayer`-backed Pixel Art canvases -- "Photo" is not a separate profile, see section 4).

### Tile isolation ↔ layers

Tile isolation's dimming overlay is visual only, and layers remain shared across tiles regardless of isolation state -- isolation does not create separate per-tile layer stacks.

As of `V1_27`, tile isolation *does* block actual drawing outside the isolated tile (fixed in `PixelLayer.plot()` itself -- see the Bugs Squashed companion doc, entry 1.1, for the full investigation). Before that fix, the overlay's `pointer-events: none` styling made it look like it should block input but it never did, for several sessions, before anyone tried drawing across the boundary while isolated. When adding a new drawing tool or a new way to write a pixel, verify it still respects this boundary -- the fix lives in the one true low-level choke point (`PixelLayer.plot()`), not in each tool's own code, so a new tool should inherit the correct behaviour automatically as long as it eventually calls `.plot()` rather than mutating `pixelData` directly.

### Tool UI ↔ drawing engine

Changing a tool label or adding a slider does not automatically change
the drawing algorithm.

### Canvas size ↔ data representation

Changing canvas dimensions must update the authoritative artwork
representation and all derived rendering state together.

### Large images ↔ memory

Never assume a large canvas is cheap merely because Canvas 2D can
display it.

### Undo history ↔ memory budget

`pushUndo()` is capped by both an action count (`MAX_UNDO`) and a byte
budget (`HISTORY_MEMORY_BUDGET`, 64 MiB). `pruneHistoryLimit()` evicts
the *oldest* entries first when either cap is exceeded. A single
large-canvas bucket fill or full-canvas operation can consume a large
fraction of the budget by itself; if other entries already sit ahead of
it, they can be silently pruned first. "Undo doesn't work" reports
should be checked against this before assuming the undo registration
itself is broken — see section 37.1 for a worked example (paint bucket).

### Destructive actions ↔ confirm pattern

Native `window.confirm()` is a known-bad pattern in this codebase — it
was found unreliable on iOS, which is why `makeTapTwiceConfirm()` (and,
as of V1_9, its per-element sibling `elementTapTwiceConfirm()` for
dynamically-rendered buttons with no stable id) exists. Any new
destructive action (delete, clear, discard) must use one of these two
patterns from the start, never `confirm()`. As of `V1_9`, zero native
`confirm()` calls remain anywhere in the codebase — the last three
(single-layer delete, group delete, bulk multi-select delete) were
migrated in section 39.7, following the first two (`confirmWandDelete`,
`deleteSelection`) migrated in section 37.3. If a future change ever
reintroduces `confirm()`, that is a regression, not a stylistic choice.

### DOM-visible state ↔ underlying data array

Any UI that lets the person reorder or edit something by manipulating
the DOM directly (drag-to-reorder, inline editing) needs an explicit
step that writes the result back into whatever data array the DOM was
rendered from — the DOM order/content is not automatically the source
of truth just because it's what the person just interacted with. See
section 38.4's palette drag-reorder bug: reordering worked visually but
was silently discarded on the next re-render because nothing synced the
new DOM order back into `portraitTilePalettes`. When auditing a
feature that claims to "already work," check not just that an edit is
visible on screen, but that it survives whatever re-render/reload path
normally rebuilds that UI from data.

### One-finger pan edge clamp — FIXED in V1_10

Previously flagged here as a known gap: the one-finger Pan-tool drag
(`g.manualPan` in the touch-gesture handler) set
`viewport.scrollLeft`/`scrollTop` directly with no clamping, so a
person could scroll the canvas completely out of view. The fix that
was flagged as ready-to-use — `clampPanScrollWithinEdgeMargin(value,
maxScroll)` (renamed from `clampScrollKeepingPeek` in V1_10) plus its
`MIN_CANVAS_PEEK` constant — is now actually wired into that drag path
(section 40.1a). Kept as a danger-zone entry, retitled, so a future
session that finds `clampPanScrollWithinEdgeMargin` still recognizes
it as intentional, load-bearing code rather than another unused
function to flag again.

### A same-named wrapper is not necessarily the real choke point

When several call sites all need the same guard/behaviour added, find
the actual lowest-level function they all funnel through before
patching each caller individually -- and don't assume a global wrapper
function is that function just because it shares a name with the real
one. Concrete example (Bugs Squashed companion doc, entry 1.1): the
global `plot(x,y)` function looked like the obvious single choke point
for every pixel write in the app, but `applyPixelToolAt`/`blendPixel`
(the actual dispatcher for Pencil/Brush/Soft Brush/Hard Eraser/Soft
Eraser) and `performWandDelete()` both call `layer.plot(...)` --
`PixelLayer`'s own class method -- directly, bypassing the global
wrapper entirely. A fix applied only to the global `plot()` would have
silently missed most of the tools that actually needed it. Trace every
caller of a behaviour you're trying to guard before picking where to
add the guard, rather than assuming the most obviously-named function
is the real destination.

### A Proxy only catches writes that go through it

A `Proxy`-based change-tracking system (e.g. `makeTrackedPixelData`,
which backs `PixelLayer.pixelData` and drives undo-history capture for
every single-pixel write via `plot()`) only fires its `set` trap for
writes that go *through* the Proxy -- `obj[i][j] = x`. A bulk operation
that reassigns the tracked property itself -- `this.pixelData =
someNewStructure` -- silently escapes the Proxy completely, even
though it looks like "the same kind of write" at a glance. Concrete
example (Bugs Squashed companion doc, entry 1.3): `PixelLayer.
setPixelData()` (the method every flip, resize, and clear-layer
operation funnels through) did exactly this, meaning flip/clear on any
small canvas silently recorded zero undo history for a long time
before anyone noticed via a specific flip reproduction. Any future
bulk-replace method built against a Proxy-tracked structure needs its
own explicit before-capture (see `setPixelData()`'s fix for the
pattern) -- it cannot rely on the Proxy to catch it automatically.

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
-   [x] Linear undo/redo direction for memory safety
-   [x] Undo History panel direction
-   [x] Large-image optimization direction for Photo mode

## Progress in the current restoration pass

The following items have now been implemented in the current build, subject to real-device testing:

-   [x] Pencil / Brush / Soft Brush / Hard Eraser / Soft Eraser reference restored.
-   [x] Colour-to-Alpha/background-removal reference restored.
-   [x] Photo / Pixel Art / Portrait / Sprite profile routing restored.
-   [x] Pixel Art uses `PixelLayer`; Photo uses `ImageLayer` rather than the old image-backed PixelLayer workaround.
-   [x] Match a Colour / Colour Match logic intentionally removed from the current build. Do not restore it unless explicitly requested.
-   [x] History changed from retained branching to linear undo/redo for memory safety.
-   [x] Pixel history changed from full-grid snapshots to sparse changed-pixel deltas.
-   [x] History received a byte-based memory budget plus an action-count safeguard.
-   [x] Photo/ImageLayer history changed to 64 × 64 RGBA tile snapshots for localized edits, with full-image snapshots reserved for operations that affect most/all of the image.
-   [x] History uses a single, live-adjustable memory budget (`HISTORY_MEMORY_BUDGET`, section 41.9) shared across all layer types. A separate, larger Photo-specific budget was tried, found to be dead code (never actually checked by the pruning logic — section 41.8), and removed in favour of the single adjustable one.
-   [x] JavaScript syntax checks were run before publishing the latest restoration builds.
-   [x] WebGL2 was investigated for the Image/Photo renderer and then removed entirely (section 41.7) — it provided no benefit its shader wasn't already getting from Canvas2D, and measurably cost more memory with a documented iOS resize-leak risk. Canvas2D is the only rendering path now, for every layer type and canvas size.

Important: these are implementation claims, not a substitute for real-device behavioral testing. In particular, large Photo-mode history and cross-frame behavior still need testing on the target browsers/devices.

## Still requiring careful implementation/testing

-   [ ] Complete verification of every document-mutating operation in
    the history engine
-   [x] Linear undo/redo behavior replaces the previous retained branch-history approach.
-   [ ] Complete verification of undo/redo behavior under all combinations of undo/redo/new edits
-   [x] Canvas resize UI, 3×3 artwork anchoring, built-in numeric keypad, and resize undo transaction implemented; large-image stress testing remains.
-   [ ] Layer reorder history
-   [ ] Full mask semantics
-   [x] Core Colour-to-Alpha implementation restored.
-   [ ] Colour-to-Alpha edge-case verification across layer types and large images
-   [ ] Indexed colour export/import
-   [ ] 3D reference layer
-   [ ] Dockable editor panel system
-   [ ] Animation/timeline system
-   [ ] Full PSD feature preservation
-   [ ] Large Photo-mode stress testing on real iOS/Brave/Safari targets (one specific case — Wand tool + pinch-to-zoom-out on a ~1.017M-pixel canvas, iOS Brave, V1_7 — confirmed no crash; see "Large-canvas crash investigation" above. Broader Photo-mode stress testing, other browsers, and other operations remain open.)
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
10. **Animation/timeline system** — see section 43.3 for the person's actual current spec (spritesheet+XML playback, still pending fuller detail) and section 43.2 for its priority relative to spline editing and gradients.
11. **Full PSD feature preservation**.
12. ~~**Photo renderer architecture** — introduce a renderer abstraction; investigate WebGL2 for Photo mode with Canvas 2D fallback.~~ DONE, and closed in the opposite direction than planned: a WebGL2 renderer abstraction was built, then investigated and removed entirely once found to provide no real benefit and a real memory/leak risk on iOS. See section 41.7. Canvas2D is the only renderer now.
13. **Photo tiling as a rendering/data architecture** — potentially extend the 64 × 64 tile model beyond undo history if profiling shows it improves iOS responsiveness and memory usage.
14. ~~**Memory diagnostics** — expose current raster/history/tile estimates in the debug UI~~ DONE — the Debug drawer's stats readout shows canvas size, rendering mode, undo/redo depth, history memory used vs. budget, and estimated raster memory; the budget itself is live-adjustable via a slider. See section 41.9.
15. **Potential product split** — eventually consider separate Photo Editor and Pixel Art Editor shells while sharing low-level document utilities. Do not split prematurely while core history/profile behavior is still being stabilized. (The person asked about this directly in passing during the ABCD/layer-collapse discussion and it was deliberately parked, not decided either way — no new information since this backlog item was first written.)

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

## 32.2 History branch UI / tree integration — SCRAPPED, but the ORIGINAL REASONING WAS WRONG (see 32.2a)

This section previously described an intended Paint.NET-style branching history tree (undo to an earlier point, edit, and the abandoned future remains available as a clickable branch rather than being destroyed). That direction is **scrapped for now** — but the reason originally given here ("iOS browser memory limitations... retaining every abandoned branch indefinitely is not memory-safe") was investigated and challenged, and does not hold up. See 32.2a for the full finding before treating this as settled.

The current, correct architecture is linear undo/redo (`undoStack`/`redoStack`, `pushUndo()`, `HISTORY_MEMORY_BUDGET`, oldest-entries-evicted-first pruning — see section 30's "Undo history ↔ memory budget" danger-zone entry, section 37.1 for a worked example of this budget's real-world effect, and section 41.9 for the live-adjustable budget slider). Editing after an undo discards the redo stack outright rather than preserving it as a branch. This has already shipped and is reflected elsewhere in this handoff (see the "Still requiring careful implementation/testing" checklist: "Linear undo/redo behavior replaces the previous retained branch-history approach").

**Do not resurrect the branching-tree design without reading 32.2a first.** The old build referenced in "Historical Regression References" (`Pixel_art_app_bucket_projectname_colourtool_fix_2_html.txt`) still has a working branching implementation and is a legitimate reference if this is revisited -- but the actual cost driver needs to be measured against *this* build's current entry-size model, not assumed from the old build's memory behaviour or from "iOS = must be linear."

## 32.2a Independent challenge to the "branching = memory-unsafe" reasoning

The person asked for this reasoning to be checked against real-world practice rather than taken on faith, since it had never actually been tested -- only asserted, based on the old build (32.2) running into memory trouble under iOS constraints.

**First pass (web search on pixel art / vector / large-canvas editors) seemed to confirm the original claim:** Piskel (the closest real comparable to this app) uses linear history with a hybrid snapshot+replay strategy explicitly chosen for memory efficiency. Every small/lightweight pixel art tool found (PixelCraft, several itch.io/DEV Community examples) uses a plain linear undo stack with a capped step count. Every vector/SVG editor found describes plain linear undo/redo, discarding the redo stack on a new edit after undoing -- structurally identical to this build's own `discardRedoHistory()`. Branching itself only turned up in text editors (Helix, Vim's `undotree` plugin), where it was framed as an optional, advanced feature layered on top of a linear default.

**Second pass (specifically Photoshop, the most relevant serious raster+layers comparable) toppled that conclusion.** Photoshop has offered non-linear (branching) history since Photoshop 5, as a standard, well-documented, opt-in toggle ("Allow Non-Linear History") -- not a rare or experimental feature. Multiple independent sources describing its actual memory cost make the real driver explicit: *"every history state consumes RAM... on a large, multi-layer composite, a single history state can be several hundred megabytes"* and performance guides recommend capping history states hard (as low as 10) specifically on lower-RAM systems. Critically, **this cost applies identically whether Photoshop's history is in linear or non-linear mode** -- the expense comes from each state being a large, retained snapshot, not from the tree topology connecting those snapshots. A linear history storing full-size snapshots is exactly as memory-hungry as a branching one storing the same snapshots; pruning old *linear* entries only helps because it discards snapshots, and pruning old *branches* would help by exactly the same mechanism, for exactly the same reason.

**The actual, corrected conclusion:** the original reasoning conflated two different things -- "the old build's specific implementation was memory-heavy" and "branching history is inherently memory-heavy." The evidence supports the first, not the second. What actually drives memory cost, in every source found (Photoshop's own performance guidance, this build's own `estimateHistoryEntryBytes()` and section 41.8's math showing ~8 MiB for a full-canvas `imageFull` edit), is **the size of what's stored per history entry**, not whether those entries form a stack or a tree. A tree only adds cheap parent/child pointers on top of the same entries a linear stack would store; if this build's per-entry cost is already kept small (sparse pixel diffs, tile-based image diffs -- see section 30's "Undo history ↔ memory budget" entry), a branching structure over the *same* entries would not automatically reintroduce the crash risk the original 32.2 blamed on branching per se.

**What this does and doesn't change, practically:**
- This does **not** mean branching should be added back now. Linear history remains the current, correct, shipped architecture, and re-adding branching is still out of scope unless explicitly requested -- this finding only corrects the *reasoning*, not the *decision*.
- It **does** mean a future session revisiting this topic should evaluate branching on its actual merits (entry size, pruning strategy, real memory measurement against this build's current per-entry costs) rather than dismissing it on the "iOS can't handle trees" reasoning recorded in the original 32.2, which was never actually verified and does not survive scrutiny against how a comparable professional tool (Photoshop) handles the same tradeoff.
- The old build in "Historical Regression References" remains useful precisely because it has a working (if memory-heavy, full-snapshot-per-node) branching implementation to study, should this be revisited -- see that entry for specifics on what to port over carefully versus what not to (its clone-per-edit undo shape does not scale to a large canvas either way, tree or no tree).

## 32.2b Feasibility check against the current codebase and the person's actual goals (V1_26)

Requested directly by the person: is restoring branching history actually feasible right now, checked against both the real current code and the roadmap (section 43.2), not just in the abstract.

**Technically, more feasible than when 32.2/32.2a were first written.** The tree-node infrastructure was never fully torn out during the linear-history migration -- `historyRoot`/`historyCurrent` nodes still carry real `.parent`/`.children` links, and a working `detachHistoryNode()` function already exists and correctly unlinks a node from its parent/children. The only thing forcing strictly linear behaviour is `discardRedoHistory()` running on every new edit after an undo. Separately, `estimateHistoryEntryBytes()` confirms every entry type (`imageTiles`, `imageFull`, `pixels`, `canvasResize`) is already stored in the sparse/tile-diff shape 32.2a argued a real branching implementation would need to avoid reintroducing the old memory problem -- that prerequisite is already satisfied by the current code, not something that would need to be built first.

**Against the person's actual goal list (section 43.2), it does not clear the bar for being done now.** None of the three set goals (sprite animation workflow, spline editing, adjustable gradients) require branching history to function -- they need *an* undo system, and any of the linear options already discussed (A/B/C/D, section 42.2/45+) satisfy that. Nothing on the goal list depends on "recover an abandoned branch after undoing and editing again."

**Against the September 14 deadline (section 43.1):** real, non-trivial remaining scope even with the backend prerequisite already met -- a branch-navigation UI would need to be built (the old build's own UI, or something like Photoshop's non-linear history panel, both require real interface work, not just backend logic), plus testing that undo/redo/branch-navigation don't interact badly with the sparse-diff replay logic in some new way branching would introduce. That's real session-days competing directly against the three set goals for the same limited budget.

**Conclusion, recorded as the actual decision:** feasible, genuinely more so than previously assumed, but **deprioritized** -- not blocking or blocked by anything currently on the roadmap. Revisit after the three set goals are addressed, not before. This is the same category of finding as the `PixelLayer` Proxy-removal comparison against the goal list (section 42.2): good, real, unblocked-by-nothing hygiene work that should sit in the backlog rather than compete with what actually needs to ship.

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

As of `V1_8_portraits`, this list of concepts is still accurate, but several are now mode-conditional rather than unconditionally present — see section 38.3 for the `hiddenWhen`/function-valued-`name` mechanism that makes Brush, Soft Brush, Soft Eraser, and Colour to Alpha unsearchable in Portrait mode, and Hard Eraser display as plain "Eraser" there.

## 32.7 Old Wand feather algorithm

The old feather implementation is intentionally **excluded** from restoration.

Do not silently reintroduce it unless the user explicitly requests it again.

------------------------------------------------------------------------

# Historical Regression References

These builds are references for specific behaviour only. They must not automatically become the base for new development.

- **V11** — clean historical reference for the Portrait opacity slider.
- **V12** — renderer invalidation architecture reference.
- **V13** — V12-based Portrait opacity slider restoration.
- **`Pixel_art_app_bucket_projectname_colourtool_fix_2_html.txt`** — the last build before the `ImageLayer`/WebGL2 split existed at all (no `ImageLayer` class, zero WebGL references anywhere; `PixelLayer` was the only raster layer type, handling every canvas size itself). Uploaded during the section 42.2 investigation as a candidate reference for what was originally a full `ImageLayer`/`PixelLayer` collapse — that collapse was later declined in favour of the narrower "Option B" (section 42.2), so this build is now most relevant for its explicit, non-Proxy undo-capture pattern specifically, not as a template for a merge that isn't happening. Specific findings:
  - `beginEdit()`/`commitEdit()` here is **type-agnostic**: one entry shape (`type:'pixels'`, full before/after `cloneGrid(layer.pixelData)` clone) for every pixel edit, gated only by `isPixelLike(layer)`. This is a clean historical example of exactly the "one undo-capture shape regardless of layer type" model section 42.2 is aiming to get back to -- but its full-grid-clone-per-edit approach does not scale to a large (e.g. 1408×768) canvas the way the current build's sparse/Proxy-based tracking does, so it should inform the *shape* of a fix, not be ported over wholesale.
  - History pruning here (`pruneHistoryLimit()`, `MAX_UNDO`) is purely **action-count-based**, with no byte-memory budget concept at all -- a materially simpler and different safety model than the current `HISTORY_MEMORY_BUDGET` system (section 41.9).
  - It already had a **live, user-facing dropdown to change the undo limit** (`[40,100,250,500,1000]`, immediately re-pruning and re-rendering on change) -- a real precedent for exactly the kind of user-adjustable-limit UI later rebuilt as the History Memory Budget slider (section 41.9), though the earlier version tuned action count rather than memory bytes.
  - This build still has the **branching-history tree** (redo path explicitly retained in the tree on a new edit from an older state, per its own code comment), predating the deliberate scrap-and-replace with linear undo/redo documented in section 32.2. Its branching model is not something to revert to as-is (its full-grid-clone-per-node storage doesn't scale to a large canvas, tree or no tree), but section 32.2's *original reasoning* for scrapping branching ("iOS memory limits" as an inherent property of trees) was later independently challenged and did not hold up -- see section 32.2a. This old build is therefore a legitimate reference for branching-history mechanics specifically, should that be revisited, once paired with the current build's already-efficient per-entry sparse/tile-diff storage instead of this build's full clones.
  - No targeted bug-hunt has been done on this file; if one is wanted later, it's a separate task from the architecture comparison recorded here.
- **Claude `Pixel art app v1_3.html`** — latest base supplied before the camera architecture work.
- **V1_3_camera** — first camera-based pinch/pan implementation.
- **V1_4_camera** — camera pinch/pan plus restored two-finger twist rotation.
- **`Pixel_art_app_V1.html`** — reference for the pre-camera-architecture era. Notable for two things: (1) its two-finger pan/zoom/rotate anchoring was correctly centered on the pinch midpoint, even though the gesture itself was not smooth/fluid (see section 36 — do not replicate the non-smooth feel, only the anchoring principle); (2) it used the native `window.confirm()` dialog for destructive actions, which is why wand/selection delete worked there but not in V1_5. `confirm()` was later found unreliable on iOS; every remaining call site was migrated to the app's own tap-twice confirm pattern across sections 37.3 and 39.7, and as of `V1_9` zero native `confirm()` calls remain anywhere in the codebase.
- **V1_5** — camera architecture continued from V1_4_camera; introduced the Debug System (section 35). Had the pinch-zoom centering bug fixed in V1_6.
- **V1_6** — fixes the V1_5 pinch-zoom centering bug (section 36). Base for the V1_7 fix/feature pass.
- **V1_7** — eight-item fix/feature pass (section 37): move-layer/group history labels, tap-twice confirm for wand/rect-selection delete, selection persistence across project switches, Portrait tile-isolation lock (later superseded -- see section 38.4), hiding/auto-fallback for Portrait-invalid tools, tile-boundary stroke clipping. Base for `V1_8_portraits`.
- **V1_8_portraits** — Portrait-mode search filtering, per-tile palette drag-reorder/export fixes, tile-isolation freeze replacing the old separate lock button (section 38). Base for `V1_9`.
- **V1_9** — colour/tool-selection UX fixes, full `confirm()` → tap-twice migration (zero native `confirm()` calls remain from this point on), first major dead-code sweep (section 39). Base for `V1_10`.
- **V1_10** — fit-to-screen on new/opened canvas, one-finger pan edge clamp, function-naming cleanup pass (section 40). Base for `V1_21_wip`.
- **`V1_21_wip`** — structural-reorganization prep: two-purpose image-import function split, WebGL2 image renderer removed entirely, adjustable history-memory budget added (section 41). Not a numbered release build. Base for `V1_22`.
- **V1_22** — Debug drawer made reachable from the Hub and raised above every overlay including the search palette (section 41.10–41.11). Base for `V1_23`.
- **V1_23** — flip buttons gained a "loading" state around their fully-synchronous operation (section 41.12). Base for `V1_24`.
- **V1_24** — documentation/small-rename session; the flip/undo bug was root-caused but the fix deliberately deferred at the time (section 42). Base for `V1_25`.
- **V1_25** — the flip/undo bug's actual fix: `window.ImageLayer = ImageLayer;` added, correcting a wrong assumption from an earlier session that `class` declarations attach to `window` automatically (section 44.1). Static build-version display added. Base for `V1_26`.

Use an older build only to recover or compare a specific known behaviour. `V1_26` is the current build -- see "Current Build Status" at the top of this document, which is the authoritative pointer and should always be checked rather than assumed from this list, since this list can lag a session or two behind.

------------------------------------------------------------------------

## Optimisation and Regression Rules

- Do not perform broad architectural cleanup while fixing a single feature unless explicitly requested.
- Do not replace a working system with a simplified demonstration.
- Camera-only changes must not become document edits, history entries, or unnecessary full document renders.
- Historical builds are references, not automatic replacement codebases.
- When a regression has a known root cause, fix the root cause rather than adding unrelated refresh/rebuild behaviour.
- Preserve existing features unless the requested change explicitly supersedes them.

------------------------------------------------------------------------

# 33. Regression-Prevention Procedure

Before producing another build:

1. Start from the current build named in "Current Build Status" above (currently `Pixel_art_app_V1_26.html`).
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
13. When a bug is found and fixed, write its full narrative in the companion `Pixel_art_app_bugs_squashed_V1.md` document, not in this document's chronological sections — see the note near the top of this file. If the bug teaches a durable lesson, add that lesson to section 30 here, with a pointer to the companion file's entry for the full story.

A feature is not considered implemented merely because:

- a button exists,
- CSS exists,
- a class exists,
- a function has the expected name,
- or the debug menu displays a mode.

> **Trace the actual state mutation, rendering, and history path before declaring a feature restored.**

**Why this procedure exists:** the regressions this procedure guards against are properties of this specific codebase's history across many sessions (dead code accumulating, comments drifting out of sync with the code they describe, features silently superseded without their older version being removed) — not a claim about any particular AI tool's general reliability. The person maintaining this project has noted, as their own observation rather than a verified comparison, that they have not personally experienced this kind of regression using Claude the way they describe having seen with ChatGPT's free tier; that's recorded here as their impression, not as an externally confirmed fact, and should be treated as anecdotal context rather than a citable claim.

------------------------------------------------------------------------

# 34. Handoff Build Selection

For a new development chat, provide:

1. The **latest explicitly designated build** — current source of truth.
2. This updated handoff `.md` — architecture, regression notes, restoration requirements, **and code documentation** for the systems it describes (Debug System, camera/pinch-zoom, Portrait-mode tool rules, etc.). It is not purely a disposable summary; treat sections that describe named functions/variables as living documentation of the current build, not just prior-session notes.
3. Historical reference builds only when a specific missing implementation needs investigation.

Do not hand over every intermediate build unless investigating a particular regression.

The next chat must preserve the rule:

> **The latest explicitly designated build is authoritative; historical builds are reference material, not replacement codebases.**


## Build naming convention

Starting with the next published build, HTML deliverables use the short versioned naming scheme:

- `Pixel_art_app.html.txt` — base/unversioned name when appropriate.
- `Pixel_art_app_V1.html.txt`
- `Pixel_art_app_V2.html.txt`
- and so on, incrementing the version number for each subsequent published build.

In practice, the camera-architecture branch has instead used `V1_4_camera` → `V1_5` → `V1_6` → `V1_7` → `V1_8_portraits` → `V1_9` → `V1_10` → `V1_21_wip` → `V1_22` → `V1_23`, i.e. plain incrementing numbers (plus an occasional descriptive suffix, e.g. `_portraits`, `_wip`) off the `V1_x` lineage rather than a fresh `V1`/`V2`/... sequence, with a deliberate jump from `V1_10` to `V1_21` for the person's planned large structural reorganization (section 41). Treat "Current Build Status" at the top of this handoff as the actual source of truth for the current filename; this section describes the intended scheme, not a guarantee of what any given past build was actually named.

Avoid embedding long lists of restored features or implementation details in the filename. Those details belong in this handoff/readme.

### Hub UI cleanup

The four profile buttons that were previously displayed in the **Pixel Art Hub header** (Photo, Pixel Art, Portrait, Sprite) were removed because the profile selection belongs in the New Canvas flow. The profile buttons inside the New Canvas sheet remain.

------------------------------------------------------------------------

# 35. Debug System

The app has a built-in Debug drawer (right-side edge-swipe drawer, `#debugDrawer`, opened via the ⚙️ DEBUG tab or a right-edge swipe) plus a matching JS capture layer installed near the top of the script, before anything else runs, so it can catch errors from later code.

## 35.1 Debug drawer UI

`#debugDrawer` has two parts:

- `#debugDrawerControls` -- sticky header containing the stats readout and all toggle buttons.
- `#debugLog` -- scrollable log output below it.

Controls, top to bottom:

- **REFRESH STATS** -- re-runs `refreshDebugStats()`.
- **UNRESTRICTED VECTOR** (`debugVectorToggleBtn`) -- calls `toggleDebugUnrestrictedVector()`.
- **FORCE BUILT-IN KEYBOARD** (`forceKeyboardToggleBtn`) -- calls `toggleForceCustomKeyboard()`.
- **TOUCH / LOGS / TRACE** (`logToggle-touch`, `logToggle-js`, `logToggle-trace`) -- three independent capture switches via `setLogToggle(kind, on)`.
- **COPY LOG** (`exportLogBtn`) -- calls `exportLogToClipboard()`.
- **CLEAR LOG** -- calls `clearDebugLog()`.

## 35.2 Stats readout (`refreshDebugStats`)

Populates `#debugStats` with, in order: Profile, Canvas dimensions, Rendering mode label, Zoom, Frame count (with active frame index), Layer count (current frame vs. all frames), Undo/Redo stack depth, estimated raster memory in MB, and `devicePixelRatio`.

Memory is Claude's own tally via `estimateMemoryBytes()` (sums `gridW * gridH * 4` bytes across pixel/image/mask/clip layers, plus `naturalWidth * naturalHeight * 4` for image-backed layers) -- **not** a browser memory API, since iOS/WebKit exposes none.

## 35.3 Log capture (`debugLogEntries`)

A single in-memory array, capped at 300 entries (oldest dropped first via `.shift()`), rendered into `#debugLog` by `renderDebugLog()`. Each entry is `{ kind, category, msg, t }`:

- `kind`: `'log' | 'warn' | 'error'` -- governs colour (`log-error`, `log-warn`).
- `category`: `'touch' | 'js' | 'trace'` -- governs colour (`log-touch`, `log-trace`) and which toggle gates it.
- `t`: `HH:MM:SS` timestamp.

Three independent capture switches, **all default off** -- diagnostic tools meant to be turned on only while actively chasing a bug, not left running:

| Switch | Variable | Captures |
|---|---|---|
| TOUCH | `logTouchEnabled` | Every `touchstart`/`click` anywhere on screen, with coordinates and the hit element (via capture-phase listeners + `document.elementFromPoint`, so `stopPropagation()` downstream can't hide it). Very chatty. |
| LOGS | `logJsEnabled` | `console.warn`/`console.error` calls (patched at startup) plus uncaught `error`/`unhandledrejection` window events. Real problems. |
| TRACE | `logTraceEnabled` | UI action tracing sprinkled through button handlers via `traceLog(...)`, e.g. "togglePanel(layers) called" -- for "why didn't my tap do anything" bugs, distinct from genuine JS errors. |

`traceLog()` always forwards to the real browser devtools console via `console.debug` regardless of the TRACE toggle, since a real console doesn't have the small-screen clutter problem the in-app log does. Only the in-app copy is gated by `logTraceEnabled`.

`describeEl(el)` renders any DOM element as a short `TAG#id.class` string for log readability. `escapeHtml(s)` escapes `&`, `<`, `>` before entries are injected into `#debugLog` as HTML.

`exportLogToClipboard()` joins all entries as `[time] [kind/category] msg` lines and writes them to the clipboard, with a `\u2705 COPIED!` / `\u274C FAILED` button-label flash.

## 35.4 Debug-only behaviour toggles

Two toggles change actual runtime behaviour rather than just logging:

- **`debugUnrestrictedVector`** (`toggleDebugUnrestrictedVector()`) -- switches vector layers between the normal pixel-snapped rendering and the old smooth/display-resolution rendering, for visual comparison. Triggers `layoutCSS()` on every vector layer in every frame when toggled.
- **`forceCustomKeyboard`** (`toggleForceCustomKeyboard()`) -- forces the custom on-screen keyboard to appear even on a non-touch desktop device, so it can be tested without a touch screen.

## 35.5 Error-path integration

Several user-facing failure alerts (add vector layer, add layer, add reference layer, import image, return to gallery) point the user at the Debug tab for details ("check the Debug tab for details") rather than exposing a raw stack trace, since the Debug drawer's LOGS capture is where the underlying `console.error`/exception would have landed if enabled.

## 35.6 Rule

The Debug system is diagnostic infrastructure, not a feature to casually extend or strip down. When adding new debug-only behaviour, follow the existing pattern: a module-level boolean flag, a toggle function that flips it and syncs a button's `active` class, and (if it affects rendering) an explicit re-layout call rather than waiting for the next natural render.

------------------------------------------------------------------------

# 36. Pinch-Zoom Centering Fix (V1_6)

## 36.1 The bug

In V1_5, pinching to zoom in/out was anchored on the canvas center instead of the finger midpoint. Rotation was unaffected (it correctly anchored), only scale/pan drifted.

## 36.2 Root cause

`applyCameraTransform()` sets `container.style.transform` with `transform-origin: center center` and applies `scale(cameraScale)`. `updateCanvasPanZoomRotate()` only tracked the pinch midpoint's screen-space *translation*:

```js
cameraPanX = startPanX + (m.x - startMidX);
cameraPanY = startPanY + (m.y - startMidY);
```

This ignores that scaling around a fixed transform-origin moves every point radially away from (or toward) that origin, proportional to `(cameraScale - 1)`. The anchor point under the fingers at gesture start drifts away from the fingers as scale changes, because nothing compensated for the scale-induced shift. Rotation was unaffected because the old code's rotation term was independent of this pan math.

## 36.3 The fix

`startTwoFingerGesture()` now captures the pinch midpoint's offset from the container's **untransformed** center, in local (unscaled, unrotated) container-space (`localOffX`, `localOffY`), by inverting the transform at gesture start:

```js
const r = container.getBoundingClientRect();
const centerX = r.left + r.width / 2, centerY = r.top + r.height / 2;
const dx = m.x - centerX, dy = m.y - centerY;
const rad = -cameraRotation * Math.PI / 180;
const localOffX = (dx * Math.cos(rad) - dy * Math.sin(rad)) / cameraScale;
const localOffY = (dx * Math.sin(rad) + dy * Math.cos(rad)) / cameraScale;
```

On every move, `updateCanvasPanZoomRotate()` re-solves `cameraPanX`/`cameraPanY` so that same local point, after applying the *new* scale and rotation, lands back exactly under the current pinch midpoint, solved inline rather than via a separate coordinate-transform helper (see 36.4 for why there is no such helper as of V1_9).

The container's own bounding-rect center is stable through the gesture (no `layoutAll()` runs mid-gesture), so this has no per-frame drift.

## 36.4 `gridToScreenClient` removed in V1_9

`gridToScreenClient(gx, gy)` (grid-space → screen-space, the inverse of `getPosFromClient`) was a documented coordinate helper with zero call sites as of V1_6/V1_7/V1_8_portraits — the 36.3 fix solves the pan offset inline instead of round-tripping through it, and nothing else ever called it either. It was kept through V1_8_portraits as "the documented inverse of `getPosFromClient`, for future use," but was explicitly requested for removal and deleted in `V1_9`, along with the one remaining comment elsewhere that referenced it by name.

`getPosFromClient(cx, cy)` itself (screen-space → grid-space) is unaffected and remains heavily used throughout the coordinate/gesture system — only its now-removed inverse was ever unused. If a future feature needs "where does this grid point land on screen right now," it will need to be re-derived (the math is straightforward and is preserved in this section's `updateCanvasPanZoomRotate` excerpt above, which does the same transform inline for a single point).

## 36.5 What was deliberately not changed

The live pinch remains fluid/continuous while fingers move (no per-frame snapping), matching V1_5's design. `Pixel_art_app_V1.html` anchors correctly but is not smooth/fluid during the gesture — its non-smooth feel was explicitly excluded from this fix; only its anchoring *principle* (keep a fixed grid point under the fingers) was ported over, adapted from V1's scroll-based (`scrollLeft`/`scrollTop`) approach to V1_5's CSS-transform-based camera.

------------------------------------------------------------------------

# 37. V1_7 Fix/Feature Pass

Eight items addressed in one pass, based on `V1_6`. Numbered to match the original request list for traceability.

## 37.1 Paint bucket undo — investigated, not a code bug

Traced the full path: `startStroke()` → `beginEdit()` → bucket fill (global or contiguous flood-fill) → `plot()` → the tracked-pixel-data `Proxy` captures before-values into `layer._historyCapture` → stroke end → `commitEdit()` diffs and calls `pushUndo()`. This is correctly wired for both bucket-fill modes.

The actual explanation is the in-app memory budget: `pushUndo()` enforces `HISTORY_MEMORY_BUDGET` (64 MiB) via `pruneHistoryLimit()`, which evicts the **oldest** entries first (`undoStack.shift()`) whenever the running total exceeds budget. A single large bucket fill on a near-max canvas (999×999) is roughly 34 MiB by itself (`estimateHistoryEntryBytes()`'s `'pixels'` branch: ~36 bytes/changed-pixel). If history already has other entries when a large fill lands, older strokes can get silently pruned before the fill itself would ever be evicted (since pruning always removes from the front). This can look like "undo doesn't work" when what actually happened is that the entries the user expected to undo *back into* were already evicted.

No code change was made here — the undo registration itself is correct. If this needs to actually change, the options are: raise `HISTORY_MEMORY_BUDGET`, cap bucket-fill undo granularity (e.g. store a tile-diff instead of a full per-pixel change list for very large fills), or warn the user when a fill is about to consume a large fraction of the budget.

## 37.2 "Move item" → "Move layer" / "Move group"

`moveTreeNode()` handles both layer and group nodes (reordering within a tree, including entering/leaving groups). The undo-history label was a blanket `'Move item'`; it's now conditional on `node.kind`: `'Move group'` for group nodes, `'Move layer'` for layer nodes.

## 37.3 Confirm-delete (wand tool, selection tool) not working

Root cause: `confirmWandDelete()` and `deleteSelection()` were the only two destructive actions still using the native `window.confirm()` dialog. Every other destructive action (Clear, Main Menu, Start Fresh) already uses the app's own `makeTapTwiceConfirm()` pattern — built specifically, per an existing in-code comment, because native `confirm()` "proved unreliable on iOS." These two call sites were simply never migrated. This explains why `Pixel_art_app_V1.html` (which predates the tap-twice pattern entirely) still worked: `confirm()` was the only option there and evidently worked in whatever context that build was tested in.

Fix: both converted to `makeTapTwiceConfirm()`, matching the existing pattern.

- New button ids: `wandDeleteBtn`, `deleteSelBtn`.
- New confirm objects: `wandDeleteConfirm`, `rectDeleteConfirm`.
- `confirmWandDelete()` now just triggers the tap-twice confirm; the actual delete logic moved to `performWandDelete()`.
- `deleteSelection()` now triggers `rectDeleteConfirm` for the rect-selection case (it still delegates to `confirmWandDelete()` first when a wand selection is active, unchanged); the actual delete logic moved to `performDeleteSelection()`.

**Rule going forward:** any new destructive action should use `makeTapTwiceConfirm()` from the start. Native `confirm()`/`alert()`-as-confirmation should be treated as a known-bad pattern in this codebase, not just an inconsistency to fix opportunistically.

## 37.4 Selection persisting across projects

`selection` (rect select) was being cleared on project-switch, but `wandSelection`/`wandSelectionCount` (wand/lasso mask) was not — so a wand selection could persist visually into a newly opened or newly created project, potentially at the wrong canvas dimensions.

Fix: added `resetSelectionState()` — clears `wandSelection`, `wandSelectionCount`, `selection`, and `movingSelection` together, resets the Move-Selection button's active state, and refreshes the selection overlay/tools-visibility. Unlike `clearWandSelection()`, it does **not** record a selection-undo entry, since project-teardown/load already calls `resetHistory()` and a stale selection-undo entry pointing at the old document would be meaningless.

Wired into all project-switching entry points:
- `goToMainMenu()`
- `openProjectFromStore()`
- `startNewProjectFromGallery()`
- `startFreshConfirm`'s `onConfirm`
- the import-image-as-new-project flow

## 37.5 Lock for "show other tiles" (Portrait mode)

Previously, `updatePortraitTileOverlay()` always read the live `portraitActiveTileKey`, which `syncPortraitPaletteForPoint()` auto-updates on every draw/tap in a different tile (and on Pan-tool tap in Portrait mode). This meant the isolation view would jump to follow the pointer even when the user just wanted to keep working on one isolated tile.

Fix: added `portraitTileIsolationLocked` (bool) and `portraitIsolationLockedKey` (the pinned tile key, captured at lock-on time). A 🔒 button appears next to the isolate toggle whenever isolation is on. While locked:
- `updatePortraitTileOverlay()` reads `portraitIsolationLockedKey` instead of the live `portraitActiveTileKey`.
- `syncPortraitPaletteForPoint()` still updates the **palette** to follow the pointer as before (so colour-picking convenience is unaffected) but skips the overlay refresh.

Turning isolation off entirely also clears the lock and the pinned key.

## 37.6 Hide soft eraser / size-adjustable brush in Portrait mode

Portrait's 40×40 tiles are too small for size-adjustable/soft brushwork to be a sensible default, and per section 37.7's fallback, those tools are unreachable in Portrait mode anyway — so their buttons and controls are now hidden there rather than left as dead UI.

Hidden via `updateToolVisibility()` when `selectedProfile === 'portrait'`:
- Tool buttons: `#brushToolBtn`, `#softBrushToolBtn`, `#softEraserToolBtn` (all given ids for this purpose; `pencil` and `hardEraser` remain visible).
- Slider rows inside `#pixelToolControls`: `#brushSizeRow`, `#brushSoftnessRow`, `#softEraserSizeRow`, `#softEraserSoftnessRow`.

Also removed a duplicate, unguarded "🖌️ BRUSH" button in the Tools drawer (paired with FILL in its own row) that had the same `data-tool="brush"` as the now Portrait-gated button — it was fully dead/redundant markup with identical behavior to the primary Brush button, and leaving it would have been a second entry point not covered by the new hiding logic.

## 37.7 Auto-redirect invalid tools to nearest equivalent (Portrait mode)

`PORTRAIT_TOOL_FALLBACK` maps each invalid Portrait-mode tool to its fixed-size equivalent:

```js
const PORTRAIT_TOOL_FALLBACK = { brush: 'pencil', softBrush: 'pencil', softEraser: 'hardEraser' };
```

Applied in two places:
- `window.selectPixelTool(n)` — redirects at the point of tool selection, covering every tool-button click (all five pixel tools route through this function via `handleToolBtn`).
- `updateToolVisibility()` — a safety net for entry paths that set `selectedProfile` directly instead of going through a button click (e.g. loading a saved Portrait project while `currentTool` was `brush`). Re-dispatches through `handleToolBtn()` so every other piece of tool-switch bookkeeping (swatch state, cursor, panel visibility) stays in sync, rather than just reassigning `currentTool` directly.

Since only `pencil` and `hardEraser` are reachable in Portrait mode, and both are always single-pixel (`size: 1` in `window.getPixelToolStroke()`), there is no remaining case where a radius-based brush stamp could straddle a tile boundary — relevant to 37.8.

## 37.8 Stroke should stop at 40×40 tile boundaries (Portrait mode)

Bug: dragging a stroke could paint across a tile boundary as long as the drawing colour happened to exist in both tiles' palettes. `plot()`'s existing Portrait check (`if (selectedProfile==='portrait' ...) { ... if(!pal.includes(colour)) return; }`) only blocks by *colour validity in the target tile's palette*, not by *tile membership of the stroke itself* — so a colour shared between adjacent tiles' palettes (a supported, common case — see the palette-per-tile design in the top-level Purpose/Approach sections) could cross freely.

Fix: the stroke's origin tile is captured once, at `startStroke()`, into `g.strokeTileKey` (via `portraitTileKeyForPoint(x, y)`, only when `selectedProfile === 'portrait'`). In `onMove()`'s pixel-tool branch, the `linePixels()` interpolation between the last and current drag point is clipped at the first point that leaves `g.strokeTileKey`, before any of the points are applied:

```js
if (g.strokeTileKey) {
    const cut = pts.findIndex(([px,py]) => portraitTileKeyForPoint(px,py) !== g.strokeTileKey);
    if (cut !== -1) pts = pts.slice(0, cut);
}
```

`g.lastBrushPos` is still updated to the real (unclipped) cursor position every move, so if the user drags back into the origin tile, the line resumes correctly from the actual finger position rather than from the clipped boundary point.

This only needed to guard the line-interpolation/drag path, not a brush-radius stamp, because of 37.7: the only tools reachable in Portrait mode (`pencil`, `hardEraser`) are always single-pixel, so there's no radius-stamp case that could straddle a boundary on a single tap.

## 37.9 Dead code / stale comments removed during this pass

While investigating the above, the following pre-existing issues (not part of the original 8-item list) were found and cleaned up, since they were directly adjacent to code touched in this pass:

- **Duplicate "BRUSH" button** — see 37.6.
- **`gridToScreenClient()` stale comment** — see 36.4 (the function itself was later fully removed in V1_9; this V1_7 entry only covers fixing its outdated comment).
- **`g.panStart`** — dead closure state in the touch-gesture handler's `g` object. Declared and reset to `null` in two places (`startTwoFingerGesture()`, stroke-end teardown) but never read anywhere; a leftover from the pre-camera, scroll-based zoom architecture that `cameraGesture` fully replaced. Removed the declaration and both reset lines.

------------------------------------------------------------------------

# 38. V1_8_portraits Fix/Feature Pass

Five items addressed, based on `V1_7`. Numbered to match the original request list for traceability.

## 38.1 "HARD ERASER" → "ERASER" label in Portrait mode

The visible tool button (`#hardEraserToolBtn`) swaps its text between "🧹 HARD ERASER" (default) and "🧹 ERASER" (Portrait mode) inside `updateToolVisibility()`, alongside the button-hiding logic already there from section 37.6. Label-only — `data-tool`, id, and behaviour are unchanged. Portrait only has one eraser tool reachable at all (soft eraser redirects to it via `PORTRAIT_TOOL_FALLBACK`), so "hard" — a distinction that only matters next to a soft eraser — stops being meaningful there.

The command-palette entry for this tool was deliberately left as a **function**-valued `name` (see 38.3) so the same label logic applies when searching, not just when looking at the button.

## 38.2 Colour to Alpha disabled in Portrait mode

Colour to Alpha bypasses the per-tile curated-palette model by design (it samples arbitrary background colour, not a palette entry), so it doesn't fit Portrait's model at all — unlike brush/soft brush/soft eraser (section 37.7), which fit the model but just need a fixed-size substitute.

It isn't part of `pixelToolDefs`/`window.selectPixelTool`, so it needed its own redirect rather than reusing `PORTRAIT_TOOL_FALLBACK`:

- `handleToolBtn(t)` redirects `t = 'colorToAlpha'` to `t = 'pencil'` when `selectedProfile === 'portrait'`, before the `pixelToolDefs` dispatch.
- `updateToolVisibility()` has the matching safety-net check for entry paths that set `selectedProfile` directly (e.g. loading a saved Portrait project) instead of going through a button click — same pattern as the rest of section 37.7.
- The button (`#colorToAlphaToolBtn`) is hidden in Portrait mode via the same `show()` calls as the other Portrait-hidden controls.

## 38.3 Search results respect Portrait-mode restrictions

New, generic mechanism rather than a one-off patch: `registerCommand(id, name, aliases, action, category, hiddenWhen)` gained an optional sixth parameter. `hiddenWhen` is `() => boolean`; when it returns true, the command is excluded from search results (typed query **and** the empty-query default listing) entirely, not just from the visible button. This is what makes hidden tools genuinely unreachable via search rather than just visually tucked away — search can't become a backdoor around a mode's restrictions.

Applied to every Portrait-hidden tool: `tool.brush`, `tool.softBrush`, `tool.softEraser`, `tool.colorToAlpha`, all gated on `() => selectedProfile === 'portrait'`.

`registerCommand`'s `name` parameter also now accepts a function (`() => string`), resolved at render time in both `buildSearchResults()` and `renderGlobalCommandResults()`. This is what lets `tool.hardEraser`'s search label track the same Portrait-mode rename as the visible button (section 38.1) instead of drifting out of sync with it.

**On search architecture generally:** section 32.6 asks future sessions to recover/extend the existing command-search registry (`registerCommand`/`commandRegistry`/`buildSearchResults`) rather than build a second, competing one. The existing system was checked against that spec and against the Photoshop/Photopea/macOS-Spotlight model the person asked about, and already matches it: ranked fuzzy+prefix+exact scoring, a full-screen dimmed overlay with a top-anchored input (not a centered dialog), live-as-you-type results, and commands combined with layer/group results in one ranked list. `hiddenWhen` and function-valued `name` extend that existing system in place; they are not a new search architecture.

## 38.4 Per-tile palette: audit findings and fixes

The person asked whether the colour palette already auto-adjusts itself per grid/tile. It was thoroughly checked, section by section, against the request:

**Already correctly implemented (no bug found):**
- Palette auto-switches per tile via `syncPortraitPaletteForPoint()`, keyed by `portraitTileKeyForPoint()` (`floor(x/40) + ',' + floor(y/40)`).
- Each tile has its own independent, capped 15-colour array (`PORTRAIT_PALETTE_LIMIT`), stored in `portraitTilePalettes` (a `Map<tileKey, string[]>`).
- Per-tile arrays are saved and restored per-project (`portraitTilePalettes: Object.fromEntries(portraitTilePalettes)` on save, `new Map(Object.entries(...))` on load).

**Two real gaps found and fixed:**

1. **Drag-to-reorder swatches didn't persist.** `setupPaletteDragEvents()`'s drag handler only ever reordered the **DOM** (`pal.insertBefore(...)`); it never wrote the new order back into the underlying tile array. Since `replaceVisiblePalette()` rebuilds the DOM *from* the array on every tile switch and project load, a user's custom ordering was silently discarded the next time the palette re-rendered. Fixed: `onEnd()` now reads the post-drag DOM order and rewrites the active tile's array (`ensurePortraitTilePalette(portraitActiveTileKey)`) to match, filtered against the array's own contents so a stray/foreign swatch element can't inject an invalid entry.

2. **Export only captured the active tile, not all tiles.** `getSwatchArray()`/`exportSwatchArray()` read from `#palette .swatch` — the currently-visible DOM, i.e. one tile. Fixed: in Portrait mode, export now serializes `Object.fromEntries(portraitTilePalettes)` (every tile's array, keyed by tile coordinate) in one JSON file (`portrait-swatches-all-tiles.json`). Import (`applyImportedSwatchArray()`) accepts either that per-tile object shape (writing each tile's array via `ensurePortraitTilePalette`, then refreshing the visible palette from whichever tile is currently active) or a plain flat array (applied to just the active tile, for compatibility with a non-Portrait export). Non-Portrait mode is unaffected — single flat array in, single flat array out, as before.

## 38.5 Palette locked to the isolated tile; opacity range change

Originally (section 37.5) tile isolation had a separate 🔒 lock toggle: isolation-on by itself still let the palette follow the pointer between tiles, and only *additionally* locking pinned the visual overlay. The person's testing showed this wasn't the wanted behaviour — turning the overlay on at all should stop the palette from switching when tapping other tiles, with no separate lock step.

**Fix:** `syncPortraitPaletteForPoint(x, y, force, resetIsolation)` gained a `resetIsolation` parameter (default `false`). When `portraitTileIsolation` is on and `resetIsolation` is not explicitly `true`, the function returns immediately — the active tile, palette, and overlay all stay exactly where they were, regardless of `force`. `force` kept its original, narrower meaning (bypass the "same tile as before" no-op check) and is now orthogonal to isolation-blocking, since one existing caller (`force=true`, from the Pan-tool's tap-to-switch-tile gesture) needed to be blocked by isolation while other `force=true` callers (fresh profile entry, palette-image import, import-as-new-project) legitimately don't care about a stale isolation state and needed to bypass it. Those three call sites now pass `resetIsolation=true`; the two everyday-interaction call sites (drawing-tool taps, Pan-tool tap) pass the default `false` and are correctly blocked.

Toggling isolation off then back on re-anchors to whatever tile is active at that moment — this is now the (only) way to move the isolated tile, replacing the old dedicated lock button. The separate lock feature (`portraitTileIsolationLocked`, `portraitIsolationLockedKey`, the 🔒 button, and `updatePortraitTileOverlay()`'s branch reading the locked key instead of the live active key) was removed entirely as redundant — isolation-on now does that job unconditionally.

**Opacity range:** the "other tiles opacity" slider's range changed from 0–100% to **50–100%** (`<input type="range" min="50" max="100">`). Below 50%, the non-isolated tiles become visible/distracting enough to defeat the purpose of isolating one tile. The default value (`portraitTileIsolationOpacity = 0.78`) was already within the new range, so no migration/clamp was needed for existing sessions.

## 38.6 Dead code found and removed during this pass

- **`registerCommand('tool.eraser', 'Eraser', ['erase','rubber'], () => handleToolBtn('eraser'), 'Tools')`** — a broken, dead command registration. `'eraser'` was never a real tool id anywhere in the tool system (the real ids are `hardEraser`/`softEraser`); calling `handleToolBtn('eraser')` would leave `currentTool` set to a value no other code recognizes, since it isn't in `pixelToolDefs` and falls through to the generic `currentTool = t` assignment. It duplicated `tool.hardEraser`'s search aliases (`'erase'`) without doing anything useful. Removed entirely — `tool.hardEraser` already covers those search terms and does something real.
- **Matching dead condition removed elsewhere:** an `OR`-chain in the pixel-cursor/Portrait-palette-sync handler (`if(currentTool==='brush'||currentTool==='eraser'||...)`) checked for the same nonexistent `'eraser'` tool id — a condition that could never be true. While fixing it, a related real gap was closed at the same time: the chain was missing `hardEraser`/`softEraser` outright (only the dead `'eraser'` placeholder stood in for them), meaning erasing near a Portrait tile boundary never triggered the tile-follow that brush/pencil/bucket/etc. all get. Replaced the dead check with `currentTool==='hardEraser'||currentTool==='softEraser'`.

------------------------------------------------------------------------

# 39. V1_9 Fix/Feature Pass

Six requested items, three scope-expanded confirm()-migration fixes (person-approved mid-session), and a dead-code sweep, based on `V1_8_portraits`.

## 39.1 Deselect transparency on drawing-tool selection; restore last colour

Selecting Pencil, Brush, Soft Brush, Vector Pen, Fill (bucket), Line, Rect, or Ellipse while the transparent swatch is selected now restores whatever real colour was last selected, instead of leaving the tool with "no colour" active (which would silently draw nothing).

Implementation:

- `lastNonTransparentColor` (new top-level state) is updated inside `handleSwatchClick()` whenever a real (non-transparent) swatch is clicked.
- `APPLY_LAST_COLOUR_TOOLS = ['pencil','brush','softBrush','vpen','bucket','line','rect','ellipse']` is the list of tools this applies to. `hardEraser`/`softEraser` are deliberately excluded — erasing *is* drawing transparency, so transparent-as-selected-colour is correct there, not an oversight.
- The check lives in two places, mirroring the existing dual dispatch for pixel tools: `handleToolBtn(t)` for tools not in `pixelToolDefs` (vpen, bucket, line, rect, ellipse), and `window.selectPixelTool(n)` for the ones that are (pencil, brush, softBrush) — `handleToolBtn` returns early and delegates to `selectPixelTool` for the latter set, so both needed the same restoration logic.

## 39.2 Selecting transparency auto-selects Hard Eraser

Confirmed with the person (transparency pairing with Hard Eraser, not "hard brush" — the request's original wording was ambiguous between the two). `handleSwatchClick(c, isT)` now switches `currentTool` to `'hardEraser'` whenever `isT` is true and the current tool isn't already the hard eraser, calling `updateToolVisibility()` to keep the rest of the UI in sync.

## 39.3 Wand/lasso CLEAR button greys out with no selection

`#wandClearBtn` (given an id for this purpose) now starts with the native `disabled` attribute in the HTML, and `updateSelectionOverlay()` — which already runs on every selection change and already branches on `hasWandSelection()` — sets `clearBtn.disabled = true/false` in its two existing branches. No new CSS was needed; `.btn:disabled { opacity: 0.35; cursor: default; }` already existed and was simply never wired to this button.

## 39.4 / 39.5 Button renames

- Wand panel: "🧽 CONFIRM DELETE" → "🗑️ DELETE PIXELS" (armed/tap-twice text unchanged: "⚠️ TAP AGAIN TO DELETE"). "❌ CLEAR" → "❌ CLEAR SELECTION".
- Rectangle-selection panel: "🧽 DELETE SEL" → "🗑️ DELETE PIXELS" (scope-expanded per the person's approval, for consistency with the wand panel's new wording — both buttons do the same underlying thing, erase pixels within a selection, not delete the selection object itself).

## 39.6 "Delete layer" history label

The person's initial request was to split this into "Delete pixel layer" / "Delete vector layer". Implemented, then explicitly reverted on the person's instruction: **"delete layer" should stay generic and apply to all layer types, present and future** — not be split by type. `deleteLayer()`'s `pushTreeOperation` call uses the plain `'Delete layer'` label regardless of `layer.type`. Documented here specifically so a future session doesn't reintroduce the type-split thinking it was an oversight — it was requested, tried, and deliberately reverted.

## 39.7 Full confirm() → tap-twice migration (scope expansion, person-approved)

While implementing 39.6, three more native `confirm()` calls were found — the same known-bad-on-iOS pattern documented in section 30/37.3. The person approved migrating all three:

- **`deleteLayer(i)`** (single-layer delete, per-row icon button in the layers panel) and **`deleteGroup(node)`** (per-row group delete) — these can't use the existing id-based `makeTapTwiceConfirm()`, since a fresh `<button>` element is created on every layers-panel re-render (no stable `id` to key off). A new **`elementTapTwiceConfirm(btn, idleText, armedText, onConfirm, timeoutMs)`** helper was added alongside `makeTapTwiceConfirm()`: armed state and the auto-cancel timer live directly on the button element via a `WeakMap` (`elementTapTwiceState`), so each row's confirm state is independent and self-cleans if the row is ever removed while armed (no dangling `id`-based timer to leak). Both functions were restructured to take the triggering button as a parameter and split into an outer trigger call and an inner `doDelete()` closure, matching the existing `confirmWandDelete`/`performWandDelete` split.
- **`deleteSelectedItems()`** (multi-select bulk delete, a single fixed toolbar button) — this one *does* have a stable id (`deleteSelectedItemsBtn`), so it uses the standard `makeTapTwiceConfirm()` pattern. Split into **`confirmDeleteSelectedItems()`** (trigger) and **`performDeleteSelectedItems()`** (actual deletion), with a new `deleteSelectedItemsConfirm` instance declared alongside `wandDeleteConfirm`/`rectDeleteConfirm`.
- **Regression caught and fixed during this migration:** `registerCommand('layers.delete', ...)` still referenced the old function name `deleteSelectedItems` (renamed to `performDeleteSelectedItems`), which would have thrown a `ReferenceError` if triggered via search after the rename. Fixed to call `confirmDeleteSelectedItems` instead, so search-triggered deletion still goes through the tap-twice confirm rather than bypassing it.

**Zero native `confirm()` calls remain anywhere in the codebase as of `V1_9`.** Verified exhaustively (grepped for every `confirm(` call site and manually excluded all `makeTapTwiceConfirm`/`elementTapTwiceConfirm`/comment matches). Any future destructive action must use one of these two tap-twice helpers from the start — see section 30's "Destructive actions ↔ confirm pattern" danger-zone entry, updated to reflect this.

## 39.8 Dead code and wrong-comment sweep

Systematic pass: extracted every CSS class selector and every top-level `function` name, checked each for real usage (not just its own definition), and manually reviewed every candidate before removing anything, since an unused function isn't automatically dead code — some are unwired-but-legitimate (see the `clampScrollKeepingPeek` exception below) or tied to a half-built feature worth asking about rather than silently deleting.

**Confirmed dead and removed:**

- **`window.selectTransparentSwatch`** — referenced defensively (`typeof window.selectTransparentSwatch === 'function'`) inside `window.selectPixelTool`, but never defined anywhere, so the check was always false and the `try`/`catch` around it was unreachable dead code. Simplified to the one line that actually ran (`selectedColor = null`).
- **`.gallery-card.selected-card`** and **`.x-sep`** — orphaned CSS rules for classes never applied to any element (`className` is set to plain `'gallery-card'`/`'gallery-card new-canvas-card'` everywhere; no gallery multi-select feature exists to use `selected-card`).
- **`canMoveNode(node, direction)`** — superseded by simpler inline `pos>=arr.length-1`/`pos<=0` checks written directly at the up/down button call sites; `moveTreeNode` (not this function) is the actual mover. Its own logic was a strict subset of what the inline checks already cover.
- **`moveLayer(from, to)`** — operated on the flat `layers` array directly rather than the tree structure (`f.layerTree`) that's the actual source of truth for stacking order; superseded by `moveTreeNode`. Pre-tree-architecture leftover.
- **`loadPortraitPaletteFromImage(img)`** — a wrapper around `samplePortraitTilePalettes()` + `syncPortraitPaletteForPoint()`; the real image-import call site inlines both calls directly and never calls this wrapper. Its doc-comment ("Replaces the editable palette with the first unique opaque colours...") was relocated to `samplePortraitTilePalettes()`, which is what it actually now describes, and reworded slightly to reflect the per-tile (not single-palette) behaviour.
- **`ensureWandSelectionMask()`, `setWandPixel(mask,x,y)`** — small wand-selection helpers, never called; the real wand-fill code paths construct/write the `Uint8Array` mask directly inline.
- **`getHistoryPath(node)`, `historyDescendants(node,depth)`, `historyNodeLabel(node)`** — history-tree traversal helpers with no call sites; the actual Undo History panel renderer walks `undoStack`/`redoStack` directly rather than via these.
- **`isDescendantNode(root,targetId)`, `nodeChildren(node)`** — generic layer-tree helpers, never called; `collectNodeIds`, `findNode`, and friends cover the tree-traversal needs actually used elsewhere.
- **`syncAllFrameTrees()`** — never called; `ensureFrameLayerTree`/`syncActiveLayersFromTree` are invoked directly wherever needed instead.
- **`getProfilePickerDimensions()`** — never called. Its doc-comment ("Handles picking Standard/Portrait/Sprite on the hub...") was actually describing `selectProfile()`, which already has its own accurate, more detailed comment a few lines below — the misplaced comment was dropped rather than duplicated.

**Found, discussed with the person, and removed:**

- **`updateHubState()`** and the **`#hubContinueSection`** HTML block it controlled (a "Current Work" panel on the Pixel Art Hub splash screen with "▶️ Continue Editing" / "💾 Save Current Project" buttons, hidden by default via inline `display:none`). Neither was wired to anything — `updateHubState()` was never called, so the section could never become visible. Per the person's choice, both were removed rather than wired up or left as unexplained dead UI.
- This left **`continueEditing()`** (the function the removed button called) orphaned as a direct consequence, but it was **deliberately left in place** rather than cascade-deleted: it's a complete, distinctly-purposed function (per its own comment, it resumes in-place "without touching size," unlike other paths) that was reachable before this change, not confirmed-dead before it. Removing it forecloses ever restoring the "Continue Editing" shortcut without rewriting the logic from scratch. If a future session confirms there's no other planned way to reach it, it can be removed then.

**Found and deliberately left alone (unwired, not dead):**

- **`clampScrollKeepingPeek(value, maxScroll)`** and its `MIN_CANVAS_PEEK` constant — a real, well-commented function ("keeps a scroll value... so panning to an extreme leaves a sliver of canvas visible") that is never actually called. The one-finger Pan-tool drag (`g.manualPan`, in the touch-gesture handler) sets `viewport.scrollLeft`/`scrollTop` directly with **no clamping at all** — meaning a user can currently scroll the canvas completely out of view with a one-finger pan. This is a real, pre-existing functional gap, not dead code to clean up: the function should probably be wired into that drag path, but that's a behaviour change outside the scope of a "remove dead code" pass, so it was left as-is and is flagged here for a future session rather than silently fixed or removed.
- **`window.ImageLayer`** — INCORRECTLY treated here as a false positive at the time. This entry originally claimed `class ImageLayer { ... }` at script top level attaches to `window` automatically, unlike `const`/`let`. **That claim was wrong and was never verified before being written down** — see section 44.1 for the correction: `class` declarations behave like `let`/`const` for this purpose, not like `var`/`function`. The `window.ImageLayer` checks were not a legitimate feature-detection guard; they were silently always `false`, and this is the actual root cause of the flip/undo bug investigated across sections 42 and 44. Fixed in `V1_25` by explicitly assigning `window.ImageLayer = ImageLayer;` after the class declaration.

**Addendum, later in the V1_9 session:** `gridToScreenClient()` — the function this sweep's "found and deliberately left alone" logic had *kept* from V1_6 through V1_8_portraits (see 36.4) — was separately, explicitly requested for removal after this sweep had already concluded, and was deleted along with its one remaining comment reference. This wasn't found by the sweep methodology above; it's called out here for completeness since it's dead-code removal that happened in the same session. See 36.4 for the full account.

------------------------------------------------------------------------

# 40. V1_10 Fix/Feature Pass

Three requested items plus a follow-up naming/cleanup round, based on `V1_9`.

## 40.1 Viewport/edge detection — confirmed already present, reused

Before implementing anything, checked whether the code already had a way to detect the edge of the browser viewport. It did, and it's well-built:

- **`getViewportSize()`** — returns the true visible area via `window.visualViewport` when available (falling back to `window.innerWidth`/`innerHeight`), specifically because mobile Safari's dynamic toolbar changes what's actually visible without updating `vh`/`vw` CSS units to match.
- **`MIN_CANVAS_PEEK`** / **`clampPanScrollWithinEdgeMargin()`** (renamed in 40.4 from `clampScrollKeepingPeek`) — a scroll clamp that keeps a sliver of canvas always visible at an edge rather than letting it scroll completely out of view. This existed but was **unwired** (flagged, not fixed, in the V1_9 dead-code sweep — see section 39.8's "found and deliberately left alone" note). It is now wired in; see 40.1a.

No new detection primitive was built — both 40.1a (pan clamp) and 40.2 (fit-to-screen) hook onto these two existing pieces rather than reimplementing viewport math a third time.

### 40.1a One-finger pan now clamped to an edge margin

The one-finger Pan-tool drag (`g.manualPan` in the touch-gesture handler) previously set `viewport.scrollLeft`/`scrollTop` with no limit at all, so a person could scroll the canvas completely off-screen. It now routes both axes through `clampPanScrollWithinEdgeMargin(value, maxScroll)`, closing the gap flagged in V1_9.

## 40.2 Fit-to-screen on new/opened canvas

New/opened canvases now default to showing the whole picture, roughly centered, at a zoom level close to filling the screen with a small margin — rather than a hardcoded `scale = 10` (new canvas) or whatever zoom was saved with the project (opening one).

**`computeFitToScreenZoomIndex(w, h)`** (new function): computes the ideal scale to fit `w × h` within the viewport minus a `FIT_TO_SCREEN_MARGIN` (10px) on each side, then snaps to the nearest `ZOOM_STEPS` preset **by absolute distance** — the same nearest-preset approach the two-finger pinch-release handler already uses (`updateCanvasPanZoomRotate`). This was explicitly changed mid-session from an earlier "always round down, never crop" version to allow overshoot: the nearest preset can be slightly larger than the exact fit, cropping a little rather than always landing on a smaller, blurrier step.

Wired into every genuine "canvas becomes visible for the first time" path — deliberately **not** into paths that resume/continue existing work in place, since those should preserve whatever the person was last looking at:

- `newCanvasCreation()` (renamed from `initApp()`, see 40.3) — the fresh-canvas branch only, not the "resize existing work in place" branch.
- The import-image-as-new-project flow.
- `loadProjectFile()` (opening a project from a file).
- `openProjectFromStore()` (opening a project from the in-app gallery).

Not applied to `continueEditing()` or `newCanvasCreation()`'s own "resuming existing work, just resizing" branch — both explicitly preserve state rather than starting fresh, per their own existing comments.

### 40.2a Saving no longer persists zoom level

Per the person's follow-up instruction, `scale` was removed from every place a project gets serialized, so opening a project always computes fit-to-screen fresh rather than ever having a saved value to fall back to:

- `saveCurrentStateToStore()` (in-app gallery save)
- the duplicate-project function
- the Main-Menu auto-save-in-place path
- `saveProject()` (JSON file export)
- the gallery context-menu's "save to file" action

One read-only reference to `proj.scale` was found and left alone: the gallery thumbnail blur (see 40.5 — since removed entirely per a separate request, this is now moot, but is documented here for the record of what was found and why it was safe to leave mid-session).

## 40.3 `initApp()` renamed to `newCanvasCreation()`

Per the person's explicit (self-described as "my opinion," but implemented as requested) preference. Renamed the function declaration, both call sites (`onclick` handler, `frames.length === 0` fallback), both `traceLog()` label strings, and the doc-comment that referenced it by name (`// Shared by initApp()/continueEditing()/loadProjectFile()...`).

## 40.4 Vague-function-name cleanup

Two rounds, since the first round's scope was clarified with the person mid-session:

**Round 1 (viewport/gesture helpers):**
- `clampScrollKeepingPeek` → **`clampPanScrollWithinEdgeMargin`**
- `getPos` → **`getEventPos`** (word-boundary-safe rename; did not touch `getPosFromClient`, a different, still-used function whose name happens to contain "getPos" as a prefix)
- `mid2` → **`touchMidpoint`**
- `dist2` → **`touchDistance`**
- `angle2` → **`touchAngle`**

**Round 2 (layer-tree helpers, follow-up request):**
- `canMoveNode` — already removed as confirmed-dead code in the V1_9 sweep (section 39.8); nothing left to rename.
- `moveTreeNode` → **`reorderLayerTreeNode`** — the original name didn't convey that this function can both reorder a node's stacking position *and* move a layer into or out of an adjacent group, which its own comment already explains in detail.

## 40.5 Gallery thumbnail blur removed

Per the person's request. Removed the `thumbZoom`/`img.style.filter` logic in the gallery-card renderer (`renderGallery()`) that blurred a project's thumbnail based on its last-saved zoom level, along with the now-orphaned `.low-zoom-thumb` CSS rule and the `transition: filter 0.15s ease` on the base thumbnail rule (which existed solely to animate that now-removed filter). This was already heading toward moot after 40.2a removed `scale` from all new saves (new projects would never trigger the blur again regardless), but was removed outright rather than left as inert code referencing a field that no longer exists in fresh saves.

## 40.6 Dead code found and removed during this pass

- **`readNcmDigitGroup(id)`** — a leftover from the `getProfilePickerDimensions()` removal in the V1_9 sweep (section 39.8): that removal deleted the only caller but missed this callee. Confirmed doubly dead — not just unreferenced in JS, but its target DOM ids (`ncm-w-group`, `ncm-h-group`) don't exist anywhere in the HTML either, meaning the whole "ncm digit group" UI concept it was written for no longer exists.
- **Duplicate `centerCanvasInViewport()` doc-comment** — the exact same comment block was pasted twice: once correctly above the function itself, and once misattached above `MIN_CANVAS_PEEK`/`clampPanScrollWithinEdgeMargin` (then still named `clampScrollKeepingPeek`), burying those two's own correct, separate comments. The misplaced copy was removed.

------------------------------------------------------------------------

# 41. Planned: V1_21 Structural Reorganization (PREP WORK STARTED, MAIN REORG NOT STARTED)

The person has requested a large, explicitly multi-session refactor for a future `V1_21`: reorganize the entire file by functional area (grouping related functions together instead of their current, largely chronological/ad-hoc ordering), with a side goal of reducing file size if possible. **The actual grouping/moving has not begun.** What *has* happened is a first prep step, done deliberately as its own isolated unit before any moving starts — see 41.5. This section records the plan discussed and paused so it doesn't need to be re-derived from scratch whenever the main reorganization resumes.

## 41.1 Why this is high-risk and needs its own procedure

The file has ~350 top-level functions as of `V1_10` and no automated test suite. A single mis-copied brace during a large cut-and-paste reorganization can silently corrupt something far from the edit site, and nothing will catch it until much later — possibly not until a specific feature is exercised in testing. The existing Regression-Prevention Procedure (section 33) was written for feature-level changes, not for moving the entire file's structure at once, and is not sufficient on its own for this. This section adds rules specific to this reorganization; section 33 still applies on top of them.

## 41.2 Rules for this refactor specifically

1. **Reordering only — zero logic changes mixed into the same edits.** Renames, dead-code removal, and behaviour fixes are a different kind of change and must happen in separate, clearly-labelled passes, not silently folded into a move. This was explicitly deferred by the person (see 41.4) rather than declined — it's still in scope for this project, just not as part of moving code.
2. **Build a verification harness before moving a single line, and re-run it after every batch.** At minimum: a snapshot of every function name and its call-site count, taken before the refactor starts, diffed against the same snapshot after each batch. A function whose call-site count changed, or that silently vanished, is a signal to stop and investigate before continuing — not something to wave through because "it's probably fine."
3. **Move in small batches — one functional section at a time — each ending in a syntax check, the diff/inventory check from rule 2, and a shipped intermediate file.** Never attempt the whole file in one pass.
4. **Explicit protected call graph, checked every batch, not just at the end:**
   - Every `recordSelectionUndo(...)` call site must remain wired to the exact same call graph it had before the move.
   - Every debug hook (`traceLog(...)` calls, and anything that writes into `debugLogEntries` — see section 35.3) must remain wired identically. The Debug System is diagnostic infrastructure (section 35.6); a reorganization must not quietly detach a hook from the code path it was meant to observe.
5. **Section list** — the person deferred finalizing this (see 41.4), but the starting proposal, based on both the person's own list and what the file already contains, was:
   - Debug System (drawer, log capture, toggles) — largely already grouped, per section 35.
   - On-screen Keyboard
   - On-screen Numpad
   - Canvas Rendering (layout, camera, viewport — `layoutAll`, `applyCameraTransform`, `getViewportSize`, `computeFitToScreenZoomIndex`, etc.)
   - Canvas Lifecycle — Entry Paths: `newCanvasCreation()` (new canvas from the hub), the import-image-as-new-project flow (the person noted there may be two related code paths here worth checking during survey, not just one), `loadProjectFile()` (opening from a file), `openProjectFromStore()` (opening from the in-app gallery).
   - Canvas Lifecycle — Exit Paths: Main Menu, Save, Continue Editing, and whatever else leaves/tears down the live canvas.
   - Profile Rules (pixelArt/portrait/sprite button behaviour, `PORTRAIT_TOOL_FALLBACK`, tool hiding/auto-fallback logic from sections 37.6–37.8 and 38–39).
   - Tools — one subsection per tool: Pencil, Brush/Soft Brush, Hard/Soft Eraser, Bucket, Wand, Lasso, Line/Rect/Ellipse, Vector Pen/Shape/Edit, Eyedropper, Colour to Alpha, Pan.
   - Undo/Redo + History Memory System (`pushUndo`, `undoStack`/`redoStack`, `HISTORY_MEMORY_BUDGET`, `pruneHistoryLimit` — see section 30's "Undo history ↔ memory budget" entry and section 37.1).
   - Everything not covered above still needs an explicit home during actual planning (Layers panel, Gallery/Hub, Palette/Swatches, Project Save/Load serialization, Command Search) — the risk flagged at the time was that leaving these as an implicit "misc" bucket defeats the purpose of the reorganization, so they need their own named sections too, not a catch-all.

## 41.3 Side goal: file-size reduction

Requested as a secondary goal "if possible" — not a requirement that should compromise the primary reorganization goal or introduce risk of its own. Scope was not finalized (see 41.4): whether this means minification/whitespace reduction as a separate later pass, or also collapsing obviously duplicated inline patterns spotted while reorganizing, is still an open question for whenever this resumes.

## 41.4 What was explicitly deferred, not decided

When this was proposed, the person deferred all three open questions rather than answering them:

- Whether the section list in 41.2 point 5 is correct as proposed, or needs adjusting/splitting differently.
- How work should be chunked across sessions/messages (one full section per message vs. flexible stopping points).
- How aggressive the file-size side goal should be.

**Do not assume any of these were implicitly resolved.** A future session picking this up should re-confirm the section list and re-ask the pacing/aggressiveness questions rather than guessing from this write-up, since the person may have a different answer by the time this actually starts. This section exists so the *shape* of the plan and its safety rules aren't lost, not so the open questions can be treated as settled.

## 41.5 Prep work done: splitting `setupImportImageInput()` (build `V1_21_wip`)

Before any grouping/moving began, surveying the 5 proposed entry paths surfaced a problem: `setupImportImageInput()` was actually **one function serving two unrelated purposes**, branching internally on `pendingImportKind`:

- Importing an image onto a **new layer within the currently-open canvas** (not an entry path at all).
- Importing an image as **an entirely new project**, discarding whatever was open (a genuine entry path).

Grouping this function under "Canvas Entry Paths" as-is would have been misleading — half of what it does isn't an entry path. Splitting it was correctly identified as a **logic-adjacent change** (separating two purposes into two functions), not a pure reorder, so per 41.2 rule 1 it needed to happen as its own explicit, isolated step before any actual grouping/moving — the person confirmed this reading and asked for the split as the entire scope of this session, with grouping deferred to a later one.

**What changed:**

- **`importImageAsNewLayer(img, file, importBtn)`** (new) — the "add to existing canvas" branch, extracted verbatim. Still calls `pushTreeOperation('Import image as pixel layer', before)` exactly as before.
- **`importAsNewProjectFromImage(img, file)`** (new) — the "start a new project" branch, extracted verbatim. Still calls `traceLog(...)` and `resetSelectionState()` exactly as before (not `recordSelectionUndo` — this path intentionally doesn't record undo history for the outgoing document, same reasoning as `goToMainMenu()`; see the comment on `resetSelectionState()` itself).
- **`setupImportImageInput()`** (kept, narrowed) — now only wires the shared file-picker/`FileReader`/`Image`-decode plumbing and the shared `try`/`catch` error handling, then dispatches to one of the two functions above based on `pendingImportKind`. The shared async plumbing was deliberately *not* duplicated into each half — that would have risked the two paths silently diverging in their error handling over time, which is a correctness risk, not a stylistic one.
- **Removed:** `const _origSetupImportImageInput = setupImportImageInput;` — dead code sitting immediately after `goToMainMenu()`, assigned once and never referenced again anywhere (looked like an abandoned decorator-pattern attempt; its own comment claimed "hook up the import image to assign a currentProjectId after import," but no such hookup ever followed it). Confirmed dead via exhaustive grep before removal, then removed at the person's explicit request even though it's a logic change, since finding and removing it was called out as in-scope for this session specifically.

**Verification performed** (per 41.2 rule 2, a full inventory diff, not just "read the diff and eyeball it"):

- Function-name inventory: 340 → 342 names, diff showed exactly the two new functions added and nothing removed or renamed.
- Call-site count diff across all pre-existing names: exactly one function's count changed (`setupImportImageInput`, 3 → 4), and the change was traced and explained — the real call site is unchanged; the delta is two new doc-comments mentioning it by name replacing the old dead reference to it.
- Confirmed by direct grep that `pushTreeOperation`, `traceLog`, and `resetSelectionState` all still fire from exactly the same logical point in the code as before the split, just now inside correctly-scoped functions.
- Syntax-checked (`new Function(...)` per script block) and `<div>` tag-balance checked; both clean.

**Result:** `Pixel_art_app_V1_21_wip.html`, based on `V1_10`. Not a numbered release build — a work-in-progress checkpoint for the still-in-progress `V1_21` reorganization. The 5 entry paths are now genuinely 4 clean entry functions (`newCanvasCreation()`, `importAsNewProjectFromImage()`, `loadProjectFile()`, `openProjectFromStore()`) plus `importImageAsNewLayer()` correctly recognized as *not* an entry path, ready for accurate grouping whenever the actual moving work resumes. No grouping/moving has happened yet — all four/five relevant functions are still in their original file locations.

## 41.6 Dead-function scan methodology, and first full run's results

The person asked how dead functions and wrong comments would actually be found, not just fixed opportunistically. The answer split into two different-quality processes:

**Dead functions — systematic, repeatable, run on demand:**

1. Extract every top-level `function name(...)` declaration and every top-level `window.name = function` assignment (as of this scan: 342 + 4 = 346 named top-level functions, plus 9 classes that are their own separate category and weren't part of this scan).
2. For each name, grep the whole file for `\bname\b` and count all occurrences.
3. Any name with count ≤ 1 (nothing but its own declaration) is a *candidate*, not a confirmed-dead function.
4. Manually investigate every candidate before touching it — a low count doesn't always mean dead: it can mean legitimately-unwired-but-real (like `clampScrollKeepingPeek` before it was wired into the pan-clamp fix), or a naming mismatch where a *similarly*-named function is the one actually being called instead (see the first finding below), or half of an abandoned-but-real feature worth asking about rather than deleting (like `updateHubState`, removed in V1_9 only after discussion).
5. Only remove what's confirmed dead after that manual check; for anything genuinely unused but not obviously wrong, ask rather than assume.

**Wrong/stale comments — currently opportunistic only, not systematic.** There is no mechanical way to grep for "a comment that no longer describes its code" the way there is for an unreferenced function name. Every stale-comment fix so far (the `gridToScreenClient` comment that named a caller that no longer called it, the duplicated `centerCanvasInViewport()` comment sitting over the wrong function) was found incidentally, while reading that code closely for an unrelated reason — not from a deliberate sweep. The person and Claude agreed this doesn't need to be a separate pass before the reorganization: comments can't break anything when code moves (JS doesn't execute them), but a wrong comment *can* cause a function to be filed in the wrong section during the reorg, since the comment is often the only signal for what an unclearly-named function is actually for. The agreed plan: fold a lightweight "does this comment still match this code" check into the reorg itself, verifying and fixing each function's comment at the moment it gets moved into its new section, rather than running a separate exhaustive sweep across all ~7,400 lines first.

**First full scan's results (run against the state after 41.5's split), two candidates found:**

- **`window.getCurrentCanvasRenderingModeLabel`** — a thin wrapper around `getCanvasRenderingModeLabel` that did nothing but call it and return the result unchanged. Investigation found *why* it was dead: the Debug stats panel's real call site (`refreshDebugStats()`) calls `getCanvasRenderingModeLabel(...)` directly, not the `window`-exposed wrapper — a naming near-miss (two very similarly named functions, only one actually wired to a caller) rather than a simple "nobody needs this." **Removed**, per the person's decision.
- **`window.getImageRendererInfo`** — genuinely unused with no near-miss; returns which renderer (WebGL2 vs Canvas2D) an `ImageLayer` is using, which nothing currently surfaces (not even the Debug stats panel, which would be the natural place). **Kept, not removed** — per the person's decision, since wiring it in would be a feature addition and removing it would lose a plausibly-useful introspection hook for no real benefit. Flagged with an explanatory comment directly above its declaration so a future dead-code scan doesn't need to re-investigate it from scratch.

**Verification:** function-name diff showed exactly one removal (`getCurrentCanvasRenderingModeLabel`) and zero additions; the one call-count change among surviving names (`getCanvasRenderingModeLabel`, 3→2) was traced and explained — it's the wrapper's own now-deleted call to the real function, not a change to the real call site. Syntax and `<div>`-balance both clean.

## 41.7 WebGL2 image renderer removed entirely

Investigated at the person's request: whether the app's dual `WebGL2ImageRenderer`/`Canvas2DImageRenderer` split (used for the large-canvas `ImageLayer` tier, >999px on either axis) was pulling its weight, versus adding complexity for no real benefit. Two things were checked before touching any code:

- **Is the WebGL2 shader doing anything WebGL is actually good at?** No. Its fragment shader was a plain, unfiltered texture sample (`outColor = texture(uTexture, vTexCoord);`) — no blending, no filtering, no per-pixel transformation. Every edit re-uploads the *entire* CPU-side `ImageData` as a fresh texture and redraws a full-screen quad; there was no incremental or shader-driven work happening that Canvas2D's `drawImage()`/`putImageData()` doesn't already do in one call.
- **Does it actually prevent the crashes it was believed to prevent?** The person had heard WebGL2 helps avoid crashes on very large images, and separately wondered whether the history/memory-budget system already covered this. Investigation found both beliefs needed correcting: the memory-budget system (`HISTORY_MEMORY_BUDGET`, section 30) only governs *undo-history retention*, not the live canvas's own memory footprint — a completely separate concern. And on the crash-prevention claim itself, a web search found the opposite of the assumption: WebGL contexts measurably consume 5–10x more memory than Canvas2D for the same canvas dimensions, and there is a documented iOS Safari-specific memory leak where a WebGL canvas's memory climbs on every resize until the tab is killed, with the equivalent Canvas2D case staying flat. For an app whose Purpose section explicitly targets touch-first/iOS, and whose canvases do get resized (project resize, new-canvas creation), this is a real risk in the direction opposite to what WebGL2 was assumed to solve.
- A live reproduction of a bucket-fill-undo problem on a 1408×768 imported canvas (the person's own test sequence: new 32×32 canvas → Main Menu → import 1408×768 image → wand delete ~1.017M pixels globally with fuzzy matching → add layer → bucket fill) was independently investigated in the same conversation (see 41.8) and found to resolve without any WebGL-related change — reinforcing that WebGL2 wasn't providing the crash-safety property associated with it.

**What changed:**

- **`WebGL2ImageRenderer`** (the whole class, constructor through `destroy()`, ~140 lines including shader source, context-loss/restore handling, and the full render pipeline) — removed entirely.
- **`IMAGE_RENDERER_PREFERENCE`** and **`window.getImageRendererInfo`** — removed. With only one renderer left, a "which renderer is this using" introspection hook and a preference toggle between renderers both stop being meaningful (this is a direct consequence of there being one renderer, not a separate judgment call — contrast with section 41.6, where `getImageRendererInfo` was deliberately *kept* when there were still two renderers to distinguish between).
- **`createImageRenderer(layer)`** — simplified from a try/WebGL2-then-catch-fallback-to-Canvas2D dispatcher down to a one-line factory that always constructs `Canvas2DImageRenderer`. Kept as a named function (rather than inlining `new Canvas2DImageRenderer(layer)` at the one call site) so `ImageLayer` doesn't need to know or care which concrete renderer class it's using — preserves the same abstraction boundary for whenever/if a future renderer option is added.
- **Six stale comments elsewhere in the file** that referenced WebGL2 as if it were still an active rendering option (the `IMAGE RENDERERS` section banner, `ImageLayer`'s constructor comment about `el`/`cpuCanvas`, the `IMAGE_MODE_999_THRESHOLD_PATCH` block comment, the `DOCUMENT STATE -> RENDERER INVALIDATION -> RENDER` section banner, and `createBaseRasterLayer`'s renderer-selection comment) — all updated to describe the current Canvas2D-only reality, most pointing back to the explanatory comment above `createImageRenderer` for the "why" rather than repeating it six times.
- **One unrelated pre-existing duplicate comment found incidentally** while tracing a verification-harness call-count discrepancy: `"Rebuilds the stats readout in the Debug panel..."` was sitting misattached above `toggleDebugUnrestrictedVector()`, when the function it actually describes (`refreshDebugStats()`) already had its own correct copy of the same comment a few lines below. Removed the misattached copy. This predates this session's changes and wasn't caused by the WebGL2 removal — it surfaced only because the harness's `undo` call-count diff needed full manual tracing to explain, and this turned out to be part of that explanation (the duplicate comment happened to mention "undo depth" in passing).
- `this.rendererMode = this.renderer.kind` inside `ImageLayer`'s constructor was deliberately **left in place**, even though it now always evaluates to the single constant `'canvas2d'` and is never read anywhere. Removing it would be one more small trim beyond what was asked; flagged here rather than removed unilaterally, consistent with this session's practice of keeping logic-adjacent changes scoped to exactly what was requested.

**Verification:** Full inventory diff (functions + classes this time, 354 names in the baseline) showed exactly `WebGL2ImageRenderer` and `getImageRendererInfo` removed, nothing added. Five call-count deltas among survivors were individually traced and explained: `Canvas2DImageRenderer` and `createImageRenderer` both rose (now referenced/constructed in places the removed class used to handle), `ImageLayer`/`PixelLayer` rose by one each (mentioned once more in the rewritten comments), and `undo`'s count only moved because of the incidental duplicate-comment fix above — confirmed via a direct line-content diff (not just a count diff) showing every surviving `undo`-containing line was byte-identical before and after, with only line numbers shifting from the deletions. Syntax-checked and `<div>`-balance-checked clean. File size: 7466 → 7324 lines (142 lines removed), a direct step toward the file-size side-goal from section 41.3.

**Result:** `Pixel_art_app_V1_21_wip.html` updated in place (still a work-in-progress checkpoint, not a numbered release). The large-canvas (`>999px`) tier now has exactly one rendering path: Canvas2D via `Canvas2DImageRenderer`. `IMAGE_MODE_MAX_DIMENSION = 999` and the pixel/image tier split itself are unchanged and were not questioned — only the renderer choice *within* the image tier was collapsed.

## 41.8 Bucket-fill undo: investigated, appears resolved, cause not fully confirmed

The person reported a bucket-fill undo problem — described at one point as the memory-eviction algorithm deleting the *newest* entry instead of the *oldest* — using the exact reproduction steps in 41.7's third bullet. `pruneHistoryLimit()` (section 30's "Undo history ↔ memory budget" entry) was traced carefully: `undoStack.push(entry)` appends to the end, and `undoStack.shift()` removes from the front, which is genuinely oldest-first eviction as written — no code bug matching the "deletes newest" description was found. Manual sizing math for the reported scenario (a full-canvas bucket fill on a 1408×768 `ImageLayer`, tile-based `imageTiles` storage at `PHOTO_HISTORY_TILE_SIZE = 64`) came to roughly 8.3 MiB for one such entry — nowhere near large enough to be evicted on its own even against the smaller of the two budgets.

**A real, separate bug was found during this investigation and is still live:** `PHOTO_HISTORY_MEMORY_BUDGET` (128 MiB, intended as a larger cap specifically for Photo/large-canvas history) is declared but **`pruneHistoryLimit()` never checks it** — the function only ever compares against the flat `HISTORY_MEMORY_BUDGET` (64 MiB), regardless of which layer type or profile is active. The 128 MiB Photo-specific budget is currently dead code that does nothing. This was not fixed in this session (out of scope for a rendering-focused pass) and should be addressed alongside the planned adjustable-budget slider (see 41.9) — most likely by either wiring `PHOTO_HISTORY_MEMORY_BUDGET` into the check properly, or removing it if a single adjustable budget turns out to be simpler than maintaining two.

The person retested after later fixes had landed and reported "history suddenly works as intended now." No code change made in this conversation touched `pruneHistoryLimit`, `pushUndo`, or the eviction logic, so if the underlying symptom is genuinely resolved, the fix did not come from anything done here — it may be that the original failure mode was order/timing-dependent and didn't reproduce on retest, or that an earlier session's change (this conversation didn't audit which one) was actually responsible. **This should be treated as "not currently reproducing," not "root-caused and fixed."** If it recurs, get Debug-drawer LOGS (and ideally TRACE) output from a reproduction before investigating further — the person offered to capture this but a reproduction log was not obtained in this session.

## 41.9 Adjustable history-memory budget — DONE

Implemented as requested: a live slider in the Debug drawer's new "History Memory Budget" section, applied immediately (not persisted across sessions, not a `prompt()`-style one-off, matching the person's spec exactly).

**What changed:**

- **`HISTORY_MEMORY_BUDGET`** changed from `const` to `let` (default unchanged: 64 MiB) — the single value `pruneHistoryLimit()` actually checks.
- **`PHOTO_HISTORY_MEMORY_BUDGET`** (the dead 128 MiB constant from 41.8, never actually checked by anything) — removed outright rather than wired in. One live-adjustable budget the person can set themselves is simpler and more honest than maintaining two constants where only one ever did anything.
- **`setHistoryMemoryBudgetMiB(mb)`** (new) — clamps the slider's value to an 8–512 MiB range, updates `HISTORY_MEMORY_BUDGET`, updates the slider's own label, immediately re-runs `pruneHistoryLimit()` (so lowering the budget takes effect right away rather than waiting for the next edit to trigger a prune), refreshes the Undo History panel if it's open, and refreshes the Debug stats readout.
- **`#historyMemoryBudgetSlider`** (new HTML) — a `<input type="range" min="8" max="512" step="8">` in the Debug drawer, between the existing "Rendering" and "Log Capture" subsections, matching the drawer's existing control conventions.
- **`refreshDebugStats()`** — gained a new "History memory: ~X / Y MiB" line, and now syncs the slider's position/label to the live `HISTORY_MEMORY_BUDGET` value whenever it runs (guarded by `document.activeElement !== slider` so an automatic refresh can't fight the person's own in-progress drag). This already ran on every Debug-drawer open (`openDrawer()` already called it), so the slider is correctly initialized the first time the drawer is shown with no extra wiring needed.
- **The Undo History panel's status line** ("Linear history • X / 64 MiB") — the hardcoded "64" was replaced with the live budget value, so it stays accurate after the slider changes it.

**Verification:** inventory diff showed exactly one function added (`setHistoryMemoryBudgetMiB`), nothing removed from the function/class list (`PHOTO_HISTORY_MEMORY_BUDGET` was a `const`, not a function, so its removal doesn't show up in that particular diff — confirmed separately via direct grep, zero remaining references outside one deliberate historical-explanation comment). Four call-count deltas among survivors (`pruneHistoryLimit`, `refreshDebugStats`, `renderUndoHistory`, `uiAction`), each individually traced to exactly one new call site inside the new function/slider, nothing unexplained. Syntax, `<div>`-balance (171→173, matching the two new wrapper divs in the slider row), and `<input>` count all checked clean.

**Result:** `Pixel_art_app_V1_21_wip.html` updated in place. The history-memory budget is now a single, live-adjustable value instead of two constants where only one was ever enforced.

## 41.10 V1_22: Debug drawer accessible from the Hub

Requested: Debug should be reachable from the Pixel Art Hub (splash/gallery screen), not just from inside an open canvas.

**Root cause traced before touching anything:** `#debugDrawer` and its `#drawerBackdrop` were both nested inside `#main-app`, which has `#main-app { display: none; }` until a canvas is open. A hidden ancestor hides its entire descendant subtree regardless of the descendant's own `position: fixed` and `.open`/z-index state -- so a hub button simply calling the existing `toggleDrawer('debug')` would have toggled the drawer's classes correctly but shown nothing, since `#main-app` itself was still invisible. This is not a z-index problem (that came later, see 41.11) -- it's a display-hierarchy one.

**Precedent found and followed:** the custom on-screen keyboard already has this exact problem solved, with its own comment saying so verbatim: `<!-- Global on-screen keyboard: kept outside #main-app so it remains usable from the Hub. -->`. The fix here follows the same established pattern rather than inventing a new one.

**What changed:**
- `#debugDrawer` and `#drawerBackdrop` moved from inside `#main-app` to be siblings of it (alongside the keyboard), using script-verified div-depth counting to find exact block boundaries rather than manual line-matching -- **a first attempt using a direct text-based `str_replace` corrupted the document structure** (partially removed the drawer's wrapping tags without correctly closing them) and had to be reverted to the clean `V1_21_wip` base before redoing the move with a boundary-counting script. Noted as a general lesson: in a file this size with this much structural repetition, moving large HTML blocks should default to scripted boundary-finding, not manual text matching.
- A "DEBUG" button added to `#gallery-header` (`.btn` styled, `flex: 0 0 auto` override since `.btn`'s base `flex: 1` would otherwise fight the header's `space-between` layout), wired to the existing `toggleDrawer('debug')`.
- `refreshDebugStats()` audited for hub-safety: `frames`/`layers` default to empty arrays (safe), but `gridW`/`gridH` are `undefined` before any canvas exists. Confirmed no crash (`Number(undefined)` -> `NaN`, falls through the `>999` checks safely) but changed the canvas-size line to show "none open" instead of "undefined x undefined" for honesty, since this is now a real reachable state rather than a theoretical one.
- `openDrawer`/`closeDrawer` left otherwise unchanged; `.side-drawer`, `.fbtn` class toggling, and `drawerOpenName` bookkeeping all worked correctly regardless of the drawer's DOM position, since none of it was ever scoped to `#main-app` specifically.

**Verification:** `<div>` count unchanged at 173/173 before and after the move (confirming nothing lost or duplicated during the corrupted-then-reverted-then-redone process), syntax clean.

## 41.11 V1_22: Debug drawer raised above every overlay, including the search palette

Follow-up request: put the Debug drawer visually on top of everything. Investigated first (not assumed): the app already uses `position: fixed` + explicit `z-index` consistently for every overlay, with no nested-stacking-context or `overflow: hidden` clipping issues -- this was a one-number stacking change, not a rewrite, once 41.10's display-hierarchy fix was already in place.

Full z-index inventory taken before changing anything (lowest to highest): drawers/panels at 850-960, splash/gallery screens 1000-1200, various confirm/context overlays 1800-2100, and the global command/search palette at **9999** -- the highest value in the file by a wide margin, by design (meant to be reachable from anywhere).

Person's follow-up refinement: move the search palette from 9999 to 3000, and put Debug at 9000 -- i.e. Debug above literally everything including search, rather than just above the normal app chrome.

**What changed:**
- Global command palette: `z-index: 9999` -> `3000` (one property in the inline `style.cssText` where it's constructed in `openGlobalCommandPalette()`).
- `#debugDrawer { z-index: 9000; }` -- an ID-specific override, since `.side-drawer` is a shared base class used by both `#toolsDrawer` and `#debugDrawer`; raising the shared class would have wrongly lifted the Tools drawer too. Tools stays at its normal 950 tier.
- `#drawerBackdrop.debug-open { z-index: 8999; }` -- the backdrop is also shared between both drawers (per 41.10's move), so it needs a *conditional* override, not a permanent one: `openDrawer()`/`closeDrawer()` now toggle a `.debug-open` class on the backdrop specifically when Debug (not Tools) is the drawer being opened/closed, so the backdrop only rises to meet the drawer when Debug is actually the one showing.

**Verification:** confirmed the full z-index list before and after had no other value sitting between 2100 and 9999 that could collide with the new 3000, and re-sorted the final list to confirm the intended ordering held everywhere (Debug > search palette > everything else). Syntax and `<div>`-balance clean.

## 41.12 V1_23: Flip buttons show a "loading" state, one undo step preserved

Requested: horizontal/vertical flip buttons should grey out and read "loading" while the flip runs, then restore automatically, with the existing one-undo-entry-per-flip behaviour preserved (explicitly flagged by the person as the hard part -- "good luck compressing this step").

**Investigated before implementing:** `flipHorizontal()`/`flipVertical()` (both `PixelLayer`'s array-based version and `ImageLayer`'s `ImageData`-based version) are fully synchronous nested-pixel-loop operations with no yield point -- a single-threaded JS loop cannot let the browser repaint mid-operation. This means the only way to show a "loading" state at all is: disable + relabel the button, force an actual repaint via `requestAnimationFrame` + a zero-delay `setTimeout` (two separate yields, since `requestAnimationFrame` alone can still land before the next paint on some browsers), *then* run the flip, *then* restore the button. Confirmed with the person before implementing that this means "loading" will visibly flash even on a small/fast canvas and will genuinely stay up for however long a large `ImageLayer` flip takes -- there is no way to make it conditional on operation size without adding complexity disproportionate to the request.

Re: "one undo step" -- traced `beginEdit()`/`commitEdit()` and confirmed a single flip button press already produced exactly one `pushUndo()` call before this change; the request's real requirement was to *not break* that while adding the loading UI, not to newly merge two separate operations into one (each button already triggers only its own single flip).

**What changed:**
- **`runWithLoadingButtonState(btnId, loadingText, runOperation)`** (new, shared by both flip handlers; third parameter renamed from the original `work` to `runOperation` in section 43's session, per the person's request -- `work` as a name gave no hint it was a deferred, potentially-slow operation callback) -- disables and relabels the given button, defers via `requestAnimationFrame(() => setTimeout(() => { ... }, 0))`, runs `runOperation()`, and restores the button's original text/enabled state in a `finally` block so restoration happens even if `runOperation()` throws (defensive; the flip functions already swallow their own errors internally, but this covers anything above that inner `try`, like `activeLayer()` itself).
- **`flipActiveLayerH()`/`flipActiveLayerV()`** -- bodies unchanged in every functional respect (same `traceLog` calls, same `isPixelLike`/`beginEdit`/`commitEdit`/CSS-transform branch logic, same `renderLayersPanel()` refresh at the end), just now wrapped in a `runWithLoadingButtonState(...)` call so the button shows "LOADING..." and goes native-`disabled` (which already greys it out via the existing `.btn:disabled { opacity: 0.35; }` rule -- no new CSS needed) for the deferred tick, then during the flip itself, then restores.
- The `beginEdit()`/`layer.flipHorizontal()`/`commitEdit(snap)` sequence still runs as one uninterrupted synchronous block inside the deferred callback -- the undo-transaction boundary was not touched or split in any way.
- Confirmed `uiAction()` (the wrapper both flip buttons' `pointerup` listeners call through) doesn't await or synchronously depend on its callback completing, so deferring the real work inside the flip functions themselves is safe; confirmed no other call site (keyboard shortcut, command registry) invokes either flip function and might have assumed synchronous completion.

**Verification:** inventory diff showed exactly one function added (`runWithLoadingButtonState`), nothing removed; the one call-count change among survivors (`ImageLayer`, +1) traced to the new doc-comment mentioning it by name. Syntax and `<div>`-balance (173/173) clean.

------------------------------------------------------------------------

# 42. Flip/Undo Bug Investigation (RESOLVED), and DECIDED: PixelLayer Proxy Removal (Option B) (NOT STARTED)

## 42.1 The flip/undo bug: root cause found, fix not yet applied

The person reported: after importing a large (1408x768) photo and pressing a flip button once, the flip visually succeeds but Undo stays greyed out and the History panel is empty.

**Investigated at length before any log was available.** `beginEdit()`/`layer.flipHorizontal()`/`commitEdit(snap)` were traced end-to-end and even independently simulated in Node -- the transaction logic for `ImageLayer`'s `'imageFull'` undo path is correct as written and pushes exactly one `pushUndo()` call in isolation. `estimateHistoryEntryBytes()`'s handling of `imageFull` entries, the 512 MiB budget ceiling, and the `'imageFull'` type-string match at both the write and read sites were all individually checked and ruled out.

**The actual cause, found from the person's TOUCH+LOGS+TRACE log:**

```
flipActiveLayerH called, activeLayer=CANVAS.layer-canvas type=pixel isPixelLike=true
```

The imported 1408x768 photo became a **`PixelLayer`** (`type=pixel`), not an `ImageLayer` (`type=image`) as the >999px threshold should produce. Every hour spent tracing the `ImageLayer`/`'imageFull'` undo path was tracing a code path this canvas never actually took -- the real defect is upstream, in whatever decided which class to instantiate at import time (`pixelLayerFromImage()`'s `shouldUseImageMode(w,h) && window.ImageLayer && selectedProfile !== 'portrait' && selectedProfile !== 'sprite'` check, or something feeding it a wrong value). A diagnostic-only build (`Pixel_art_app_V1_23_debug.html`, based on `V1_23`, not a numbered release) was shipped with two added `traceLog()` calls at the exact decision point in `pixelLayerFromImage()`, to capture which of those four conditions is actually false at runtime. **The person reproduced again on that debug build and the bug still persists, but a second log with the new instrumentation has not yet been supplied.**

**Explicitly deprioritized by the person.** The bug fix itself is no longer the priority -- see 42.2. Do not spend further session time chasing this specific symptom until 42.2's larger cleanup has happened; it is likely to be resolved as a side effect of collapsing the two layer classes (see 42.1a), or at minimum will be far easier to diagnose correctly once there's only one undo-capture system instead of two.

### 42.1a Why this bug is a symptom of the larger problem, not an isolated defect

`PixelLayer` already contains unused, half-built scaffolding for exactly the "large canvas as image" idea `ImageLayer` exists to provide separately: a `renderMode: 'image'` state, `setImageRenderSource(img)`, and a `switchToPixelRender()` method, all defined on `PixelLayer` itself -- but `setImageRenderSource()` is never called anywhere in the codebase (confirmed via exhaustive grep). This reads as an earlier, abandoned attempt to unify the two layer types that was started and not finished, leaving both the old two-class system and a partial, dead alternative sitting in the file at once. The `PixelLayer`/`ImageLayer` split, and its two separate undo-capture systems (`PixelLayer`'s single sparse-map `_historyCapture` vs. `ImageLayer`'s dual `'tiles'`/`'full'`-mode `_historyCapture`), is exactly the kind of seam where "which code path did this layer actually take" bugs like 42.1 live, and will keep producing them until it's resolved properly rather than patched around.

## 42.2 DECIDED: Option B only -- drop PixelLayer's Proxy, keep two classes (NOT STARTED)

**This section's original title/framing ("collapse ImageLayer into PixelLayer") is superseded.** Investigation and a follow-up benchmark (below) led to a real, locked decision that is narrower than a full collapse: **Option B only.** `ImageLayer` and `PixelLayer` remain two separate classes with their own data shapes -- nothing is being unified or merged. The only change planned is inside `PixelLayer` itself: replace its `Proxy`-based change-tracking (`makeTrackedPixelData`) with the same kind of explicit, non-Proxy tracking `ImageLayer` already uses (`setPixel()` calling `captureHistoryTile()`/`captureHistoryFull()` directly, no Proxy involved). The array-of-arrays *shape* stays exactly as it is.

**Options C and D, considered and explicitly declined/deferred by the person:**
- **Option C** (flat `Uint8ClampedArray` + bounding-box undo via `putImageData`'s native dirty-rectangle support, unifying both classes onto one storage shape) -- explicitly **declined**. The person does not want to over-engineer this further; B alone recovers nearly all the real performance gap (see the benchmark below) without touching `PixelLayer`'s storage shape or merging the two classes.
- **Option D** (command-pattern undo -- store the operation and its inverse, not a pixel diff -- for naturally-invertible operations like flip/rotate) -- explicitly **reserved for the vector layer's undo system specifically, and only if/when that work is separately approved.** Not to be applied to `PixelLayer`/`ImageLayer` as part of this section's work. Do not build this speculatively ahead of the vector-layer decision.

**Why B and not A, with real numbers now, not just risk-hedging language.** A follow-up synthetic benchmark isolated the Proxy's cost from the array-of-arrays *shape's* own cost, on a 1000x700 grid (Node.js, so relative comparison only, not an on-device number):
- Array-of-arrays, no Proxy at all: 25.85ms
- Array-of-arrays, Proxy-tracked (today's real `PixelLayer`): 186.45ms
- Flat typed array (today's real `ImageLayer`): 17.30ms

The Proxy alone accounts for a **7.2x** slowdown; the array-of-arrays shape itself, with no Proxy, is only **1.5x** slower than a flat buffer. In other words: **the Proxy is almost the entire cost.** Dropping it while keeping the array shape (Option B) recovers nearly all of the performance gap that originally motivated considering a full collapse (Option A/C) -- without the larger blast radius of merging two classes or rewriting the storage format. This is why B was chosen over A/C: it gets nearly all the benefit for a fraction of the risk and session-time cost, which matters given the person's hard deadline (section 43.1).

**Origin.** The person had always assumed `ImageLayer`'s reason for existing was to host the WebGL2 renderer (removed in section 41.7). With WebGL2 gone, they asked whether the `ImageLayer`/`PixelLayer` split still improves anything, and separately flagged that `VectorLayer`/`ReferenceLayer` had never been checked against the same WebGL2 question.

**Historical reference available for this work:** `Pixel_art_app_bucket_projectname_colourtool_fix_2_html.txt`, the last build before the split existed at all -- see its entry in "Historical Regression References" for what its unified `PixelLayer`-only, type-agnostic undo model looked like. Less directly relevant now that a full collapse (which that old build would have most informed) is declined -- kept as a reference for its explicit, non-Proxy capture pattern specifically, which is closer to what B actually needs.

**Investigated, both questions:**
- `VectorLayer` and `ReferenceLayer` were **never involved with WebGL2 at all** -- both extend the shared `Layer` base class and use plain Canvas2D (`this.ctx`, `drawImage()`) throughout, past and present. Nothing to reconsider there; this line of investigation is closed.
- `ImageLayer` vs `PixelLayer`, post-WebGL2-removal: `ImageLayer` no longer buys anything `PixelLayer` doesn't already do natively. It maintains its pixel data as a flat `Uint8ClampedArray` and exposes a `Proxy`-wrapped fake `pixelData[x][y]` array-of-arrays interface purely so shared tool code (written against `PixelLayer`'s real array structure) can address it the same way -- going through `getPixel`/`setPixel` on every single access. `PixelLayer` has that structure natively, no proxy needed. `ImageLayer` also carries its own renderer object (`Canvas2DImageRenderer`, the sole survivor of section 41.7's removal), its own `cpuCanvas`, and the separate two-mode undo-capture system described in 42.1a. (This paragraph remains accurate background even though a full collapse was declined -- it's why B, not "leave PixelLayer's Proxy alone," was the right call.)

**The person separately raised a specific historical claim:** that WebGL2 was originally meant to prevent a browser crash when ~1 million pixels are wand-selected (highlighted) and the canvas is then pinched to zoom out. This was checked directly rather than assumed either way:
- The wand-selection *highlight* (`#selectionOverlay`, drawn from the `wandSelection` `Uint8Array` mask) is **completely independent of which layer class holds the artwork** -- it's its own dedicated overlay `<canvas>`, redrawn only when the selection itself changes (`updateSelectionOverlay()`), never during a zoom. During a pinch-zoom, only its CSS `width`/`height` change (a cheap, browser-native, GPU-composited scale); the pixel buffer itself is untouched. This was true before WebGL2 existed and remains true now.
- `ImageLayer.layoutCSS()` (what runs on every zoom) is exactly as cheap as `PixelLayer`'s and `VectorLayer`'s equivalent -- CSS `style.width`/`style.height` only, no data resize, no re-render.
- The actual, already-documented fix for this exact crash scenario (section "Large-canvas crash investigation" near the top of this handoff, and the V1_7 re-test noted there) was the **camera architecture** -- not resizing/re-laying-out the canvas buffer during a live pinch gesture, only snapping zoom to the nearest preset on release -- which has nothing to do with which layer class or renderer is in use. The V1_7 re-test of this exact scenario (Wand tool, ~1M pixels, pinch-zoom-out, iOS Brave) already succeeded with **no WebGL2 involvement at all**, since the removal happened in V1_21_wip, several versions later than that successful re-test.

**Conclusion:** the WebGL2-preserved-us-from-crashing belief does not hold up under investigation -- for this specific scenario, the fix was already elsewhere and already independently verified.

**Actual scope for Option B, for whenever this work begins:**

Unlike a full collapse, B does **not** touch the 14 `instanceof ImageLayer`/`instanceof PixelLayer` call sites at all -- both classes still exist, still get chosen the same way they are today, still serialize/deserialize/resize the same way. The only real surface area is inside `PixelLayer` itself:
- `makeTrackedPixelData()` -- remove the `Proxy` wrapping; return a plain array-of-arrays instead.
- `PixelLayer.plot()` -- add an explicit `_historyCapture.before` write before mutating `this.pixelData[x][y]`, mirroring what the Proxy's `set` trap used to do automatically (same pattern `ImageLayer.setPixel()` already uses with `captureHistoryTile()`/`captureHistoryFull()`).
- `PixelLayer.setPixelData()` -- already fixed in `V1_28` (section 44's bug log, Bugs Squashed entry 1.3) to explicitly capture the outgoing grid before a bulk reassignment; this fix stays exactly as it is under Option B, since it was never Proxy-dependent in the first place, and would need to stay even if the Proxy is removed from `plot()`.
- Any other direct writer of `this.pixelData[x][y]` that currently relies on the Proxy's automatic capture needs the same explicit-capture treatment `plot()` gets -- this needs a fresh grep for `.pixelData[` writes on `PixelLayer` specifically before starting, since the exact list may have changed since the 14-call-site count above (which was for the declined full-collapse scope, not B's narrower one).

**Genuine risks, not glossed over:**
- Every direct `this.pixelData[x][y] = ...` write site on `PixelLayer` needs to be found and given explicit capture -- missing one would silently reintroduce a version of the same undo bug fixed in section 44/`V1_28`, just via a different code path. This needs its own careful audit, not an assumption that `plot()` is the only writer (see the "same-named wrapper is not the real choke point" danger-zone lesson -- the same caution applies here).
- Still worth a verification harness and small batches, consistent with section 41's general discipline for risky changes, even though B's blast radius is much smaller than a full collapse.

**Explicit priority ordering, per the person:** this work is a higher priority than the specific flip/undo bug from 42.1, which is now moot anyway -- that bug (section 44.1) was fixed by an unrelated one-line `window.ImageLayer` wiring fix, not by anything in this section.

------------------------------------------------------------------------

# 43. Overall Roadmap and Priority Order (as of V1_24)

## 43.1 Real time constraint

The person's Claude Pro plan ends **September 14, 2026**. Their own usage pattern is roughly 3 session-days per week. As of this handoff's last update (August 12, 2026), that's approximately **12 remaining session-days** before the plan lapses. Each session-day realistically completes one meaningfully-sized unit of work (one feature, one bug fix, one reorg batch) -- risky work (the section 41 reorganization, the section 42 layer collapse) specifically has to move in small, individually-verified batches rather than all at once, which caps how much a single session can safely cover regardless of how much raw time is available in it. A future session should recalculate the remaining days against the current date before assuming this budget is still accurate.

## 43.2 Goal tiers, per the person

**Set goals (commit to attempting all of these within the plan window):**
1. Sprite animation workflow -- see 43.3, spec still pending fuller explanation from the person.
2. Spline editing in vector mode. **Note on undo for this feature:** "Option D" (command-pattern undo -- store the operation and its inverse, e.g. "point 3 moved from (10,20) to (15,25)," rather than a pixel/state diff) is reserved specifically for this feature's undo system, per the person -- but only if/when spline editing is actually approved and started. Do not build D speculatively ahead of that; see section 42.2 for the full A/B/C/D comparison and why D fits vector edits naturally.
3. Adjustable gradients with per-stop adjustable colours (Photoshop-style gradient editor).

**Stretch goals (attempt only if time remains after the set goals):**
4. Raise the real canvas creation/resize ceiling from 2000px to 4096×4096 -- see section 4's "Planned, not yet implemented" note for the exact clamp sites this touches. Ahead of 3D specifically, per the person.
5. 3D.
6. PSD layer import/export -- explicitly last.

**Foundational work, updated:** the flip/undo bug (section 42.1) is now **resolved** -- it was fixed by an unrelated, small, one-line `window.ImageLayer` wiring fix (section 44.1), not by anything touching the `PixelLayer`/`ImageLayer` split. Separately, section 42.2's original "collapse into one class" plan was investigated and **declined** in favour of a narrower fix, "Option B" (remove `PixelLayer`'s Proxy-based change tracking, keep both classes and both data shapes as they are) -- see 42.2 for the full reasoning and the benchmark that led to this call. Because B is small and self-contained (touches only `PixelLayer`'s internals, not the 14 `instanceof` call sites a full collapse would have), it no longer needs to be treated as a large architectural prerequisite blocking the three set goals the way a full collapse would have -- but it's still real, undone work with its own real risk (see 42.2's "genuine risks" list), and should be scheduled deliberately rather than assumed to be free just because it's smaller than originally planned.

The full section-41 structural reorganization (grouping code by function) was **not** included in either tier by the person in this pass and should be treated as lower priority than everything in 43.2 unless the person says otherwise -- it is about long-term maintainability, not shipping new capability, and the person's own framing throughout this conversation has been about getting features and fixes done within a hard deadline.

**Ongoing code/readme cleanup passes** (dead-code sweeps like the one confirmed clean in `V1_28`, this handoff doc's own periodic accuracy passes) are small enough to keep doing opportunistically alongside bug fixes and don't need their own dedicated session the way the section-41 reorganization does. The person has asked that this kind of cleanup rank ahead of the two stretch goals (3D, PSD) specifically -- i.e. if there's a choice between spending limited remaining time on a cleanup pass versus starting 3D/PSD work, cleanup wins. This does not change 43.2's set-goal priority (sprite/spline/gradient still come first); it only clarifies where cleanup sits relative to the two stretch goals once/if the set goals are done.

## 43.3 Sprite animation workflow -- spec pending

The person's first set goal is explicitly **not** an extension of the existing Sprite profile's flipbook-style frame strip (frames array, FPS playback, spritesheet PNG export -- all of which already exist and were confirmed working before this feature was scoped). It is a **different, specific pipeline**: animations are read and played back from an **XML file inside a ZIP archive**, where the ZIP also contains multiple PNG spritesheet pages that the XML's frame/region data cross-references. This is structurally closer to a texture-atlas animation format (the general shape used by tools like Spine, DragonBones, or TexturePacker-style atlas+XML exports) than to the existing frame-by-frame Sprite mode.

**The person has not yet fully explained this and said they will add detail later.** Do not begin implementation or detailed scoping from the one-sentence description above -- it is a placeholder capturing what's known so far, not a complete spec. When the person provides the fuller explanation, this section should be rewritten with the real requirements (XML schema/format expected, whether playback-only or also authoring/export, how it relates to or replaces the existing Sprite profile, whether existing `frames[]`/FPS/spritesheet-export code is reused or bypassed) before any code is written.


------------------------------------------------------------------------

# 44. Flip/Undo Bug RESOLVED (V1_25), Version Display, Two New Bugs Flagged and Held

## 44.1 Root cause of the flip/undo bug (section 42.1): confirmed and fixed

The bug from section 42.1 -- imported large photos always landing as `PixelLayer` (`type=pixel`) instead of `ImageLayer` (`type=image`), regardless of the >999px threshold -- was fully root-caused via a targeted diagnostic build and traced to something much more fundamental than the size-threshold logic itself.

**The actual cause:** every `window.ImageLayer` check in the codebase (`pixelLayerFromImage`, `enforcePixelArtRendererForDimensions`, `createBaseRasterLayer`, `addPixelLayer`) was checking a property that was never being set. `class ImageLayer { ... }` declared at the top of the script does **not** automatically create `window.ImageLayer` -- this is standard JS behaviour, confirmed via web search and independently reproduced in a Node.js sandbox (`class TestLayer {}` exists and is callable, but `globalThis.TestLayer === TestLayer` is `false`). `class` declarations behave like `let`/`const` in this respect, not like `var`/`function` declarations, which *do* attach to the global object. **This corrects a wrong claim made in an earlier session** (documented at the time as "class ImageLayer at script top level in a browser context does attach to window automatically, unlike const/let" -- that claim was asserted without verification and was incorrect). Every `window.ImageLayer` check in the codebase had therefore always evaluated `false`, meaning `ImageLayer` had likely never been constructible through the normal size-threshold path in any prior build, going back further than this investigation covers -- every canvas, regardless of size, had been silently running through `PixelLayer`'s Proxy-tracked array-of-arrays model the entire time.

**The fix (`V1_25`):** one line, `window.ImageLayer = ImageLayer;`, added immediately after the class declaration -- matching the existing convention already used for other intentionally-global identifiers in this file (e.g. `window.pixelToolDefs`). No other class in the file is checked via `window.X` anywhere, so `ImageLayer` was uniquely affected; nothing else needed the same fix.

**Real-world consequence, confirmed by the person after shipping:** imports and flips are now "blazingly fast." A companion diagnostic build had separately measured the buggy `PixelLayer` path at **598ms** for a single flip on a 1408x768 canvas (real on-device number, not the earlier ~279ms Node.js synthetic estimate -- real DOM/canvas repaint overhead is meaningfully higher than a benchmark loop). The `ImageLayer` path's real on-device number was not separately captured (the person confirmed via feel and second-resolution log timestamps that it completed within the same second, consistent with a fix), but `runWithLoadingButtonState` now logs exact millisecond timing permanently going forward (see 44.3), so a future flip will produce a precise number without needing another one-off diagnostic build.

**Real risk this fix activated for the first time:** with `window.ImageLayer` now correctly truthy, five call sites across the app started executing branches that had likely never run in production before, including `enforcePixelArtRendererForDimensions()`'s pixel-to-image conversion branch (constructing a fresh `ImageLayer` from an existing `PixelLayer`'s content on a canvas resize crossing the 999px threshold). This was reviewed by inspection (looks structurally sound, uses `loadFromImage()` correctly) but has not been separately stress-tested as its own scenario -- worth keeping in mind if a resize-across-the-threshold bug surfaces later, since that exact code path is newly live.

**Confirmed working by the person:** `undo()`/`redo()` were tested after this fix (Undo pressed, Redo pressed, both via the History panel directly) and confirmed working. The person separately noted "history still needs work on the next pass" as a general area to revisit later, but did not describe a specific reproducible symptom at this time -- nothing further to act on here until a concrete issue is reported.

## 44.2 Verified: no other class has the same `window.X` gap

While applying the fix, every class declaration in the file was checked for the same pattern (`Canvas2DImageRenderer`, `ImageLayer`, `Layer`, `PixelLayer`, `MaskLayer`, `ClipLayer`, `ReferenceLayer`, `VectorLayer`). None of the others are ever referenced via a `window.X` check anywhere in the codebase -- `ImageLayer` was uniquely affected, confirmed by exhaustive grep, not assumed.

## 44.3 V1_26: permanent flip-button response timing, version display improvements

**Response timing (requested by the person, permanent instrumentation, not a one-off diagnostic build):** `runWithLoadingButtonState()` -- the shared wrapper both flip buttons already used for their loading-state UI (section 41.12) -- now measures and logs two numbers via `traceLog` on every call: the paint-tick delay (how long the forced `requestAnimationFrame`+`setTimeout` repaint actually took) and the operation time (the real flip/whatever-runs-inside-it). Since every future button that uses this shared wrapper automatically gets timed, this doesn't need to be re-added per-feature.

**Version display, in two forms now:**
- **Passive (V1_25):** a static "V1_25"-style label under the Hub's title, and a "Build: V1_25" line pinned at the top of the Debug drawer, both set at boot.
- **Active (V1_26, this session's addition):** a "PRINT VERSION" button in the Debug drawer that logs `Build version: V1_26` via `traceLog` (so it appears in an exported log, which the passive labels don't) and briefly flashes the version directly on the button itself as immediate on-screen confirmation.

`BUILD_VERSION` is a single top-level constant (`const BUILD_VERSION = 'V1_26';`, near the very top of the script) -- update this one line with every new numbered build going forward. This was added specifically because two separate sessions lost real time to "which file did I actually open" confusion (a diagnostic build that looked unchanged at first glance, and general risk of testing a stale tab).

## 44.4 Two new bugs found, investigated, and explicitly held (not fixed yet)

**Update:** 44.4a (Portrait tile isolation) was fixed in `V1_27` -- see Bugs Squashed entries 1.1–1.2 and section 30's danger-zone entries. 44.4b (Resize-Cancel) remains unfixed. Its original framing below ("deferred until the collapse... happens") is now stale -- the collapse itself was declined in favour of the narrower Option B (section 42.2), which touches only `PixelLayer`'s internal change-tracking and does not touch `openProjectFromStore()` or the gallery Resize flow at all. 44.4b has no real dependency on 42.2's work and can be picked up independently whenever it's prioritized; it was never actually blocked by the layer-class question, only loosely associated with it because both were being discussed in the same session.

### 44.4a Portrait tile isolation doesn't block drawing outside the isolated tile

**Symptom, as reported:** with Portrait tile isolation on (the dimming overlay showing which 40x40 tile is "active"), every tool (pencil, eraser, fill, wand) can still draw on the dimmed, supposedly-inactive tiles.

**Investigated, root cause found (not a regression):** `#portraitTileIsolationOverlay` and its `.pt-mask` dimming rectangles are explicitly `pointer-events: none` in the CSS. This was never built to block input -- it is, and always has been, a purely visual "which tile am I on" indicator. No code path anywhere checks "is isolation on, and is this point outside the isolated tile" before allowing a draw; `plot()`'s only Portrait-specific gate is a completely different check (whether the current colour exists in that tile's own palette).

**What a real fix would need:** a boundary check added to `plot()` (and the fill/wand equivalents) comparing the point being drawn against `portraitActiveTileKey`'s bounds whenever `portraitTileIsolation` is on, rejecting the draw if it's outside. Genuine new logic, not a config flip -- correctly sized as its own piece of work, not a quick fix.

**Status:** held. Flagged for consideration alongside the section 42.2 collapse and the A/B/C/D architecture comparison, since it touches the same drawing-tool code paths (`plot()` and friends) that comparison will already be auditing.

### 44.4b Cancelling "Resize Canvas" from the gallery still leaves the project open

**Symptom, as reported:** tapping "Resize" on a project card in the gallery context menu, then tapping Cancel on the resize dialog, does not return to the hub -- the project stays fully open.

**Investigated, root cause found:** the context-menu handler (`ctx-resize` click listener) calls `openProjectFromStore(id)` -- a full, immediate, irreversible commit (tears down any previous session's canvases, rebuilds `frames`/`gridW`/`gridH`/`layers` from the stored project, right then) -- **before** showing the resize dialog. By the time Cancel is visible, the project is already fully open; `closeResizeCanvasSheet()` correctly closes the dialog but was never wired to also undo step one, because step one was never designed to be undoable.

**Two options discussed with the person, in plain terms:**
- **Option A (true "don't commit until confirmed"):** `openResizeCanvasSheet()` currently reads `gridW`/`gridH` directly from already-live globals (and bails out entirely if `frames.length` is falsy) -- it structurally cannot show correct numbers without the project already being loaded. True option A would require new code to peek at a stored project's dimensions from `projectStore` directly, without committing state, so the dialog can render correct numbers *before* `openProjectFromStore` runs, and only actually open the project on Confirm. This is real new logic, not a reorder.
- **Option B (same end result, smaller change):** keep the current open-then-show-dialog order as-is, but make Cancel also navigate back to the hub (equivalent to pressing Main Menu) instead of only closing the dialog. From the person's perspective the outcome is identical either way -- tap Resize, see the dialog, tap Cancel, land back at the hub -- Option B just gets there by briefly entering and then leaving, rather than never entering at all.
- The person selected **Option A** in principle, but after the "true A requires new peek-without-committing logic" scope was clarified, chose to **flag and hold this entirely** rather than commit to either option's implementation cost right now, specifically because it should be considered alongside the section 42.2 collapse and the A/B/C/D comparison (both touch `openProjectFromStore` and project-loading behaviour directly).

**Status:** held, Option A preferred if/when this is picked up, but not started.

## 44.5 Real on-device flip timing confirmed (V1_26)

The person re-ran the flip test on `V1_26`, with the new permanent timing (section 44.3) active for the first time on a real device:

```
flipHorizontalBtn: paint-tick delay 3.0ms, operation 11.0ms, total 14.0ms
```

**14ms total**, correctly routed through `type=image` (`ImageLayer`). This closely matches the original synthetic Node.js benchmark from the ABCD investigation (~14ms for the flat-array flip in isolation, before the `window.ImageLayer` bug was found) — confirming that estimate was a good predictor once the real code path was actually reachable, and confirming the earlier buggy-path number (598ms, `PixelLayer`'s Proxy-tracked array-of-arrays) really was Proxy overhead specifically, not some other hidden cost. The flip/undo bug from sections 42 and 44.1 is fully closed, with real on-device numbers now on record for both the broken and fixed paths.

## 44.6 Portrait tile isolation bug (44.4a): confirmed unrelated to the ImageLayer/PixelLayer (ABCD) question

The person asked whether 44.4a (Portrait tile isolation not blocking drawing outside the active tile) is related to the ABCD architecture comparison (section 42.2, sections 45+). It is not, and should be treated as fully independent:

- ABCD concerns how raster pixel **storage and undo-tracking** work (`PixelLayer` vs `ImageLayer`) -- a question about what happens *after* a draw is already permitted.
- The Portrait isolation bug concerns **input gating** -- whether a draw at a given point should be allowed through *at all*, based on which 40x40 tile is currently active. This sits entirely above the storage layer; the missing check would need to live in `plot()` (and the fill/wand equivalents) regardless of which layer class ends up handling storage.
- Portrait canvases are also small by construction (tile-based spritesheets built from 40x40 tiles essentially never cross the 999px threshold), so this bug has near-zero practical overlap with the size-threshold logic ABCD is about.

**Flagged for the next build, independently of ABCD** -- per the person's request, this should not wait on or be bundled with the architecture comparison. It remains scoped as described in 44.4a: a boundary check needed in `plot()` and friends, comparing the draw point against `portraitActiveTileKey`'s bounds whenever `portraitTileIsolation` is on.

------------------------------------------------------------------------

# 45. V1_28 Bug-Fix Batch (RECONSTRUCTED -- see note below)

**Note on this section:** this section, and section 46, were found missing from this document after an interrupted turn left the file in a partial state -- the person caught this via a save-to-iPhone crash that turned out to be a symptom of truncated content, not an app bug. The actual code (`Pixel_art_app_V1_28.html`, `BUILD_VERSION = 'V1_28'`) and the Bugs Squashed companion doc (entries 1.1-1.3) were both confirmed intact and used as the source of truth to reconstruct this section, rather than relying on memory of the original turns. If anything here reads as slightly different in phrasing from what a person following along in the original conversation remembers, the code and the Bugs Squashed doc are the more reliable references going forward.

Four items requested together, all shipped in `V1_28`:

## 45.1 New Canvas sheet hint text removed

The "≤999px uses pixel rendering; larger canvases use image rendering" hint text (shown under the Import Image button and under the Pixel Art profile choice in the New Canvas sheet) was removed entirely, per the person's request. This text existed in two places that both needed clearing -- `openNewCanvasSheet()`'s initial build of `#ncm-hint`, and `selectProfile()`'s re-render of the same element on every profile switch -- missing the second would have let the text reappear the moment someone tapped back to the Pixel Art profile button after seeing it cleared once.

## 45.2 Pixel cursor now respects Portrait tile isolation

See Bugs Squashed entry 1.2 for the full investigation. `updateCursor()` only checked whole-canvas bounds, with no awareness of Portrait tile isolation, even after `PixelLayer.plot()` was fixed to block drawing outside the isolated tile in `V1_27`. Rather than duplicate the boundary-check logic a second time, it was factored into a new shared function, `isPointOutsidePortraitIsolation(x,y)`, called by both `PixelLayer.plot()` (updated to use it instead of its own inline copy) and `updateCursor()`. This is now referenced directly in section 4's Portrait sub-section.

## 45.3 Flip's loading-state UI removed; `runWithLoadingButtonState` marked stale

Per the person's explicit request. `flipActiveLayerH()`/`flipActiveLayerV()` no longer call `runWithLoadingButtonState(...)` -- their bodies run directly instead, so the flip buttons no longer disable or relabel to "LOADING..." during a flip. `runWithLoadingButtonState` itself was **not deleted** -- it's marked with an explicit "STALE / NOT CURRENTLY CALLED" comment explaining why it was orphaned and how to verify before ever reusing it (a genuinely slow future synchronous operation could still legitimately want this exact pattern). While making this edit, a genuinely orphaned duplicate comment was also found and removed -- an "Erases every pixel..." fragment misattached above `runWithLoadingButtonState` that actually belonged to `deleteSelection()`, which already had its own correct copy.

## 45.4 Second real undo bug found and fixed: `PixelLayer.setPixelData()`

See Bugs Squashed entry 1.3 for the full investigation. Distinct from the `V1_25` `window.ImageLayer` bug -- this is the small-canvas (`PixelLayer`) path, which was never affected by that fix. `PixelLayer.flipHorizontal()`/`flipVertical()` call `this.setPixelData(newData)`, which does `this.pixelData = makeTrackedPixelData(...)` -- a direct property reassignment, not a write *through* the existing tracked `Proxy`, so neither level of the Proxy's `set` trap ever fired and `_historyCapture.before` never got populated. Fixed by having `setPixelData()` explicitly capture the outgoing grid into `_historyCapture.before` before replacing `this.pixelData`, mirroring what the Proxy's own trap does for a single-column reassignment, applied to the whole grid at once.

**Real-world consequence found while checking the blast radius:** `clearLayerAt()` (per-row layer-clear button) and `executeClear()` (main Clear button) both already wrapped `setPixelData()` in `beginEdit()`/`commitEdit()` exactly like the broken flip did -- meaning "clear layer" was very likely also silently failing to record undo history on any small canvas, before this fix. Both benefit from the fix automatically since it lives in `setPixelData()` itself, not in flip specifically.

## 45.5 Dead-code sweep confirmed clean

Requested alongside the bug fixes. The same dead-function-scan methodology from earlier sessions (top-level function/class name extraction, word-boundary occurrence counting, manual investigation of any candidate with count ≤ 1) and an equivalent CSS-class sweep were both run against `V1_28`. Result: **zero candidates found** -- the codebase's earlier cleanup passes (sections 41.6, 39.8, and the WebGL2 removal's own sweep) have held up; there was nothing left to remove at this point.

**Verification:** all four items syntax-checked and harness-diffed clean at the time; every call-count delta was individually traced and explained (new function `isPointOutsidePortraitIsolation`, comment-only deltas for the rest). `<div>` tag balance confirmed. `BUILD_VERSION` updated to `'V1_28'`.

------------------------------------------------------------------------

# 46. Core Code Philosophy split into its own document, given authority over this one

A new document, **`Pixel_art_app_core_code_philosophy.md`**, was created at the person's explicit direction, separate from this handoff file and from the Bugs Squashed companion. Unlike this document (which describes the current state of the code and its history) and the Bugs Squashed doc (bug narratives), the new document is meant to be the small, stable *root* of why the app is built the way it is and how decisions about it get made -- changed rarely, and only deliberately, by the person's own hand.

## 46.1 What the core philosophy document contains

Written substantially in the person's own words, then structured by Claude:

- **What the app is**: touch-first, PC-compatible, single-file HTML pixel-art editor, a MediBang Paint alternative for iOS, built within the real constraints of the iOS web browser (memory limits, computational overhead).
- **The engine/algorithm decision rule** (the actual core of the document): no engine, data structure, or algorithm already in the codebase is authoritative just because it's already there -- every one is a decision that was made and can be revisited. Any new engine/algorithm decision (or any proposal to change an existing one) must go through a four-step process: (1) Claude researches it properly, including a real web search for how comparable real-world tools handle the same problem, not just reasoning from what's already in the codebase; (2) Claude compiles genuine advantages and disadvantages, stated separately for memory and for computation since the two are not interchangeable under the app's constraint ranking (see 46.2); (3) the person and Claude both reach actual agreement before anything is implemented, not Claude recommending and the person rubber-stamping; (4) every proposal is checked against whether it could be made lighter or faster -- this question itself is never skipped, though *acting* on a "yes, but it's risky" answer can be knowingly traded off against the risk of editing complex, load-bearing code, and a comparable reference (an older build, a public code example) should be checked first to de-risk that tradeoff before falling back to accepting the risk.
- **What motivated this rule, concretely**: two real, named cases from this project's own history -- the WebGL2 renderer (added on an unverified crash-prevention assumption, later found to cost *more* memory than the Canvas2D alternative it was meant to improve on, with a real iOS-specific leak risk, and removed entirely in `V1_21_wip`/section 41.7) and the `PixelLayer` Proxy-based change-tracking (never benchmarked against the alternative until directly asked, leading to the still-not-yet-implemented "Option B" decision in section 42.2).

## 46.2 The constraint ranking, refined across follow-up messages

The person clarified this in several passes, and the final, current ranking is:

**Responsiveness > Lightweight (where, within Lightweight, memory-safety > raw computation speed) > small file size.**

- **Responsiveness and lightweight are both hard constraints** -- not goals to trade away, unlike an earlier draft of this document which had only responsiveness as hard and lightweight as a stretch goal. The person explicitly upgraded lightweight to hard-required in a follow-up message.
- **If the two ever genuinely conflict, responsiveness wins** -- the person kept this tiebreaker explicitly when upgrading lightweight, rather than making the two equally absolute.
- **Within "lightweight," memory beats computation** -- the person's own words: a slower computation is better than an app crash, which could lose real, unsaved work. When a proposal has to choose between more CPU time or more memory, prefer more CPU time.
- **Small file size remains a separate stretch goal**, not ranked alongside the other two -- it can be traded away for either hard constraint, or for correctness, without hesitation.

## 46.3 Authority statement: this document now overrides the handoff document

The person, writing in their own words, explicitly declared `Pixel_art_app_core_code_philosophy.md` **authoritative over this document** -- not a soft preference, a deliberate authority change. The required reading order for a new session or agent is now:

1. `Pixel_art_app_core_code_philosophy.md` first, in full.
2. This document (`Pixel_art_app_code_philosophy_updated_handoff_V17.md`) second -- read for its handoff/build-history/code-documentation value, but any claim in it that reads as foundational or authoritative is subordinate to the core philosophy document wherever the two disagree.
3. `Pixel_art_app_bugs_squashed_V1.md` is **optional**, not part of the required sequence -- read only when the task specifically calls for bug history or a comparison against past bugs.

All three documents were updated to state this same reading order and precedence consistently, from their own perspective, so the correct order is discoverable regardless of which file a session happens to open first. This document's own opening section states its subordination explicitly; the core philosophy document's own section 2 rule (never treat something as authoritative just because it's already established) was noted as applying retroactively to this document's own sections 1-30, which describe decisions already made, not decisions that are exempt from being revisited.

**Practical effect on future sessions:** any future architecture/engine/algorithm proposal must go through the core philosophy document's four-step process (46.1) and respect the constraint ranking (46.2), even where this document's own sections 1-30 might read as having already settled the matter. This document remains the correct place for build history, bug-adjacent lessons (section 30's danger zones), and code documentation -- it just no longer sets the app's fundamental direction on its own.
