---
phase: 01-image-pipeline-and-safety
plan: 03
subsystem: image-pipeline
tags: [opencv, numpy, canny, contour-extraction, otsu, normalization]

requires:
  - phase: 01-02
    provides: "AppState dataclass with contours_normalized field, run_image_pipeline stub, load_config"

provides:
  - "load_image: loads PNG from disk, exits cleanly on missing/corrupt files"
  - "to_grayscale: converts BGR to 2D grayscale, handles already-gray input"
  - "compute_otsu_thresholds: derives Canny thresholds via Otsu method (low=0.5*otsu, high=otsu)"
  - "normalize_contour: converts pixel contour (N,1,2) to (N,2) float32 in [0.0, 1.0]"
  - "contour_color_bgr: rainbow HSV->BGR color per contour index for preview"
  - "run_image_pipeline: complete 8-step pipeline filling state.contours_normalized"

affects: [01-04-preview, phase-02-mouse-replay]

tech-stack:
  added: []
  patterns:
    - "Otsu auto-threshold: cv2.threshold with THRESH_OTSU, ratio low=0.5*high"
    - "Contour shape handling: reshape(-1, 2) before math, reshape(-1, 1, 2) only for drawing"
    - "Pixel-space simplification: approxPolyDP before normalize_contour (epsilon stays intuitive)"
    - "Auto sentinel interception: check canny_low/high == 'auto' before cv2.Canny"

key-files:
  created: []
  modified:
    - painter.py

key-decisions:
  - "Use RETR_LIST (not RETR_EXTERNAL) to preserve inner contours for line art (letter holes, etc.)"
  - "Run approxPolyDP in pixel space before normalization so epsilon value stays intuitive in px units"
  - "Filter by arcLength after simplification (not before) to measure simplified arc length"
  - "Intercept 'auto' sentinel in run_image_pipeline before cv2.Canny, not at config-load time"

patterns-established:
  - "Contour pipeline order: load -> grayscale -> blur -> Canny -> findContours -> simplify -> filter -> normalize"
  - "normalize_contour: reshape(-1, 2).astype(np.float32) then divide cols by w, h respectively"

requirements-completed: [IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06]

duration: 4min
completed: 2026-03-20
---

# Phase 01 Plan 03: Image Pipeline Summary

**OpenCV 8-step image pipeline (load -> grayscale -> blur -> Canny -> findContours -> approxPolyDP -> arcLength filter -> normalize) with Otsu auto-threshold, producing resolution-independent (N,2) float32 contour arrays in [0,1]**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-20T21:50:43Z
- **Completed:** 2026-03-20T21:54:38Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Five pure helper functions added to painter.py: `load_image`, `to_grayscale`, `compute_otsu_thresholds`, `normalize_contour`, `contour_color_bgr`
- `run_image_pipeline` stub replaced with full 8-step implementation; state.contours_normalized populated correctly
- All 12 test_image_pipeline.py tests pass; full 22-test suite (config + safety + pipeline) green with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement image pipeline helper functions** - `521d486` (feat)
2. **Task 2: Implement run_image_pipeline — replace stub with full pipeline** - `bfe0e03` (feat)

_Note: TDD tasks — both followed RED (existing stub/missing functions) -> GREEN (implementation) flow_

## Files Created/Modified

- `painter.py` - Added 5 helper functions and replaced `run_image_pipeline` stub with full 8-step pipeline

## Decisions Made

- `RETR_LIST` chosen over `RETR_EXTERNAL` to retain inner contours (holes in letters, enclosed regions)
- `approxPolyDP` runs in pixel space before `normalize_contour` so `simplify_epsilon` config value stays intuitive (px units, not fractional normalized coordinates)
- `arcLength` filter applied after simplification so minimum length measured on simplified contour
- `"auto"` sentinel intercepted in `run_image_pipeline` before `cv2.Canny` call (not at config-load time) — keeps config loading generic and validation at point-of-use

## Deviations from Plan

None — plan executed exactly as written. The stale .pyc cache caused tests to show as "skipped" until cache was cleared, but this was an environment issue, not a code deviation.

## Issues Encountered

Stale `.pyc` bytecode cache in `__pycache__/painter.cpython-314.pyc` caused the test skip guard (`pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, ...)`) to evaluate against the old painter module where functions didn't exist yet. Clearing the cache with `find . -name "*.pyc" -delete` resolved it. All tests then passed on first run.

## Known Stubs

None. `run_image_pipeline` is fully implemented. `run_preview` and `run_calibration` remain as NotImplementedError stubs, but those are Plan 04 scope.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Image pipeline complete: `state.contours_normalized` is a list of `(N, 2) float32` arrays with values in `[0.0, 1.0]`
- Plan 04 can consume `state.contours_normalized` directly for preview canvas drawing
- Phase 2 mouse replay can consume the same normalized format for coordinate mapping to bounding box

---
*Phase: 01-image-pipeline-and-safety*
*Completed: 2026-03-20*
