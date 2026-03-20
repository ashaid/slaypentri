---
phase: 02-coordinate-mapping-and-replay
plan: 02
subsystem: replay-engine
tags: [pyautogui, pynput, mouse-replay, abort, progress-bar, countdown, try-finally]

# Dependency graph
requires:
  - phase: 02-01
    provides: compute_draw_region, map_contour_to_screen, sort_contours_nearest_neighbor

provides:
  - run_replay: complete painting session with countdown, sort, map, mouseDown/moveTo/mouseUp loop (PAINT-01..08, CAL-06, CAL-07)
  - _start_abort_listener: pynput keyboard daemon setting abort_flag on Esc (PAINT-06)
  - _print_progress: inline \r progress bar with stroke count and percentage (PAINT-07)
  - updated _DEFAULTS and DEFAULT_CONFIG_CONTENT with start_delay and inter_point_delay

affects:
  - main(): now calls run_replay(state) after run_calibration(state)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "try/finally wrapping entire painting loop — guarantees mouseUp on all exit paths (PAINT-08)"
    - "pynput keyboard.Listener daemon thread returning False on Esc to stop listener (PAINT-06)"
    - "\\r overwrite with end='' flush=True for inline progress bar (PAINT-07)"
    - "Lazy pyautogui import inside run_replay — matches module-level guard pattern from Phase 1"
    - "Skip inter-stroke delay after last stroke: if i < total - 1 (Pitfall 6)"
    - "Degenerate contour skip: filter len(c) >= 2 before screen mapping (not during loop)"

key-files:
  created: []
  modified:
    - painter.py
    - tests/test_coordinate_mapping.py

key-decisions:
  - "Contour length filter (len < 2) applied pre-map in list comprehension — avoids per-stroke check inside try block"
  - "mouseUp button kwarg used for both loop-exit and finally-exit — matches mouseDown call signature exactly"
  - "progress newline printed via leading \\n in final message — keeps _print_progress() stateless"

requirements-completed: [CAL-07, PAINT-01, PAINT-02, PAINT-03, PAINT-06, PAINT-07, PAINT-08]

# Metrics
duration: ~3min (Task 1 only; Task 2 awaiting human verification)
completed: 2026-03-20
---

# Phase 02 Plan 02: Replay Engine and Main Wiring Summary

**Replay engine in painter.py — pyautogui stroke loop with countdown, nearest-neighbor sort, Esc abort via pynput daemon, inline progress bar, and guaranteed mouseUp via try/finally — awaiting end-to-end human verification**

## Performance

- **Duration:** ~3 min (Task 1 complete; Task 2 is human-verify checkpoint)
- **Started:** 2026-03-20T22:49:36Z
- **Completed (Task 1):** 2026-03-20T22:52:13Z
- **Tasks:** 1 of 2 (Task 2 is human-verify gate)
- **Files modified:** 2

## Accomplishments

- Added `_print_progress(done, total, bar_width=30)` with `\r` inline overwrite (PAINT-07)
- Added `_start_abort_listener(state)` with pynput daemon thread, Esc sets abort_flag, returns False to stop listener (PAINT-06)
- Added `run_replay(state)` as complete painting orchestrator: dry_run bypass, cv2.imread for dims, compute_draw_region, sort_contours_nearest_neighbor, screen mapping, countdown, abort listener, configurable button/delays, try/finally guard, progress output, elapsed time summary (PAINT-01..08, CAL-06, CAL-07)
- Updated `_DEFAULTS` and `DEFAULT_CONFIG_CONTENT` with `start_delay: 3` and `inter_point_delay: 0`
- Extended `main()` to call `run_replay(state)` after `run_calibration(state)`
- 7 new tests added (18 total in test_coordinate_mapping.py, 40 total in suite — all green)

## Task Commits

1. **Task 1 RED: Test scaffold** — `bccb014` (test)
2. **Task 1 GREEN: Replay engine implementation** — `a105e72` (feat)

_TDD tasks have separate RED (test) and GREEN (implementation) commits per process._

## Files Created/Modified

- `painter.py` — Added `# === REPLAY ENGINE ===` section (3 functions, ~130 lines); updated `_DEFAULTS`, `DEFAULT_CONFIG_CONTENT`, and `main()`
- `tests/test_coordinate_mapping.py` — Added 7 replay tests: dry_run, mouseup_on_exception, configurable_button, abort_flag_stops, progress_format, start_delay_default, inter_point_delay_default

## Decisions Made

- Contour length filter (`len(c) >= 2`) applied in the screen-mapping list comprehension rather than inside the try block — keeps the loop body clean and avoids per-stroke conditionals
- `mouseUp(button=button)` in finally uses the same `button` variable as the loop — guarantees the released button matches the pressed button even if the config variable is mutated
- Final completion messages use leading `\n` to clear the `\r` progress line — keeps `_print_progress` stateless (no side-effect newline)

## Deviations from Plan

None — plan executed exactly as written.

## Checkpoint Status

**Task 2 (human-verify) is pending.** Awaiting end-to-end visual verification of painting pipeline on a real screen.

## Known Stubs

None — all functions are fully wired. `run_replay` is connected to `main()` and will execute on every non-dry-run invocation.

## Self-Check: PASSED

- `painter.py` exists and contains `def run_replay`, `def _start_abort_listener`, `def _print_progress`, `# === REPLAY ENGINE ===`, `start_delay`, `inter_point_delay`, `run_replay(state)` in main, `finally`
- `tests/test_coordinate_mapping.py` has 18 test functions
- Commits `bccb014` (RED) and `a105e72` (GREEN) both exist
- `pytest tests/ -x -q` → 40 passed
