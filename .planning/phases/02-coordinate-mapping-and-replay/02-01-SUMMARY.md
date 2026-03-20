---
phase: 02-coordinate-mapping-and-replay
plan: 01
subsystem: coordinate-mapping
tags: [numpy, aspect-ratio, letterbox, pillarbox, nearest-neighbor, contour-sorting]

# Dependency graph
requires:
  - phase: 01-image-pipeline-and-safety
    provides: AppState.contours_normalized (N,2) float32 arrays, painter.py single-file structure

provides:
  - compute_draw_region: letterbox/pillarbox aspect-ratio-preserving bbox math (CAL-06)
  - map_contour_to_screen: normalized [0,1] to int32 screen pixel transform (CAL-06)
  - sort_contours_nearest_neighbor: greedy O(n^2) nearest-neighbor contour sort (PAINT-04, PAINT-05)
  - tests/test_coordinate_mapping.py: 11-test suite covering all three functions

affects:
  - 02-02 (replay engine — consumes all three functions directly)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Letterbox/pillarbox: if bbox_w/img_aspect <= bbox_h then width-constrained else height-constrained"
    - "Nearest-neighbor sort in normalized space (not pixel space) to avoid rounding accumulation"
    - "Squared distances (no sqrt) in inner comparison loop — O(n^2) but fast enough for n<5000"
    - "Contour reversal via [::-1] when far endpoint is closer to cursor"

key-files:
  created:
    - tests/test_coordinate_mapping.py
  modified:
    - painter.py

key-decisions:
  - "Returns floats from compute_draw_region (caller converts to int at map time to avoid accumulated rounding)"
  - "Sort in normalized space before mapping to screen — preserves float precision in distance math"

patterns-established:
  - "TDD RED: tests skip (not fail) before functions exist, matching Phase 1 Wave-0 pattern"
  - "# === COORDINATE MAPPING === section inserted between CALIBRATION and MAIN in painter.py"

requirements-completed: [CAL-06, PAINT-04, PAINT-05]

# Metrics
duration: 2min
completed: 2026-03-20
---

# Phase 02 Plan 01: Coordinate Mapping and Contour Sorting Summary

**Three pure functions in painter.py — letterbox/pillarbox bbox mapping and nearest-neighbor contour sort — with 11-test suite using numpy array math and no screen interaction**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-20T22:45:39Z
- **Completed:** 2026-03-20T22:47:04Z
- **Tasks:** 1 (TDD: test commit + implementation commit)
- **Files modified:** 2

## Accomplishments

- Added `compute_draw_region(bbox, img_w, img_h)` with correct letterbox and pillarbox math (CAL-06)
- Added `map_contour_to_screen(norm_contour, offset_x, offset_y, draw_w, draw_h)` returning int32 screen pixels (CAL-06)
- Added `sort_contours_nearest_neighbor(contours)` with greedy nearest-neighbor pick + endpoint reversal (PAINT-04, PAINT-05)
- 11 unit tests pass; full suite 33/33 green (Phase 1 tests unaffected)

## Task Commits

Each task was committed atomically with TDD RED/GREEN commits:

1. **Task 1 RED: Test scaffold** - `ba1a525` (test)
2. **Task 1 GREEN: Coordinate mapping functions** - `a847c1e` (feat)

_TDD tasks have separate RED (test) and GREEN (implementation) commits per process._

## Files Created/Modified

- `tests/test_coordinate_mapping.py` - 11 tests: letterbox, pillarbox, square, map origin, map corner, int32 dtype, sort travel, sort reversal, sort no-reverse, sort empty, sort single
- `painter.py` - Added `# === COORDINATE MAPPING ===` section with three functions (115 lines)

## Decisions Made

- Floats returned from `compute_draw_region` rather than ints — caller converts at map time to avoid accumulated rounding error across multiple contour points
- Sort runs in normalized space before screen mapping — keeps float precision in inner distance loop; integer rounding would accumulate error in O(n^2) comparisons
- Wave-0 TDD: tests skip (not fail) before functions exist, matching established Phase 1 convention (`try/except ImportError + pytestmark skipif`)

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All three coordinate mapping functions ready for consumption by Plan 02-02 (replay engine)
- `compute_draw_region` output tuple `(offset_x, offset_y, draw_w, draw_h)` is the exact input expected by `map_contour_to_screen`
- `sort_contours_nearest_neighbor` accepts and returns `list[np.ndarray]` matching `AppState.contours_normalized` type

---
*Phase: 02-coordinate-mapping-and-replay*
*Completed: 2026-03-20*
