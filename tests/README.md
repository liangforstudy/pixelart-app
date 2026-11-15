# Tests

Regression tests for `Pixel_Art_App.html`. They open the app in a real browser, drive it with real mouse events and check the results, so a change that breaks an existing feature shows up as a FAIL.

## Run them

From the repo root:

```
pip install playwright
playwright install chromium
python3 tests/run_tests.py
```

If you already have Chrome installed you can skip `playwright install chromium`; the script finds it. To point at a specific browser: `CHROME=/path/to/chrome python3 tests/run_tests.py`.

Each test prints how long it took, each group (static, browser) prints its total, and the last line gives the pass/fail count and the overall time. Anything other than `0 failed` means something broke.

## What's covered

- **Static:** the script parses, no duplicate element ids, no new missing `getElementById` targets, `BUILD_VERSION` is present.
- **Pencil:** draws, undo removes it.
- **File button:** floats top-left, 44 px tall, opens the File panel.
- **Fill:** close gaps holds inside a gappy square without leaking, tap fill + undo, hold-and-drag threshold, swipe fill across three areas (lines not recoloured, one undo).
- **Resize (baseline for the resize-screen rework):** top-left and centre anchors, cropping, undo, the current Resize sheet.

## Limits

Headless Chromium can't reproduce iOS Safari touch behaviour or memory limits. Real-device checks still decide.

## Adding a test

Add an `async def test_something(pg):` function in `run_tests.py` that uses `check('name', condition)`. It runs automatically on a fresh 32×32 canvas and gets its own timing line.

## Rules

- Every test, and every group of tests, prints how long it took.
- Run the tests before every commit; add a test with each new feature.
