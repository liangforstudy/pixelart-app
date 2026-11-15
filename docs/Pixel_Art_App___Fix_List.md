# Pixel Art App --- Fix List

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`).

Confirmed defects only. Add items only when explicitly asked. Resolved items stay struck out, one line each, so a recurrence isn't re-investigated from scratch.

## Open items

None.

## Resolved

1. ~~Creating an empty group recorded no undo.~~ `addEmptyGroup()` now captures tree state and calls `pushTreeOperation('Add group')`. Dead duplicate declaration removed V1_38. **Fixed V1_47.**
2. ~~File export and the gallery serialized different fields; file export dropped `portraitTilePalettes`/`portraitActiveTileKey`, nothing restored `portraitTileIsolation`.~~ One serializer (`currentProjectSaveData`, save v7) and one loader (`openProjectFromSaveData`) now serve file export, file import, and the IndexedDB gallery; all three Portrait fields round-trip. Side effects fixed: re-saving an existing project now refreshes its Portrait palettes; Duplicate copies the project's own palettes and group tree. **Fixed V1_47.**
3. ~~Undo stopped working after a stroke (V1_38, desktop Edge).~~ Resolved on its own, never root-caused.
4. ~~Thumbnails and PNG export ignored blend modes.~~ Tree-aware `flattenTreeToCanvas()` behind every flatten. **Fixed V1_39.**
5. ~~Tapping outside the colour panel left Edit Swatches mode on (locking rotate/pinch).~~ `#swatchEditBackdrop` + `exitSwatchEditMode()`, also called from `closePanel()`. **Fixed V1_38.**
6. ~~iOS colour-picker scrubbing added a swatch per intermediate value.~~ 250ms debounce on `#colorPicker` change. **Fixed V1_38.**
7. ~~Dragging a single vector point pushed no undo entry.~~ Drag start snapshots the spline's points; release pushes one `editSplinePoints` entry if anything moved. **Fixed V1_47.**
8. ~~Switching to a vector layer from Pencil/Soft Brush/erasers didn't auto-switch to Pen.~~ Registry-derived `PIXEL_ONLY_TOOL_IDS`. **Fixed V1_38.**
9. ~~Layer-type smart switch always fell back to fixed tools.~~ `lastPixelTool`/`lastVectorTool`. **Done V1_38.**
10. ~~Mask/clip could be reordered away from its target.~~ Mask/clip moves as a rigid pair with its target; moving the mask itself re-attaches to the next valid layer. **Fixed V1_39.**
