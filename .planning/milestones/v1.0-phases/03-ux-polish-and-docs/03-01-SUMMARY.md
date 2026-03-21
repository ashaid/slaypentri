---
phase: 03-ux-polish-and-docs
plan: 01
subsystem: ux
tags: [python, opencv, estimate, config, yaml]

# Dependency graph
requires:
  - phase: 02-coordinate-mapping-and-replay
    provides: run_preview, state.contours_normalized, painting config keys (inter_point_delay, inter_stroke_delay, start_delay)
provides:
  - estimate_painting_time(contours, config) function in painter.py
  - Terminal output of contour count, point count, and estimated painting time before preview window
  - Enhanced DEFAULT_CONFIG_CONTENT with value ranges for all 9 parameters
  - Unit tests for time estimation logic (5 test cases)
affects: [03-ux-polish-and-docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Time estimate reads from actual config values (not hardcoded) so estimate is meaningful"
    - "Estimate placed in run_preview terminal output before cv2.imshow call"
    - "TDD: test file imports with try/except + pytestmark skipif to skip cleanly before implementation"

key-files:
  created:
    - tests/test_preview_estimate.py
  modified:
    - painter.py

key-decisions:
  - "estimate_painting_time placed in PREVIEW section of painter.py, before run_preview, to keep related logic co-located"
  - "Time formatted as ~Xs under 60s, ~Xm Ys for 60s+ — compact and readable in terminal"
  - "DEFAULT_CONFIG_CONTENT comments updated with ranges; _DEFAULTS dict values left unchanged"

patterns-established:
  - "Estimate formula: start_delay + (total_points * inter_point_delay) + (num_strokes * inter_stroke_delay)"
  - "Config range annotations style: (0-255, or 'auto' for Otsu-based). Direction hint after range."

requirements-completed: [CAL-03, CFG-02]

# Metrics
duration: 2min
completed: 2026-03-20
---

# Phase 3 Plan 1: Preview Time Estimate and Config Annotations Summary

**Painting time estimate printed to terminal before preview window using actual config values, plus value-range annotations for all 9 config parameters in DEFAULT_CONFIG_CONTENT**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-20T23:55:01Z
- **Completed:** 2026-03-20T23:56:59Z
- **Tasks:** 2 (Task 1 TDD: RED + GREEN; Task 2)
- **Files modified:** 2 (painter.py, tests/test_preview_estimate.py)

## Accomplishments

- Added `estimate_painting_time(contours, config)` function implementing formula: `start_delay + (total_points * inter_point_delay) + (num_strokes * inter_stroke_delay)`
- Wired estimate into `run_preview` — terminal now prints `Preview ready. N contours, P points. Estimated painting time: ~Xs` before showing the OpenCV window
- Enhanced all 9 parameters in `DEFAULT_CONFIG_CONTENT` with inline value ranges and direction hints (e.g., `(odd integer, 1-31)`, `(0-255, or "auto" for Otsu-based)`, `(0.0-1.0)`)
- Added 5 unit tests covering: basic formula, default config 100-stroke case, inter_point_delay variant, empty contours, zero start_delay
- 45 total tests pass, no regressions

## Task Commits

1. **Test (RED): estimate_painting_time failing tests** - `84bf0e8` (test)
2. **Task 1: estimate_painting_time + run_preview wiring** - `812764e` (feat)
3. **Task 2: DEFAULT_CONFIG_CONTENT range annotations** - `91b0be5` (feat)

## Files Created/Modified

- `painter.py` - Added `estimate_painting_time()` function, wired into `run_preview`, enhanced `DEFAULT_CONFIG_CONTENT`
- `tests/test_preview_estimate.py` - 5 unit tests for time estimation logic (new file)

## Decisions Made

- Time formatted as `~Xs` for under 60 seconds, `~Xm Ys` for 60 seconds or more — compact for terminal output
- `estimate_painting_time` placed in the PREVIEW section of `painter.py` (just above `run_preview`) to keep related logic co-located
- `_DEFAULTS` dict values left unchanged — only `DEFAULT_CONFIG_CONTENT` comments were updated

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CAL-03 and CFG-02 requirements completed
- Plan 03-02 (README and example images) can proceed — `estimate_painting_time` is available for documenting in config reference table

## Self-Check: PASSED

- FOUND: tests/test_preview_estimate.py
- FOUND: painter.py
- FOUND: 03-01-SUMMARY.md
- FOUND commit: 84bf0e8 (test RED)
- FOUND commit: 812764e (feat task 1)
- FOUND commit: 91b0be5 (feat task 2)

---
*Phase: 03-ux-polish-and-docs*
*Completed: 2026-03-20*
