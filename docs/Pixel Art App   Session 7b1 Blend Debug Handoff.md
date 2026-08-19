# Pixel Art App — Session 7b-1 Blend-Mode Debug Handoff

**Documented against:** `Pixel_Art_App_V1_38.html`, working copy at `/home/claude/work/Pixel_Art_App_V1_38.html`, `BUILD_VERSION = 'V1_38'`.

**Status: UNRESOLVED, mid-investigation.** This file is a full record of what was built, what was tested, and what's still open, so the next session can resume without re-deriving any of this.

------------------------------------------------------------------------

## 1. What this session set out to do

Continue Session 7 (roadmap item 12, group blend modes) into **Session 7b-1**: make a group's blend-mode dropdown (already present in the UI, already persisting `group.blendMode`, but previously a no-op — see Session 7a's findings) actually render live, on-screen, as the person draws/edits.

Chosen approach (agreed with the person, see prior conversation turns): use the browser's native CSS `mix-blend-mode` + a per-group DOM wrapper `<div>`, rather than a hand-built canvas-recompositing pipeline. Rationale: smaller, more maintainable, rides on browser-native, spec-correct blending instead of reimplementing Photoshop-style blend math by hand — confirmed via web search that `mix-blend-mode` is Baseline/widely-supported and covers the same mode vocabulary the app's dropdown already exposes (`multiply, screen, overlay, darken, lighten`, source-over/Normal).

## 2. What was actually built (all present in the current working file)

### 2a. `reindexDom()` — generalized to be group-aware

**Location:** search for `function reindexDom` in the file.

Previously: flat `layers.forEach(l => container.insertBefore(l.el, pixelCursor))` — every layer, unconditionally, direct child of `#container`.

Now: for each layer, looks up its immediate parent group via the existing `findLayerNode()` helper. If that parent group has a `blendMode !== 'source-over'`, the layer's canvas gets moved into a **per-group wrapper `<div>`** (created on demand) instead of being a direct child of `#container`. Layers not in an active-blend-mode group are completely unaffected — still direct children of `#container`, byte-identical to pre-session behavior.

```js
function groupBlendWrapperId(groupId) { return 'group-blend-wrap-' + groupId; }
function getOrCreateGroupBlendWrapper(groupId, blendMode) {
    const id = groupBlendWrapperId(groupId);
    let wrap = document.getElementById(id);
    if (!wrap) {
        wrap = document.createElement('div');
        wrap.id = id;
        wrap.className = 'group-blend-wrap';
        wrap.style.cssText = 'position:absolute; inset:0;';
        container.insertBefore(wrap, pixelCursor);
    }
    wrap.style.mixBlendMode = blendMode;
    return wrap;
}
function pruneStaleGroupBlendWrappers(activeGroupIds) {
    container.querySelectorAll('.group-blend-wrap').forEach(el => {
        const gid = el.id.slice('group-blend-wrap-'.length);
        if (!activeGroupIds.has(gid)) el.remove();
    });
}
function reindexDom() {
    const f = frames[activeFrameIndex];
    const tree = f ? ensureFrameLayerTree(f) : null;
    const activeGroupIds = new Set();
    layers.forEach(l => {
        let targetParent = container;
        if (tree) {
            const found = findLayerNode(tree, l.id);
            const parentGroup = found && found.parent;
            if (parentGroup && parentGroup.blendMode && parentGroup.blendMode !== 'source-over') {
                targetParent = getOrCreateGroupBlendWrapper(parentGroup.id, parentGroup.blendMode);
                activeGroupIds.add(parentGroup.id);
            }
        }
        if (targetParent === container) container.insertBefore(l.el, pixelCursor);
        else targetParent.appendChild(l.el);
    });
    pruneStaleGroupBlendWrappers(activeGroupIds);
}
```

**Important correction made mid-session:** the first version of `getOrCreateGroupBlendWrapper` also set `wrap.style.isolation = 'isolate'`. This was **removed** after live testing showed it broke the blend entirely — `isolation:isolate` on the same element as `mix-blend-mode` makes that element form its own stacking context and blend against its own (empty/transparent) background, not against whatever's behind it. Confirmed via web search (see `mix-blend-mode` spec discussion: "an element belonging to a stacking context is isolated from the rest of the content outside that stacking context"). **Do not re-add `isolation:isolate` to this wrapper** without a very good reason — it was tried and made things strictly worse (no blend at all vs. "blend visually not showing").

### 2b. `applyGroupBlendMode()` — wired to actually call `reindexDom()`

**Location:** search for `function applyGroupBlendMode`.

```js
function applyGroupBlendMode(group){
    if(group) group.blendMode=group.blendMode||'source-over';
    reindexDom();
    refreshHookedComposites();
}
```

Previously this only set the field and called `refreshHookedComposites()` — it never triggered any DOM change, which is exactly why the dropdown was a documented no-op before this session. This is the connection that makes selecting a mode in the dropdown actually attempt to take visual effect.

### 2c. `flattenGroupSubtreeToCanvas()` — Session 7a's output, unrelated to 7b-1's bug

**Location:** search for `function flattenGroupSubtreeToCanvas`.

This is **verified working correctly** (tested twice, live, on-device — see section 4 below) and is **not implicated** in the current bug, since it's a canvas-drawing function with no dependency on CSS `mix-blend-mode` at all. It's the intended mechanism for **export/flatten** (wiring into `flattenLayersToCanvas`/thumbnail generation is still a separate, not-yet-done task — see Open Items).

### 2d. Two TEMP diagnostic tools in the Debug drawer

Both still present, both intentionally left in for continued debugging:

- **`testFlattenFirstGroup()`** / button "🧪 PREVIEW FIRST GROUP FLATTEN" — shows `flattenGroupSubtreeToCanvas`'s output for the first group found. Confirmed working correctly.
- **`testGroupBlendWiring()`** / button "🧪 CHECK BLEND WIRING (writes to Log below)" — checks wrapper existence, `mixBlendMode` computed-ish value (actually `wrap.style.mixBlendMode`, which is NOT the same as `getComputedStyle().mixBlendMode` — see Open Items, this is a known weakness in the test itself), and whether member-layer canvases are inside the wrapper. **This test currently reports PASS even though the visual blend does not work** — meaning the test is checking necessary-but-not-sufficient conditions. It should not be trusted as proof of correctness until it's rewritten to check computed style and/or actual rendered pixel color.

## 3. The bug: what's actually wrong

**Symptom:** with a group containing 2+ solid-color pixel layers, blend mode set to Multiply (or any non-Normal mode), the group renders as **plain opaque top-layer color** — no visible darkening/blending against anything, whether the backdrop is the canvas checkerboard, another layer inside the same group, or a third layer placed outside/below the group.

## 4. Everything that WAS verified correct (ruled out as the cause)

Each of these was independently confirmed via direct browser inspection (not just code-reading) on the person's actual desktop Edge, local file (`file:///C:/Users/Agile/Downloads/Pixel_Art_App_V1_38_1.html`), not an iframe:

1. **`flattenGroupSubtreeToCanvas()` itself** — confirmed correct twice: once via manual console test with different colors on base/mask, once via the Debug-drawer button test with black-on-black (stricter case). Both times the flattened output correctly matched live edits. **This function is solid.**
2. **Wrapper DOM structure** — `document.querySelectorAll('[id^="group-blend-wrap-"]')` confirmed the wrapper exists, with `children.length === 2`, `childTags === 'CANVAS#,CANVAS#'` — both member-layer canvases really are inside it.
3. **`mixBlendMode` computed style** — `getComputedStyle(wrapper).mixBlendMode` returned `'multiply'` correctly (this is the browser's own computed value, not just what was set via JS — a genuinely strong signal that the CSS property is live and active).
4. **Actual pixel data in both canvases** — sampled via `getImageData` at canvas center: one canvas `rgba(0,0,255,255)` (solid blue), the other `rgba(255,0,0,255)` (solid red), both fully opaque, both 32×32. Not a data problem.
5. **Wrapper geometry** — `getBoundingClientRect()` on the wrapper showed a size/position essentially matching `#container`'s own rect (512×512 vs. container's 515×515, position within ~2px). Not a sizing/positioning problem.
6. **`#container`'s own `transform`** — was found to have `transform: matrix(1,0,0,1,0,0)` (an identity transform, but present as an inline style rather than `none`) — this is a known trigger for creating an unwanted stacking-context boundary per multiple sources found via search. **Directly tested**: set `document.getElementById('container').style.transform = 'none'` live in console — **no change**, still no blend. Ruled out.
7. **iframe context** — the very first debugging round happened on w3schools.com (which runs code in an iframe), and there's a documented Chrome+iframe+mix-blend-mode bug. **Directly tested**: same result reproduced in a real desktop browser tab, local file, no iframe. Ruled out.
8. **Whether `mix-blend-mode` works AT ALL in this browser environment** — directly tested with two bare `<div>`s appended straight to `document.body`, no relation to the app's DOM, red background + blue-with-multiply. **Result: it worked** — the overlap region rendered as dark navy/black, which is mathematically correct for red×blue Multiply (both channels have no overlap, product is 0). This is strong evidence the browser and GPU compositing are capable of correct blending in general.
9. **`#container`'s own background** — has both `background-color: #808080` AND a checkerboard `background-image` — ruled out the specific "Chrome 58+ transparent-background bug" since a real `background-color` is present.
10. **DOM child order / z-index of siblings** — walked every direct child of `#container` via `[...container.children].forEach(...)`; found `pixel-cursor` has `zIndex:200` and `display:block` (live), everything else with an explicit z-index is `display:none`. The wrapper itself is DOM index 0 (first/bottom), `zIndex:auto`. This alone doesn't explain the bug (a z-index difference wouldn't cause "no blend at all", just possible occlusion) and wasn't conclusively tested as a fix (no test isolated this variable directly — see Open Items).

## 5. What's still genuinely unknown / NOT yet tested

- **Point 10 above was never isolated as its own test.** It's possible `pixel-cursor` or some other sibling with `display:block` and a z-index is painting over the blended result, hiding it, even though the blend itself might be computing correctly underneath. This was the leading theory when the session was paused, but never directly confirmed or denied (e.g., by temporarily hiding `pixel-cursor` and re-checking, or by screenshotting/sampling the actual rendered pixel color at the overlap point).
- **The last screenshot session (nested-group nonsense)**: the person was experimenting with dragging one Group into another / reordering, and the console dump showed `mix-blend-mode: screen` on the wrapper (not `multiply` as expected) — this wasn't chased down. It's unclear whether this was a genuine nested-group edge case surfacing a real bug, or just the person having selected a different mode in the UI without realizing it. **Needs re-confirmation with a clean, simple, single-group test case before drawing any conclusion from it.**
- **No test has yet directly sampled the actual on-screen rendered pixel color** at the point where the group visually overlaps a backdrop layer. All evidence so far is either (a) confirming inputs are correct (pixel data, wrapper geometry, computed style) or (b) visual inspection by the person, which has been ambiguous/uncertain in the last couple of rounds ("looks like hard edge to me", "can't tell tho"). The single most direct diagnostic **not yet run**: sample `document.elementFromPoint(...)` combined with something like temporarily inserting a 1x1 sampling canvas via `drawWindow`-equivalent — genuinely difficult from pure JS without a screenshot API, but DevTools' own color picker (the eyedropper icon in the Styles/Elements panel, or right-click → Inspect → hover) could give a direct, trustworthy answer if used to sample the live rendered page at the overlap point.
- **DevTools' Layers panel** (More tools → Layers, or the 3D layer view) was suggested as a next step but never actually opened. This would show Chrome's real compositing layers and could reveal whether the blend is being computed on a separate GPU layer that isn't correctly composited back in.

## 6. Concrete next steps for the next session

In rough priority order:

1. **Rewrite `testGroupBlendWiring()` to check `getComputedStyle(wrapper).mixBlendMode` instead of `wrapper.style.mixBlendMode`**, and add a genuine pixel-sample check if feasible (e.g., temporarily render the wrapper's content to an offscreen canvas via `drawImage` from the live DOM — note: this may not be possible for arbitrary live DOM/CSS blending, since `drawImage` can't capture CSS-composited output directly; may need `html2canvas` or similar, or rely on DevTools instead).
2. **Directly test the `pixel-cursor` occlusion theory**: `document.getElementById('pixel-cursor').style.display = 'none'` live, then re-check the blend visually. Cheap, fast, rules in/out a real candidate.
3. **Open Chrome DevTools' Layers panel** and inspect the actual compositing layers around the group wrapper — this is the most direct, authoritative way to see what Chrome itself thinks is happening, rather than continuing to infer from computed styles.
4. **Re-run the clean, single-group (not nested) red/blue-in-group + green-outside-group test from scratch**, screenshot the DevTools Elements panel's "Rendering" tab with "Paint flashing" or the built-in contrast/color picker to get an authoritative pixel sample at the overlap point, before trying anything else.
5. Only after the above: consider whether the fundamental approach (CSS `mix-blend-mode` + DOM wrapper) needs to be abandoned in favor of the originally-rejected offscreen-canvas-recompositing approach — but this should be a last resort, not a first reaction, since points 1-4 above haven't exhausted the diagnostic options yet.

## 7. Everything else from Sessions 1-7a (context, unaffected by this bug)

For full detail see the main handoff doc's session log and this project's Fix List / Roadmap docs (already updated separately, outside this file). Brief pointers:

- **Sessions 1-6**: completed, verified via harness, no open issues. Dead-code removal, `TOOL_REGISTRY` + size-gated raster tools, spline `stops` field prep, `isolationRegionForPoint` generalization (Portrait tile isolation prep — confirmed byte-identical to original for the two real choke-point functions), drawer system audit (no code change needed), project-settings consolidation audit (found and logged the file-export/gallery field-mismatch bug in Fix List item 2).
- **Session 7 (original) → split into 7a/7b/7c/7d**: 7a (`flattenGroupSubtreeToCanvas`) is done and verified. 7b-1 (this file's subject) is blocked on the bug above. 7b-2 (auditing the other ~12 `container.appendChild`/`insertBefore` call sites for group-awareness) has **not been started** — deliberately deferred until 7b-1's actual rendering bug is resolved, since there's no point auditing call sites for a mechanism that doesn't visually work yet. 7c (editing-path audit under active blend mode) and 7d (per-layer blend mode + expanded mode list) are both still fully pending, downstream of 7b-1/7b-2.
- **Roadmap item 14** (Selection/layer/mask transform) was logged during this arc but explicitly deferred — no code impact.
- **IndexedDB corruption-handling research** (roadmap item 7) was completed and written up in the Roadmap doc — no code impact, pure research/documentation.

## 8. Function/DOM inventory relevant to this bug, for quick reference

**New functions this session (all still present, all still needed):**
- `groupBlendWrapperId(groupId)`
- `getOrCreateGroupBlendWrapper(groupId, blendMode)`
- `pruneStaleGroupBlendWrappers(activeGroupIds)`
- `testFlattenFirstGroup()` — TEMP, Session 7a diagnostic, verified working
- `testGroupBlendWiring()` — TEMP, Session 7b-1 diagnostic, **known to be insufficient** (passes even when the real bug is present — see section 5)

**Modified functions this session:**
- `reindexDom()` — generalized, see 2a above. Verified via harness: this was the only call site touched; the other ~12 direct `container.appendChild`/`insertBefore` sites remain untouched (Session 7b-2's scope).
- `applyGroupBlendMode(group)` — now calls `reindexDom()`, see 2b above.

**New DOM elements this session:**
- Per-group `<div class="group-blend-wrap" id="group-blend-wrap-{groupId}">`, created on demand by `getOrCreateGroupBlendWrapper`, pruned by `pruneStaleGroupBlendWrappers`.
- Debug drawer: `#testFlattenGroupBtn`, `#testFlattenGroupPreviewWrap`, `#testFlattenGroupPreviewHost` (Session 7a); `#testGroupBlendWiringBtn` (Session 7b-1).

**CSS added:** none globally — `.group-blend-wrap` styling is applied entirely via inline `style.cssText`/`style.mixBlendMode` in JS, not a stylesheet rule.

**Nothing in Sessions 1-7a was touched or broken by this session's work** — the harness (function-inventory diff) was run after every change and confirmed only the expected additions/modifications occurred each time.
