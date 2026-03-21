---
phase: 01-image-pipeline-and-safety
plan: 04
subsystem: ui
tags: [opencv, pyautogui, pynput, preview, calibration, wayland, x11]

# Dependency graph
requires:
  - phase: 01-image-pipeline-and-safety
    provides: run_image_pipeline, AppState with contours_normalized, check_display_environment stub

provides:
  - run_preview: OpenCV window showing rainbow-gradient contours on black canvas with Esc abort
  - capture_click_position: pynput-based blocking click capture with countdown
  - run_calibration: two-point bounding box calibration that sets state.bbox
  - Wayland-safe module loading: lazy pyautogui/pynput imports so check_display_environment runs first

affects: [02-painting, future phases using state.bbox]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Lazy X11 library imports (pyautogui, pynput) guarded by try/except at module level to allow clean Wayland detection
    - Re-import inside function body when DISPLAY is guaranteed (post check_display_environment)
    - Black canvas preview with rainbow HSV gradient via cv2.COLOR_HSV2BGR
    - pynput.mouse.Listener on_click callback returning False to stop after single click

key-files:
  created: []
  modified:
    - painter.py

key-decisions:
  - "Lazy import pyautogui and pynput at module level via try/except: avoids Xlib.DisplayNameError crash before check_display_environment runs on Wayland-only sessions"
  - "Re-import pyautogui/_pynput inside run_preview/capture_click_position: safe because check_display_environment has already exited if DISPLAY is unset"
  - "pyautogui.PAUSE=0 set on successful module-level import (CFG-06 compliance preserved)"

patterns-established:
  - "Pattern: guard X11-dependent library imports with try/except at module level; re-import lazily inside the functions that use them (after display check)"

requirements-completed: [CAL-01, CAL-02, CAL-04, CAL-05]

# Metrics
duration: 25min
completed: 2026-03-20
---

# Phase 01 Plan 04: Preview, Calibration, and Wayland Fix Summary

**OpenCV rainbow-contour preview window and pynput two-click calibration with lazy X11 library imports to enable clean Wayland detection before display connection**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-20T22:00:00Z
- **Completed:** 2026-03-20T22:25:00Z
- **Tasks:** 3 (2 from prior execution + 1 bug fix after checkpoint)
- **Files modified:** 1

## Accomplishments

- run_preview: draws detected contours on a black canvas (np.zeros) with rainbow HSV gradient via cv2.polylines; Esc exits with code 0 printing "Aborted by user."
- capture_click_position: blocks on pynput.mouse.Listener until first click, with countdown printed to terminal
- run_calibration: two-click bounding box capture with 2-second review pause, sets state.bbox as (x1, y1, x2, y2)
- Fixed Wayland detection: module-level pyautogui and pynput imports wrapped in try/except so check_display_environment() in main() runs before any X display connection

## Task Commits

Each task was committed atomically:

1. **Tasks 1+2: run_preview, capture_click_position, run_calibration** - `6c3e77f` (feat)
2. **Bug fix: lazy pyautogui/pynput imports for Wayland detection** - `c2e5476` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `/var/home/tony/repos/slaypentri/painter.py` - Added run_preview, capture_click_position, run_calibration; wrapped pyautogui and pynput module-level imports in try/except with lazy re-imports inside functions

## Decisions Made

- Lazy import pattern for X11 libraries: module-level try/except allows painter.py to import cleanly with no DISPLAY set; the actual Xlib connection only happens inside functions that are called after check_display_environment() has confirmed a valid X session. This keeps CFG-05 Wayland detection working without moving check_display_environment to module level (which would break test isolation).
- pyautogui.PAUSE = 0 still runs inside the try block on successful import, preserving CFG-06 compliance and the test_pause_zero test.
- pynput gets the same lazy treatment as pyautogui since its module-level __init__ also connects to Xlib.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wayland detection crashed due to module-level pyautogui/pynput X11 connection**

- **Found during:** Checkpoint verification (post-Task 2)
- **Issue:** `import pyautogui` and `from pynput import mouse` both call `Display(os.environ['DISPLAY'])` at import time via Xlib. With `DISPLAY=` (unset/empty), this raised `Xlib.error.DisplayNameError` before `check_display_environment()` ever ran, producing an ugly traceback instead of the intended clean error message.
- **Fix:** Wrapped both imports in `try/except Exception` at module level with `_PYAUTOGUI_AVAILABLE` / `_PYNPUT_AVAILABLE` flags. Added `import pyautogui as _pyautogui` inside `run_preview` and `from pynput import mouse as _pynput_mouse` inside `capture_click_position` — both are safe at call time since `main()` calls `check_display_environment()` first and exits before reaching these functions if DISPLAY is unset.
- **Files modified:** painter.py
- **Verification:** `WAYLAND_DISPLAY=wayland-0 DISPLAY= python3 painter.py test_preview.png` exits code 1 with clean X11/DISPLAY message; all 22 tests still pass.
- **Committed in:** c2e5476 (fix commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug fix)
**Impact on plan:** Essential for the plan's stated goal (CFG-05 Wayland detection). No scope creep.

## Issues Encountered

The bug was discovered during the human checkpoint verification step and was the reason this continuation agent was spawned. No other issues encountered.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full Phase 1 pipeline is complete: load PNG -> edge detection -> contour normalization -> preview -> calibration -> state.bbox set
- state.bbox = (x1, y1, x2, y2) is ready for Phase 2 painting (coordinate mapping, mouse stroke replay)
- No blockers for Phase 2

---
*Phase: 01-image-pipeline-and-safety*
*Completed: 2026-03-20*
