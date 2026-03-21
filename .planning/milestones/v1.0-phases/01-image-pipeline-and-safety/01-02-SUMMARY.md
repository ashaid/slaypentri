---
phase: 01-image-pipeline-and-safety
plan: 02
subsystem: painter-core
tags: [painter.py, AppState, dataclass, deep_merge, load_config, check_display_environment, parse_cli, pyautogui, yaml, wayland]

# Dependency graph
requires: [01-01]
provides:
  - painter.py with AppState dataclass, deep_merge, DEFAULT_CONFIG_CONTENT, load_config, check_display_environment, parse_cli, main skeleton, three NotImplementedError stubs
affects: [01-03, 01-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - AppState dataclass as single source of truth (no module-level globals)
    - deep_merge for recursive YAML config merge without mutating inputs
    - pyautogui.PAUSE = 0 at module level (CFG-06)
    - tkinter-absent guard: patches mouseinfo stub before pyautogui import for headless/test environments
    - yaml.safe_load (never yaml.load) for YAML parsing
    - check_display_environment(): fail fast on WAYLAND_DISPLAY without DISPLAY

key-files:
  created:
    - painter.py
  modified: []

key-decisions:
  - Added tkinter-absent guard (mouseinfo stub patch) so painter.py can be imported in headless environments where tkinter is unavailable — pyautogui's mouseinfo calls sys.exit() if tkinter is absent, breaking test imports
  - Combined Task 1 and Task 2 implementation into single painter.py commit since file structure required all components at once to be importable

metrics:
  duration: "8 minutes"
  completed: "2026-03-20"
  tasks_completed: 2
  files_created: 1
  files_modified: 0
---

# Phase 01 Plan 02: painter.py Foundation Summary

**One-liner:** painter.py skeleton with AppState dataclass, YAML config auto-gen with deep_merge, Wayland detection, CLI argparse, and pyautogui.PAUSE=0 at module level.

## Objective

Build the painter.py skeleton that all subsequent plans import from. Make test_config.py and test_safety.py go GREEN.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | AppState dataclass, deep_merge, DEFAULT_CONFIG_CONTENT, load_config | 38b556e | painter.py |
| 2 | check_display_environment, parse_cli, main skeleton | 38b556e | painter.py (same commit) |

## What Was Built

### painter.py (227 lines)

**Sections:**
- Module header with imports (os, sys, time, threading, argparse, dataclasses, numpy, cv2, yaml, pyautogui, pynput)
- `pyautogui.PAUSE = 0` at module level (CFG-06)
- `=== CONFIGURATION ===`: DEFAULT_CONFIG_CONTENT string, _DEFAULTS dict, deep_merge(), AppState dataclass, load_config()
- `=== SAFETY ===`: check_display_environment()
- `=== CLI ===`: parse_cli()
- `=== IMAGE PIPELINE ===` stub: run_image_pipeline() raises NotImplementedError
- `=== PREVIEW / CALIBRATION ===` stubs: run_preview(), run_calibration() raise NotImplementedError
- `=== MAIN ===`: main() calling all three in order

### Key Components

**AppState dataclass:** config (dict), image_path (str), config_path (str), contours_normalized (List[np.ndarray]), bbox (Optional[tuple]), abort_flag (threading.Event), dry_run (bool), verbose (bool)

**deep_merge:** recursively merges overrides into defaults without mutating either input dict.

**load_config:** auto-generates config.yaml with annotated comments on first run; enforces odd blur_kernel_size; merges loaded YAML with _DEFAULTS via deep_merge.

**check_display_environment:** exits 1 with actionable error message containing "X11" and "DISPLAY" when WAYLAND_DISPLAY is set but DISPLAY is absent. Passes through for XWayland (both set) and X11 (only DISPLAY).

**parse_cli:** argparse with positional "image" arg plus --config, --dry-run, --verbose flags. Default config_path is config.yaml next to painter.py.

## Verification Results

```
pytest tests/test_config.py tests/test_safety.py -v
10 passed in 0.15s
```

All 10 tests pass green:
- test_config_autogenerate: PASSED
- test_config_loads_existing: PASSED
- test_deep_merge: PASSED
- test_deep_merge_no_mutation: PASSED
- test_missing_keys_fall_back_to_defaults: PASSED
- test_wayland_exit: PASSED
- test_wayland_exit_message: PASSED
- test_xwayland_ok: PASSED
- test_x11_ok: PASSED
- test_pause_zero: PASSED

CLI check:
```
python painter.py --help
# Prints: image, --config, --dry-run, --verbose listed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added tkinter-absent guard for pyautogui import**
- **Found during:** Task 1 verification
- **Issue:** pyautogui depends on mouseinfo, which calls `sys.exit()` at import time if tkinter is not installed. This caused an INTERNALERROR in pytest (SystemExit bypassed the try/except ImportError guard in test files).
- **Fix:** Added a tkinter availability check before importing pyautogui. When tkinter is absent, a stub `types.ModuleType("mouseinfo")` is inserted into sys.modules before pyautogui imports it. This prevents the sys.exit() call while still allowing painter.py to be imported in headless/test environments.
- **Files modified:** painter.py (lines 18-27)
- **Commit:** 38b556e

**2. [Rule 3 - Blocking] Created Wave 0 test scaffold files**
- **Found during:** Pre-execution check
- **Issue:** Plan 01-01 (Wave 0) test files were not committed (tests/test_config.py, tests/test_safety.py, requirements.txt, conftest.py existed on disk but not in git). This plan depends on them for verification.
- **Fix:** Files were already present on disk from a prior partial run. Proceeded with verification using the existing files.
- **Files modified:** None (files existed)

## Known Stubs

The following functions are intentional stubs with NotImplementedError — they will be implemented in Plans 03 and 04:
- `run_image_pipeline()` — implemented in Plan 03
- `run_preview()` — implemented in Plan 04
- `run_calibration()` — implemented in Plan 04

These stubs do NOT prevent this plan's goal from being achieved (the foundation components are fully implemented and tested).

## Self-Check: PASSED

- painter.py exists: FOUND at /var/home/tony/repos/slaypentri/painter.py
- Commit 38b556e: FOUND in git log
- 10 tests pass green: VERIFIED
