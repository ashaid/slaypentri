---
phase: 02-coordinate-mapping-and-replay
verified: 2026-03-20T23:30:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 02: Coordinate Mapping and Replay Verification Report

**Phase Goal:** Coordinate mapping with aspect-ratio preservation and replay engine that paints contours via pyautogui
**Verified:** 2026-03-20T23:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | compute_draw_region returns correct letterbox dimensions for tall bbox + wide image | VERIFIED | `test_letterbox` passes: draw_w=1000, draw_h=500, offset_y=150 (painter.py:470) |
| 2 | compute_draw_region returns correct pillarbox dimensions for wide bbox + tall image | VERIFIED | `test_pillarbox` passes: draw_w=500, draw_h=1000, offset_x=150 (painter.py:470) |
| 3 | compute_draw_region fills entire bbox when aspect ratios match | VERIFIED | `test_square_bbox_no_margins` passes: draw_w=draw_h=500, offsets=0 |
| 4 | map_contour_to_screen converts normalized [0,1] points to integer screen pixels | VERIFIED | `test_map_normalized_origin`, `test_map_normalized_corner`, `test_map_returns_int32` all pass; dtype confirmed np.int32 |
| 5 | sort_contours_nearest_neighbor orders contours by spatial proximity from (0,0) | VERIFIED | `test_sort_reduces_travel` confirms sorted travel < unsorted travel; `test_sort_empty_list`, `test_sort_single_contour` pass |
| 6 | sort_contours_nearest_neighbor reverses a contour when far endpoint is closer | VERIFIED | `test_sort_reverses_contour` and `test_sort_no_reverse_when_start_closer` both pass |
| 7 | Countdown prints to terminal before painting starts | VERIFIED | run_replay:655-661 reads `start_delay`, loops with time.sleep(1), prints countdown; test_start_delay_default confirms _DEFAULTS["painting"]["start_delay"]==3 |
| 8 | Each contour is painted as mouseDown -> moveTo sequence -> mouseUp | VERIFIED | run_replay:681-688 implements full stroke loop; test_dry_run_skips_painting and test_configurable_mouse_button confirm calls |
| 9 | Mouse button and inter-point delay are configurable | VERIFIED | run_replay:667-669 reads `mouse_button` and `inter_point_delay` from config; test_configurable_mouse_button passes; test_inter_point_delay_default confirms _DEFAULTS["painting"]["inter_point_delay"]==0 |
| 10 | mouseUp is called on all exit paths including exceptions and abort | VERIFIED | run_replay:674-700 wraps entire loop in try/finally with unconditional pyautogui.mouseUp; test_mouseup_on_exception confirms; test_abort_flag_stops_replay confirms abort stops after first contour |

**Score: 10/10 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `tests/test_coordinate_mapping.py` | Unit tests for coordinate mapping and contour sorting | VERIFIED | 287 lines, 18 test functions (>= plan minimum of 11 for plan-01, >= 18 for plan-02); try/except ImportError guard matches Phase 1 convention |
| `painter.py` | compute_draw_region, map_contour_to_screen, sort_contours_nearest_neighbor functions | VERIFIED | 727 lines; all three functions present under `# === COORDINATE MAPPING ===` section (line 468) |
| `painter.py` | run_replay, _start_abort_listener, _print_progress; updated _DEFAULTS and DEFAULT_CONFIG_CONTENT; updated main() | VERIFIED | All three replay functions under `# === REPLAY ENGINE ===` (line 586); _DEFAULTS includes start_delay:3 and inter_point_delay:0; main() calls run_replay at line 723 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `painter.py:compute_draw_region` | `painter.py:map_contour_to_screen` | offset_x, offset_y, draw_w, draw_h tuple | WIRED | Line 642 unpacks tuple; line 649 passes all four args to map_contour_to_screen in list comprehension |
| `painter.py:sort_contours_nearest_neighbor` | `AppState.contours_normalized` | accepts list of (N,2) float32 arrays | WIRED | run_replay:645 calls `sort_contours_nearest_neighbor(state.contours_normalized)` |
| `painter.py:main` | `painter.py:run_replay` | main() calls run_replay(state) after run_calibration(state) | WIRED | Line 723: `run_replay(state)` immediately follows `run_calibration(state)` at line 722 |
| `painter.py:run_replay` | `painter.py:compute_draw_region` | run_replay calls compute_draw_region to get draw area | WIRED | Line 642: `offset_x, offset_y, draw_w, draw_h = compute_draw_region(state.bbox, img_w, img_h)` |
| `painter.py:run_replay` | `painter.py:sort_contours_nearest_neighbor` | run_replay sorts contours before mapping to screen | WIRED | Line 645: `sorted_contours = sort_contours_nearest_neighbor(state.contours_normalized)` |
| `painter.py:run_replay` | `pyautogui.mouseUp` | try/finally guarantees mouseUp on all exit paths | WIRED | Lines 698-700: `finally: pyautogui.mouseUp(button=button)` — unconditional; confirmed by test_mouseup_on_exception |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| CAL-06 | 02-01, 02-02 | Tool maps contour coordinates to screen space preserving aspect ratio (no stretching) | SATISFIED | compute_draw_region implements letterbox/pillarbox math; map_contour_to_screen converts to int32 screen pixels; 3 geometry tests pass; run_replay uses both |
| CAL-07 | 02-02 | Configurable countdown delay before first stroke begins | SATISFIED | _DEFAULTS["painting"]["start_delay"]=3; run_replay:655-661 implements countdown; test_start_delay_default passes |
| PAINT-01 | 02-02 | Tool replays each contour as right-click mouseDown -> moveTo sequence -> mouseUp | SATISFIED | run_replay:681-688 implements full stroke loop; test_dry_run_skips_painting confirms actual calls in non-dry-run path |
| PAINT-02 | 02-02 | Mouse button for strokes is configurable (default: right) | SATISFIED | _DEFAULTS["painting"]["mouse_button"]="right"; run_replay:667 reads config; test_configurable_mouse_button passes with "left" |
| PAINT-03 | 02-02 | Inter-point delay is configurable for stroke speed tuning | SATISFIED | _DEFAULTS["painting"]["inter_point_delay"]=0; run_replay:669,685-686 reads and applies per-point sleep; test_inter_point_delay_default passes |
| PAINT-04 | 02-01 | Contours are sorted by spatial proximity (nearest-neighbor) to minimize travel | SATISFIED | sort_contours_nearest_neighbor implements greedy O(n^2) nearest-neighbor; test_sort_reduces_travel confirms travel reduction |
| PAINT-05 | 02-01 | Tool picks optimal start-point (closest endpoint) for each contour | SATISFIED | sort_contours_nearest_neighbor checks both endpoints, reverses if far end is closer; test_sort_reverses_contour and test_sort_no_reverse_when_start_closer pass |
| PAINT-06 | 02-02 | Esc hotkey aborts painting mid-stroke via background listener thread | SATISFIED | _start_abort_listener uses pynput daemon thread; on_press sets abort_flag.set() on Key.esc, returns False; run_replay:677 checks abort_flag per stroke; test_abort_flag_stops_replay passes |
| PAINT-07 | 02-02 | Tool prints stroke progress (N/M, percentage) to terminal during painting | SATISFIED | _print_progress uses \r overwrite with "N/M strokes (XX%) [bar]" format; called per stroke at run_replay:692; test_progress_output_format passes |
| PAINT-08 | 02-02 | Tool calls mouseUp on all exit paths (normal, abort, exception) | SATISFIED | try/finally in run_replay:674-700 guarantees pyautogui.mouseUp(button=button) on every exit path; test_mouseup_on_exception confirms exception path; finally executes on normal completion and abort too |

All 10 requirement IDs from both PLAN frontmatters are satisfied. No orphaned requirements — REQUIREMENTS.md maps all 10 IDs to Phase 2 and all 10 are claimed by plans.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_coordinate_mapping.py` | 21 | `pytestmark = pytest.mark.skipif(not PAINTER_AVAILABLE, ...)` | Info | Expected convention from Phase 1 — tests skip gracefully if painter.py is absent, not a stub indicator. PAINTER_AVAILABLE is True in current state, all 18 tests run. |

No blockers. No stubs. No placeholder implementations found. The `pytestmark` skipif is an intentional design pattern established in Phase 1 to support TDD Red/Green commits, not a code quality concern.

---

### Human Verification Required

One item from Plan 02-02 was designated as a blocking human checkpoint. Per SUMMARY 02-02, this was completed and approved:

**End-to-end painting verification — COMPLETED**

Per 02-02-SUMMARY.md: Task 2 (human verification) was executed. User approved the end-to-end painting pipeline. A bbox normalization bug (negative draw dimensions when user clicks bottom-right before top-left) was found during human verification and fixed in commit `5d2a0e6`. The fix adds min/max normalization at compute_draw_region:487-488. All five commits (`ba1a525`, `a847c1e`, `bccb014`, `a105e72`, `5d2a0e6`) confirmed present in git history.

No additional human verification is required — the human checkpoint gate was already passed.

---

### Test Suite Results

```
tests/test_coordinate_mapping.py: 18 passed in 0.17s
tests/ (full suite):              40 passed in 0.20s
```

Phase 1 tests unaffected (40 - 18 = 22 Phase 1 tests all green).

---

### Summary

Phase 02 goal is fully achieved. All three coordinate mapping functions are implemented, substantive, and wired. The replay engine drives the complete painting pipeline — sort, map, countdown, stroke loop, abort, progress, cleanup — with all configuration keys hooked up and all exit paths guarded by try/finally. The bbox normalization bug found during human verification was fixed and committed. All 10 requirement IDs are satisfied with test evidence. No stubs, no placeholders, no orphaned requirements.

---

_Verified: 2026-03-20T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
