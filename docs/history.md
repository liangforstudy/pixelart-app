# Pixel Art App: Docs and History

## Docs

Start with [`docs/Pixel_Art_App___Code_Documentation_and_Handoff.md`](Pixel_Art_App___Code_Documentation_and_Handoff.md). It and the other `Pixel_Art_App___*.md` files (Roadmap, Fix List, Functions, DOM, Class Methods, Renamed Identifiers) describe V1 47. [`Pixel art app core code philosophy.md`](Pixel%20art%20app%20core%20code%20philosophy.md) sets the rules the Code Documentation follows. Older notes and handoffs are in [`docs/archived/`](archived), kept for history.

## History

Every saved version from 1 August to 25 September 2026 is a separate commit on `main`. The app is always the same file (`Pixel_Art_App.html`), so each commit's diff shows what changed in that version. Each commit has a summary of what changed and gives the original file name.

Commits are dated to when each file was saved. Versions that came from a later zip without save dates (V1 42 overwritten, V1 43, V1 44 (1) to V1 46) have estimated dates between their neighbours, and their commits say so.

### Versions 38 to 47

The file names around V1 39 to V1 43 don't match the order the versions were made. The commits follow the real order:

| Step | Main changes | Compare |
|---|---|---|
| V1 38 → V1 40 | Tool registry, iOS sliders, long-press tips | [diff](../../../compare/3f8eca5...3b6fd16) |
| V1 40 → V1 41 | Customisation tab, checkerboard profiles | [diff](../../../compare/3b6fd16...81f2a08) |
| V1 41 → "V1 43" | Resizable debug drawer split | [diff](../../../compare/81f2a08...670ee4f) |
| "V1 43" → "V1 39" | Vector gradient tool | [diff](../../../compare/670ee4f...3653ca8) |
| "V1 39" → "V1 42" | Selection resize/rotate, gradient stops | [diff](../../../compare/3653ca8...7fd0bfe) |
| "V1 42" → V1 42 (overwritten) | Colour value strip (HEX / RGBA / HSV) | [diff](../../../compare/7fd0bfe...f68e4d7) |
| V1 42 → V1 43 | Sprite editor drawer, floating scrubber and D-pad | [diff](../../../compare/f68e4d7...4fc04c1) |
| V1 43 → V1 43 (1) | D-pad opacity slider | [diff](../../../compare/4fc04c1...b67bd77) |
| V1 43 (1) → V1 44 | Faster bulk pixel edits | [diff](../../../compare/b67bd77...b852d8d) |
| V1 44 → V1 44 (1) | Toasts, tappable greyed raster tools | [diff](../../../compare/b852d8d...6971fe6) |
| V1 44 (1) → V1 44 (2) | Checkerboard square size | [diff](../../../compare/6971fe6...35fc34d) |
| V1 44 (2) → V1 44 (3) | Canvas rotation sticks | [diff](../../../compare/35fc34d...1208f08) |
| V1 44 (3) → V1 45 | Pinch release keeps the canvas in place | [diff](../../../compare/1208f08...696ad6f) |
| V1 45 → V1 46 | Native keyboard everywhere | [diff](../../../compare/696ad6f...f0737bc) |
| V1 46 → V1 47 | Projects saved in browser storage | [diff](../../../compare/f0737bc...64b9529) |

### Dead ends

- **`chatgpt-fork` branch**: work done with the free version of ChatGPT on 10 August, branched from `pan_tool_algorithm_commented5`. It was dropped because of regressions and missing features. The branches `chatgpt-fork-history-engine-v5` and `chatgpt-fork-image-mode-optimized` are two side paths of the same fork.
- **`feather-colourtool-fix-2` branch**: `bucket_projectname_colourtool_fix_2` added Feather sliders to the Bucket and Wand tools. The next version was built from the file before it, and later handoffs excluded this feather algorithm on purpose. Feather is now roadmap item 19.

### Removed on purpose

- **Colour Match** (added in `restored_regressions_colour_match`, removed in V13): the handoff notes say not to restore it unless asked, and the eyedropper now does its job.
