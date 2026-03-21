---
phase: 01-image-pipeline-and-safety
plan: 01
subsystem: testing
tags: [pytest, opencv-python, numpy, pyyaml, pyautogui, pynput, conftest, fixtures]

# Dependency graph
requires: []
provides:
  - pytest test scaffold: conftest.py with 7 fixtures (tmp_config_path, existing_config_path, sample_png, blank_png, mock_wayland_env, mock_xwayland_env, mock_x11_env)
  - test stubs for CFG-01 (5 tests), CFG-05 (4 tests), CFG-06 (1 test) in test_config.py and test_safety.py
  - test stubs for IMG-01..IMG-06 (12 tests) in test_image_pipeline.py
  - requirements.txt with all 6 project dependencies pinned by minimum version
affects: [01-02, 01-03, 01-04]

# Tech tracking
tech-stack:
  added: [pytest>=8.0.0, opencv-python>=4.13.0, numpy>=2.1.0, pyyaml>=6.0.3, pyautogui>=0.9.54, pynput>=1.8.1]
  patterns: [try/except ImportError guard with PAINTER_AVAILABLE flag for skip-not-error behavior, pytestmark skipif for module-level skip]

key-files:
  created:
    - requirements.txt
    - tests/conftest.py
    - tests/test_config.py
    - tests/test_safety.py
    - tests/test_image_pipeline.py
  modified: []

key-decisions:
  - "All test files use try/except ImportError + pytestmark skipif so tests skip (not error) before painter.py exists — enables Wave 0 Nyquist compliance"
  - "Added test_normalize_contour_shape to reach 12-test minimum for test_image_pipeline.py acceptance criteria"

patterns-established:
  - "Pattern: try/except ImportError around painter imports + PAINTER_AVAILABLE flag + pytestmark skipif — ensures RED state at scaffold time without collection errors"
  - "Pattern: conftest.py sample_png fixture creates a 64x64 white-square-on-black image — deterministic for contour detection tests"

requirements-completed: [CFG-01, CFG-05, CFG-06, IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06]

# Metrics
duration: 3min
completed: 2026-03-20
---

# Phase 01 Plan 01: Wave 0 Test Scaffold Summary

**pytest test scaffold with 22 stub tests across 4 files covering CFG-01/05/06 and IMG-01..06 — all skip cleanly before painter.py exists**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-20T21:41:48Z
- **Completed:** 2026-03-20T21:44:50Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Created requirements.txt with all 6 dependencies (opencv-python, numpy, pyyaml, pyautogui, pynput, pytest)
- Created tests/conftest.py with 7 pytest fixtures covering image creation, config paths, and environment mocking
- Created 22 test stubs across test_config.py (5), test_safety.py (5), and test_image_pipeline.py (12) — all skip gracefully when painter.py is absent

## Task Commits

Each task was committed atomically:

1. **Task 1: Create requirements.txt and test infrastructure** - `d0136fc` (chore)
2. **Task 2: Create test stubs for config and safety** - `8e70dd4` (test)
3. **Task 3: Create test stubs for image pipeline** - `fcfedd5` (test)

## Files Created/Modified
- `requirements.txt` - 6 pinned minimum-version dependencies for the project
- `tests/conftest.py` - 7 shared pytest fixtures: tmp_config_path, existing_config_path, sample_png, blank_png, mock_wayland_env, mock_xwayland_env, mock_x11_env
- `tests/test_config.py` - 5 stubs for CFG-01: config autogenerate, load existing, deep merge, no mutation, missing keys fallback
- `tests/test_safety.py` - 5 stubs for CFG-05 (wayland exit, exit message, xwayland ok, x11 ok) and CFG-06 (pause zero)
- `tests/test_image_pipeline.py` - 12 stubs for IMG-01..06: load, grayscale, missing file, otsu auto, canny numeric, findContours, blank image, min length filter, normalize, simplify

## Decisions Made
- Used `try/except ImportError` guard with `PAINTER_AVAILABLE` flag and `pytestmark = pytest.mark.skipif(...)` so all tests skip (not error) before painter.py is implemented — enables immediate test collection
- Added `test_normalize_contour_shape` to meet the 12-test minimum acceptance criterion for test_image_pipeline.py (plan's action section specified 11 functions, criterion required 12)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added test_normalize_contour_shape to meet 12-test acceptance criterion**
- **Found during:** Task 3 (test_image_pipeline.py creation)
- **Issue:** Plan's `<action>` block defined 11 test functions but acceptance criteria required >= 12
- **Fix:** Added `test_normalize_contour_shape` testing that normalize_contour output is (N, 2) shaped with correct point count
- **Files modified:** tests/test_image_pipeline.py
- **Verification:** `grep "^def test_" tests/test_image_pipeline.py | wc -l` returns 12
- **Committed in:** fcfedd5 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical to meet acceptance criteria)
**Impact on plan:** Minimal addition — one extra test function strengthens IMG-06 coverage. No scope creep.

## Issues Encountered
None - all tasks executed cleanly.

## Known Stubs
All 22 tests in test_config.py, test_safety.py, and test_image_pipeline.py are intentional stubs — they import from painter (which does not yet exist) and skip when painter.py is absent. These stubs will be filled in by plans 01-02, 01-03, and 01-04 when painter.py is implemented.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Wave 0 scaffold complete — implementation plans (01-02 through 01-04) can now proceed in parallel
- Install dependencies before running tests: `pip install -r requirements.txt`
- Run tests: `pytest tests/ -x -q` — all tests will show as skipped until painter.py exists

## Self-Check: PASSED

- FOUND: requirements.txt
- FOUND: tests/conftest.py
- FOUND: tests/test_config.py
- FOUND: tests/test_safety.py
- FOUND: tests/test_image_pipeline.py
- FOUND: 01-01-SUMMARY.md
- FOUND commit: d0136fc (Task 1)
- FOUND commit: 8e70dd4 (Task 2)
- FOUND commit: fcfedd5 (Task 3)

---
*Phase: 01-image-pipeline-and-safety*
*Completed: 2026-03-20*
