# Pixel Art App --- Renamed Identifiers & Migration

**Documented against:** `Pixel_Art_App_V1_47.html` (BUILD_VERSION `V1_47`).

Scope: persisted storage (localStorage keys, IndexedDB schema), naming-convention exceptions, and migration rules. Not for function or DOM-id renames.

Default key convention: subject-then-property, prefixed `pixelApp` (e.g. `pixelAppPanelVisibility`).

## Persisted storage (all of it)

| Key / store | Kind | Holds | Convention |
|---|---|---|---|
| `pixelAppPanelVisibility` | localStorage | Panel-tab visibility + `debugOptions` (log toggles, unrestricted vector, history budget MiB, raster-gate threshold, force-enable raster tools) | default |
| `pixelAppSettingsCheckBoard` | localStorage | Checker profile per screen + custom colour pairs | **exception** (property-then-subject; `CheckBoard` spelling intentional) |
| `pixelAppDebugDrawerSplitPct` | localStorage | Debug drawer controls/log split, 15-85 | default |
| `pixelAppGradientNewStopColorSource` | localStorage | `'selected'` or `'interpolate'` | default |
| `pixelAppSpriteAnimHideMissingNameToast` | localStorage | `'1'` = don't show the missing-name toast | default |
| `pixelArtMapartPrefs` | localStorage | `{method, snapToasts}`: mapart colour method id (`MAPART_COLOUR_METHODS`) and the debug snap-toast toggle (V2_5) | default for the `pixelArt*` prefs family |
| `pixelArtEyedropSample` | localStorage | Eyedropper sample size: 1, 3, 5, 11, 31, 51 or 101 (V2_5) | default for the `pixelArt*` prefs family |
| `pixelAppBootGuard` | localStorage | `{bootsUnfinished, safeMode, openingProjectId, openingProjectName}` crash guard | default |
| `pixelAppProjects` | IndexedDB v1 | stores `meta` (keyPath `id`: name, gridW, gridH, profile, thumbnailDataURL, updatedAt) and `data` (keyPath `id`: `{id, data}`, save data v7) | - |

## Exceptions

- **`pixelAppSettingsCheckBoard`** -- deliberate one-off, decided before V1_39. Not a signal the convention changed. No migration (never shipped under another name).

## Migration rules

- **Renaming a localStorage key:** on load read the old key; if present write the new key (new shape if the shape changed), then remove the old key. Never assume empty just because the new key is missing. Keep the migration until most users have loaded once post-rename.
- **IndexedDB schema change:** bump `PROJECT_DB_VERSION` and do the change in `onupgradeneeded`. Never clear-then-write: write to a new store/location and swap, so a failed upgrade leaves the old data intact. Existing projects' `data` records use the save format; a save-format change goes through `buildFramesFromSaveData` version checks, not a DB migration.
- **Save format:** `version` 7 (V1_47). Loader accepts `version >= 2` (frames) and legacy v1 (`layers` at top level). Portrait fields are optional (defaults: `{}`, `'0,0'`, off).
- **Project ids:** time-based numbers since V1_47. No older persisted ids exist (the gallery was memory-only before V1_47).
