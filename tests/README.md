# Tests

Regression tests for `Pixel_Art_App.html`. They open the app in a real browser, drive it with real mouse events and check the results, so a change that breaks an existing feature shows up as a FAIL.

## Run them

From the repo root:

```
pip install playwright
playwright install chromium
python3 tests/run_tests.py
```

Tests are grouped by the system they cover. Run only the groups for the code you changed:

```
python3 tests/run_tests.py --list          # groups and what code each covers
python3 tests/run_tests.py fill            # one group
python3 tests/run_tests.py fill resize     # several
```

The static checks always run (under a second). If you changed shared code (layer classes, `plot()`, history, camera/layout, boot, the canvas gesture handlers), run everything. To run single tests, give part of their name: `ONLY=snap python3 tests/run_tests.py resize-screen`.

If you already have Chrome installed you can skip `playwright install chromium`; the script finds it. To point at a specific browser: `CHROME=/path/to/chrome python3 tests/run_tests.py`.

Each test prints how long it took, each group (static, browser) prints its total, and the last line gives the pass/fail count and the overall time. Anything other than `0 failed` means something broke.

## Groups

| Group | Covers |
|---|---|
| `core` | boot, New Canvas, pencil, `plot()`, undo/redo |
| `layout` | floating bars, panels and drawers |
| `fill` | bucket fill and its gestures |
| `resize` | resize engine and the number sheet |
| `resize-screen` | the resize screen |
| `settings` | Customise settings and saved preferences |
| `new-canvas` | New Canvas sheet and Create Canvas → resize screen |
| `mapart` | Mapart profile: palette lock, snapping, staircase, import, save/load |
| `gallery` | hub, saving, long-press menu |

## What's covered

- **Static:** the script parses, no duplicate element ids, no new missing `getElementById` targets, `BUILD_VERSION` is present.
- **Pencil:** draws, undo removes it.
- **File button:** floats top-left, 44 px tall, opens the File panel.
- **Fill:** close gaps holds inside a gappy square without leaking, tap fill + undo, hold-and-drag threshold, swipe fill across three areas (lines not recoloured, one undo).
- **Resize (baseline for the resize-screen rework):** top-left and centre anchors, cropping, undo, the current Resize sheet.

## Limits

Headless Chromium can't reproduce iOS Safari touch behaviour or memory limits. Real-device checks still decide.

## Adding a test

Add an `async def test_something(pg):` function in `run_tests.py` that uses `check('name', condition)`, and add its name to a group in `GROUPS` (make a new group for a new system). A test that isn't in a group fails the run. It runs automatically on a fresh 32×32 canvas and gets its own timing line.

## Rules

- Every test, and every group of tests, prints how long it took (times of 120 s or more also in minutes, e.g. `2m 05s (125.3s)`); the end shows time per group and the 3 slowest tests.
- Run the groups for the code you changed; run everything after changing shared code, and before pushing a new version.
- **Feature deleted or changed on request:** the agent deletes or updates that feature's tests (and empty groups) itself, without asking again. It lists in its report which tests it removed or changed and why. A test failing in a feature nobody asked to change is a regression: fix the app, don't edit the test.
- Run the tests before every commit; add a test with each new feature.
