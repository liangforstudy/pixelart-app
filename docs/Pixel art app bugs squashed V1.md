# Pixel Art App — Bugs Squashed Log

**Reading status: optional, not part of the required reading sequence.** The required order for a new session is `Pixel_art_app_core_code_philosophy.md` first, then `Pixel_art_app_code_philosophy_updated_handoff_V17.md` — this document sits outside that chain. Read it only when the person or the task specifically calls for bug history, or when asked to compare current behaviour against a past bug. Do not treat skipping this file as incomplete context-gathering for a session that doesn't need it.

This is a companion document to the main handoff/philosophy file
(`Pixel_art_app_code_philosophy_updated_handoff_V17.md`). It exists
because the main document was getting hard to scan for "what bugs have
actually been found and fixed" — that history was scattered across many
chronological session-log sections, interleaved with feature additions,
renames, and cleanup notes.

**Division of labour between the two documents, going forward:**

- **This document** — the actual bug narratives: what broke, how it was
  found, what the real root cause turned out to be, and what fixed it.
  Short entries, one per bug, newest first within each numbered section.
- **The main handoff document** — architecture, philosophy, roadmap, and
  the *lessons/best-practices/danger-zones* that bugs taught us (see its
  section 30, "Known architectural danger zones," and section 33,
  "Regression-Prevention Procedure") — not the blow-by-blow of each bug
  itself. When a bug here teaches a durable lesson, that lesson gets
  written into the main doc's danger-zones section, with a pointer back
  here for the full story.

**Retroactive scope:** per the person's explicit choice, this document
is **forward-only**. Section 0 below is a short index of bugs found
*before* this document existed, with one-line summaries and pointers
back to their original write-ups in the main handoff doc (which still
contain the full narratives — nothing was deleted or duplicated from
there). Every bug found from here on gets its full write-up in this
document instead.

Both documents should always cross-reference each other by name/section
so neither one drifts into being the only complete copy of anything.

------------------------------------------------------------------------

# 0. Index of Bugs Found Before This Document Existed (pointers only)

Full narratives for all of these remain in the main handoff document at
the sections indicated — not duplicated here.

| Bug | Status | Main doc section |
|---|---|---|
| Pinch-zoom centered on canvas center instead of the pinch midpoint | Fixed (V1_6) | 36.1–36.3 |
| Paint bucket undo — investigated after a report; turned out to be the memory-budget system evicting older entries, not a missing undo registration | Not a code bug (explained) | 37.1 |
| Confirm-delete (wand tool, rectangle-selection tool) silently did nothing | Fixed (V1_7) — native `confirm()` replaced with the app's tap-twice pattern | 37.3 |
| Selection (wand + rectangle) persisted across switching to a different project | Fixed (V1_7) | 37.4 |
| A drawing stroke could cross a Portrait 40×40 tile boundary mid-drag | Fixed (V1_7) | 37.8 |
| Bucket-fill undo appeared broken under a specific reproduction sequence; root cause never fully confirmed at the time, later found to be unrelated to the actual eviction-order logic (which was correct) | Investigated, not conclusively resolved at the time — see the real fix below (flip/undo bug) for the eventual full resolution of the related symptom | 41.8 |
| Flip buttons had no loading indicator despite `flipHorizontal`/`flipVertical` being long, fully synchronous operations with no yield point | Fixed (V1_23) | 41.12 |
| **The big one:** imported large (>999px) photos always became `PixelLayer` instead of `ImageLayer`, regardless of the actual size-threshold logic, making every large-canvas operation (especially flip) far slower than intended and leaving Undo/Redo empty after a flip | **Root-caused and fixed (V1_25)** — `window.ImageLayer` was never actually being set; `class` declarations don't auto-attach to `window` the way `var`/`function` do. This also corrected a wrong claim asserted (without verification) in an earlier session that they did. | 42.1, 44.1, 44.2 |
| Portrait tile isolation overlay is purely visual (`pointer-events: none`) — every tool can still draw on the dimmed, supposedly-inactive tiles | **Fixed (V1_27)** — see section 1.1 below for the full write-up (the real fix location turned out to be `PixelLayer.plot()` itself, not the places originally guessed at) | 44.4a, 44.6, and 1.1 below |
| Cancelling "Resize Canvas" from the gallery context menu still leaves the project fully open (the project is committed via `openProjectFromStore()` before the dialog even appears) | **Not yet fixed** — flagged, held, two options scoped (A: don't commit until confirmed, needs new peek-without-committing logic; B: keep current order, make Cancel also return to the Hub) | 44.4b |

------------------------------------------------------------------------

# 1. Bugs Found From This Point Forward

## 1.1 Portrait tile isolation didn't block drawing outside the isolated tile

**Reported:** "I'm still able to draw through the portrait opacity layer, pencil, eraser, fill, wand" — every tool could still draw on the dimmed, supposedly-inactive tiles while isolation was on.

**Investigated:** first confirmed the overlay itself is `pointer-events: none` by design (index entry above, originally found a few sessions before this document existed) — purely visual, never meant to block input on its own. The real fix needed a boundary check somewhere in the actual pixel-write path. Traced every function that ends up writing a pixel to find the true, single choke point rather than guessing at one call site:
- The global `plot(x,y)` wrapper function — used by bucket fill (both global and contiguous flood-fill modes call `plot(fx,fy)`/`plot(nx,ny)` per touched pixel) and, indirectly, nothing else important.
- `applyPixelToolAt`/`blendPixel` — the actual dispatcher for every brush-family tool (Pencil, Brush, Soft Brush, Hard Eraser, Soft Eraser). Found that these call `layer.plot(...)` **directly**, bypassing the global `plot()` wrapper entirely — meaning a fix at the wrapper level alone would have missed Pencil and Hard Eraser, the two tools actually reachable in Portrait mode (`PORTRAIT_TOOL_FALLBACK` redirects Brush/Soft Brush to Pencil and Soft Eraser to Hard Eraser there).
- `performWandDelete()` — also calls `layer.plot(x,y,null)` directly, same pattern.
- Confirmed `performWandSelection()` (the Wand tool's actual selection step, as opposed to deleting the selection) never calls `.plot()` at all — it only reads pixels into a selection mask, so it correctly continues to allow selecting across tile boundaries; only the destructive follow-up action (delete) needed gating, matching the bug report's intent.

**Root cause:** no code anywhere checked tile membership before writing a pixel. Confirmed there is exactly one true low-level choke point every one of the above paths funnels through: `PixelLayer.plot(x, y, color)`, the method on the class itself (not the same-named global wrapper function).

**Fix (`V1_27`):** added the boundary check directly inside `PixelLayer.plot()`, right after the existing bounds check: when `selectedProfile === 'portrait' && portraitTileIsolation` is true, compute `portraitTileKeyForPoint(x,y)` and silently no-op if it doesn't match the frozen `portraitActiveTileKey`. Placing the check inside the class method itself (rather than duplicating it across every caller) guarantees every current and future drawing path is covered automatically, with no risk of a caller being missed.

**Lesson:** when multiple callers all need the same guard, look for the actual lowest-level shared function they all funnel through before patching each caller individually — a same-named wrapper function (the global `plot()`) is not necessarily the real choke point; several important callers (`applyPixelToolAt`, `blendPixel`, `performWandDelete`) bypassed it entirely and called the class method directly. Added to the main handoff doc's danger-zones section (30) as a new entry.

## 1.2 Pixel cursor didn't respect Portrait tile isolation either

**Reported:** "Cursor still rendering in forbidden grayed out layers" — after 1.1's fix made drawing correctly stop at the isolated tile boundary, the cursor preview still moved and displayed freely across the whole canvas, implying you could draw where you actually couldn't anymore.

**Investigated:** `updateCursor()` (the pixel-cursor preview logic) only ever checked whole-canvas bounds (`x >= 0 && x < gridW && ...`), with no awareness of Portrait tile isolation at all — a separate gap from 1.1's, in a different function, that 1.1's fix didn't touch.

**Root cause:** same missing-boundary-check pattern as 1.1, just in a second location that duplicates the same rule instead of sharing it.

**Fix (`V1_28`):** extracted a shared `isPointOutsidePortraitIsolation(x,y)` function (checks `selectedProfile==='portrait' && portraitTileIsolation` and compares `portraitTileKeyForPoint(x,y)` against the frozen `portraitActiveTileKey`) and had both `PixelLayer.plot()` (updated to call it instead of its own inline copy) and `updateCursor()` call it. One rule, two callers, instead of two copies of the same rule that could drift apart.

**Lesson:** when a boundary/gating rule needs to apply to more than one caller, make it a named shared function immediately rather than copy the check inline a second time — see the "same-named wrapper" danger-zone entry (section 30) for the related, broader version of this lesson from 1.1.

## 1.3 Flip on a small (<999px) canvas didn't log an undo step either

**Reported:** "Flipping canvas less then 999px did not log undo step, history not showing, undo grayed out, but both flips successful." Distinct from the earlier `ImageLayer`/`window.ImageLayer` bug (section 44.1) — this is the `PixelLayer` (small-canvas) path, which was never affected by that bug, so it needed its own investigation rather than being assumed to be the same root cause.

**Investigated:** traced `beginEdit()`/`commitEdit()` for the `PixelLayer` (`type:'pixels'`) path and confirmed it was structurally correct -- the bug had to be somewhere in how the actual pixel data gets written during a flip, not in the undo-transaction bookkeeping around it. Found that `PixelLayer.flipHorizontal()`/`flipVertical()` call `this.setPixelData(newData)`, not `this.plot()` per pixel like every other drawing tool. `setPixelData()` does `this.pixelData = makeTrackedPixelData(this, w, h, data)` -- a direct **property reassignment** of `this.pixelData` itself, not a write *through* the existing tracked `Proxy` (e.g. `this.pixelData[x][y] = value`, which is what actually triggers `makeTrackedPixelData`'s `set` traps and populates `_historyCapture.before`). A property reassignment bypasses both levels of the Proxy entirely -- `_historyCapture.before` never gets touched, `commitEdit()`'s diff comes back with zero changes, and nothing gets pushed to `undoStack`.

**Root cause:** `setPixelData()`, the bulk-replace method every flip/resize/clear operation funnels through, silently bypasses the exact change-tracking mechanism (`makeTrackedPixelData`'s Proxy) that every single-pixel write (`plot()`) relies on, because a whole-property reassignment doesn't go through a Proxy `set` trap the way a property-of-a-property write does.

**Fix (`V1_28`):** `setPixelData()` now explicitly captures the full outgoing grid into `_historyCapture.before` (if a capture is active) *before* replacing `this.pixelData`, mirroring what the Proxy's own `set` trap already does for a single-column reassignment, just applied to the whole grid at once.

**Real-world consequence found while checking the blast radius:** every other caller of `setPixelData()` had the exact same silent gap. `clearLayerAt()` (the per-row layer-clear button) and `executeClear()` (the main Clear button) both already wrap `setPixelData()` in `beginEdit()`/`commitEdit()`, exactly like the broken flip did -- meaning "clear layer" was very likely also silently failing to record undo history, on any small canvas, before this fix. Confirmed both callers now benefit from the same fix with no separate change needed, since the fix lives in `setPixelData()` itself.

**Lesson:** a Proxy-based change-tracking system only catches writes that actually go *through* the Proxy (`obj.prop = x`, `obj[i][j] = x`) -- a bulk operation that reassigns the tracked property itself (`this.trackedThing = newTrackedThing`) silently escapes it completely, even though it looks like "the same kind of write" at a glance. Any future bulk-replace method built against a Proxy-tracked structure needs its own explicit before-capture; it cannot rely on the Proxy to catch it. Added to the main handoff doc's danger-zones section (30).

## Entry template

```
## [N.N] Short descriptive title

**Reported:** what the person actually observed, in their words where useful.

**Investigated:** what was checked, and in what order, before concluding
anything — especially anything ruled OUT, so a future session doesn't
re-check the same dead end.

**Root cause:** the actual mechanism, precisely. Not "it was fixed," the
*why*.

**Fix:** what changed, which build it shipped in.

**Lesson, if any:** does this teach a durable rule that belongs in the
main handoff doc's danger-zones section (30)? If so, note it was added
there, with a one-line summary of the rule itself.
```
