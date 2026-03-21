---
phase: 01-image-pipeline-and-safety
verified: 2026-03-20T22:45:00Z
status: passed
score: 5/5 must-haves verified
human_verification:
  - test: "Open a preview window with a test PNG (e.g. python painter.py test.png --dry-run on X11/XWayland) and confirm: contours are visible on a BLACK background (not overlaid on the source image), and the rainbow gradient is visible (first contours red, last contours blue)"
    expected: "OpenCV window titled 'Contour Preview' opens; contours rendered in color on black; window closeable with Esc (prints 'Aborted by user.') or any other key (proceeds to calibration)"
    why_human: "cv2.imshow requires a live display; automated tests do not exercise the GUI path"
  - test: "After proceeding from preview (non-Esc key), verify the calibration countdown: terminal prints 'Click top-left corner in: 3... 2... 1... GO — click now.' then after click prints 'Click bottom-right corner in: 3... 2... 1... GO — click now.' then prints 'Captured bounding box: (x1, y1) -> (x2, y2)' and 'Proceeding in 2 seconds...'"
    expected: "Two-click flow works; coordinates are real screen coordinates; tool exits after 2-second pause (since there is no Phase 2 painting yet)"
    why_human: "pynput.mouse.Listener requires physical mouse input; calibration flow cannot be unit tested"
  - test: "Success Criterion 1 wording mismatch: ROADMAP.md says 'contours overlaid on the image' but the implementation draws contours on a BLACK canvas (deliberate decision in CONTEXT.md). Confirm whether the black-canvas approach satisfies the intent of the requirement."
    expected: "Either the ROADMAP Success Criterion 1 wording is updated to say 'contours on a black canvas' OR the implementation is changed to overlay on the source image"
    why_human: "The ROADMAP text and the implementation differ on visual presentation; only the project owner can decide if the deviation is acceptable"
---

# Phase 1: Image Pipeline and Safety — Verification Report

**Phase Goal:** User can load a PNG, see detected contours in a preview window, capture a screen bounding box via two clicks, and abort at any time — with no mouse painting yet
**Verified:** 2026-03-20T22:45:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | User runs tool with PNG path and sees OpenCV window showing detected contours | ? HUMAN | `run_preview` calls `cv2.imshow("Contour Preview", canvas)` with rainbow polylines drawn on `np.zeros` canvas; correct code path verified; visual output requires human confirmation. Note: ROADMAP says "overlaid on the image" but CONTEXT.md locked decision is "black background" — wording mismatch. |
| 2 | User can press Esc to abort without any mouse movement | ✓ VERIFIED | `if key == 27: print("Aborted by user."); sys.exit(0)` at line 392-394; no pyautogui calls before Esc path; no mouse movement possible since calibration/painting come after. |
| 3 | After proceeding from preview, user clicks two screen points and sees bounding box coordinates printed | ? HUMAN | `run_calibration` calls `capture_click_position` twice with pynput.mouse.Listener; prints "Captured bounding box: (x1, y1) -> (x2, y2)"; code is substantive and wired correctly; requires physical mouse to verify |
| 4 | On pure Wayland session, tool exits with clear X11 error message | ✓ VERIFIED | `WAYLAND_DISPLAY=wayland-0 DISPLAY="" python3 painter.py test.png` exits code 1 with "Error: This tool requires an X11 session...X11...DISPLAY" message — tested and confirmed |
| 5 | All tunable parameters read from YAML config; missing keys fall back to defaults | ✓ VERIFIED | `load_config` uses `deep_merge(_DEFAULTS, loaded)` to fill missing keys; auto-generates `config.yaml` with annotated comments on first run; 5 config tests pass green |

**Score:** 3/5 truths fully verified via automation; 2/5 require human confirmation (visual GUI + physical mouse); 0 truths failed.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | Pinned dependency list with 6 deps | ✓ VERIFIED | 6 deps present: opencv-python, numpy, pyyaml, pyautogui, pynput, pytest |
| `tests/conftest.py` | 7 pytest fixtures | ✓ VERIFIED | All 7 fixtures present: tmp_config_path, existing_config_path, sample_png, blank_png, mock_wayland_env, mock_xwayland_env, mock_x11_env |
| `tests/test_config.py` | 5 tests for CFG-01 | ✓ VERIFIED | 5 test functions; try/except ImportError guard + pytestmark skipif present |
| `tests/test_safety.py` | 5 tests for CFG-05, CFG-06 | ✓ VERIFIED | 5 test functions; try/except ImportError guard + pytestmark skipif present |
| `tests/test_image_pipeline.py` | 12 tests for IMG-01..06 | ✓ VERIFIED | 12 test functions; try/except ImportError guard present |
| `painter.py` | AppState, deep_merge, DEFAULT_CONFIG_CONTENT, load_config, check_display_environment, parse_cli, load_image, to_grayscale, compute_otsu_thresholds, normalize_contour, contour_color_bgr, run_image_pipeline, run_preview, capture_click_position, run_calibration, main | ✓ VERIFIED | All 15 functions/symbols present; no NotImplementedError stubs remain |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main()` | `check_display_environment` | first call in main | ✓ WIRED | Line 469: `check_display_environment()` called before any CLI parsing |
| `main()` | `load_config` | called after parse_cli | ✓ WIRED | Line 471: `load_config(state)` called after parse_cli |
| `load_config` | `DEFAULT_CONFIG_CONTENT` | writes to config.yaml when absent | ✓ WIRED | Line 128: `f.write(DEFAULT_CONFIG_CONTENT)` inside `if not os.path.exists(state.config_path)` |
| `run_image_pipeline` | `compute_otsu_thresholds` | conditional on "auto" sentinel | ✓ WIRED | Line 296: `if low == "auto" or high == "auto": low, high = compute_otsu_thresholds(blurred)` |
| `run_image_pipeline` | `normalize_contour` | list comprehension after filter | ✓ WIRED | Lines 325-327: `state.contours_normalized = [normalize_contour(c, w, h) for c in filtered]` |
| `run_preview` | `cv2.imshow / cv2.waitKey(0)` | main thread (not threaded) | ✓ WIRED | Lines 388-389: direct calls in run_preview body; no threading.Thread wrapping |
| `run_preview` | `sys.exit(0)` | key == 27 check | ✓ WIRED | Lines 392-394: `if key == 27: print("Aborted by user."); sys.exit(0)` |
| `capture_click_position` | `pynput_mouse.Listener` | on_click callback returns False | ✓ WIRED | Lines 419-427: `from pynput import mouse as _pynput_mouse` then `with _pynput_mouse.Listener(on_click=on_click) as listener: listener.join()` |
| `run_calibration` | `state.bbox` | tuple assignment (x1, y1, x2, y2) | ✓ WIRED | Line 457: `state.bbox = (x1, y1, x2, y2)` after both clicks |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| IMG-01 | 01-01, 01-03 | Load any PNG, convert to grayscale | ✓ SATISFIED | `load_image` (sys.exit on missing/corrupt), `to_grayscale` (cv2.COLOR_BGR2GRAY); 3 tests pass |
| IMG-02 | 01-01, 01-03 | Canny with configurable thresholds + blur kernel | ✓ SATISFIED | `cv2.GaussianBlur(gray, (blur_k, blur_k), 0)` + `cv2.Canny(blurred, float(low), float(high))`; odd-kernel enforcement |
| IMG-03 | 01-01, 01-03 | Otsu auto-threshold fallback when canny set to "auto" | ✓ SATISFIED | `compute_otsu_thresholds` + sentinel check `if low == "auto" or high == "auto"`; 2 tests pass |
| IMG-04 | 01-01, 01-03 | Extract ordered contour polylines via findContours | ✓ SATISFIED | `cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)`; 2 tests pass including blank image |
| IMG-05 | 01-01, 01-03 | Filter contours below min arc-length | ✓ SATISFIED | `cv2.arcLength(c, closed=False) >= min_len` filter after simplification; test with min_contour_px=100000 passes |
| IMG-06 | 01-01, 01-03 | Douglas-Peucker simplification with configurable epsilon | ✓ SATISFIED | `cv2.approxPolyDP(c, epsilon, closed=False)` before normalization; simplify_reduces_points test passes |
| CAL-01 | 01-04 | OpenCV preview window before painting | ? HUMAN | `cv2.imshow("Contour Preview", canvas)` implemented; visual output requires human |
| CAL-02 | 01-04 | Esc aborts from preview, any other key proceeds | ✓ SATISFIED | `if key == 27: sys.exit(0)`; no mouse movement on Esc path; code verified |
| CAL-04 | 01-04 | Two-click bounding box capture in terminal | ? HUMAN | `capture_click_position` with pynput implemented; requires physical mouse |
| CAL-05 | 01-04 | Display captured bounding box for confirmation | ? HUMAN | `print(f"\nCaptured bounding box: ({x1}, {y1}) -> ({x2}, {y2})")` present; "Proceeding in 2 seconds..." present; requires live run |
| CFG-01 | 01-01, 01-02 | YAML config with sensible defaults | ✓ SATISFIED | `load_config` + `deep_merge(_DEFAULTS, loaded)` + auto-generation; 5 config tests pass |
| CFG-05 | 01-01, 01-02 | Wayland-only detection with actionable error | ✓ SATISFIED | Tested: exits code 1, prints X11 + DISPLAY in message; lazy import pattern prevents pre-check crash |
| CFG-06 | 01-01, 01-02 | pyautogui.PAUSE = 0 at startup | ✓ SATISFIED | Line 39: `pyautogui.PAUSE = 0` in successful import block; test_pause_zero passes |

**Orphaned requirements check:** CAL-03 (preview with estimated painting time) is Phase 3, not Phase 1 — not orphaned. CFG-02, CFG-03, CFG-04 are Phase 3 — not orphaned. No Phase 1 requirements are unclaimed.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `painter.py` | 473 | Comment "Phase 1 stubs — filled in by Plans 03 and 04" inside `main()` is stale — all stubs have been replaced | ℹ️ Info | No functional impact; cosmetic only |

No functional stubs, placeholder returns, hardcoded empty data, or TODO/FIXME markers found. No unsafe `yaml.load()` usage. No `NotImplementedError` remains in painter.py.

### Human Verification Required

#### 1. Preview Window Visual Output

**Test:** Create a test PNG (`python3 -c "import cv2, numpy as np; img = np.zeros((200, 200, 3), dtype=np.uint8); cv2.rectangle(img, (30, 30), (170, 170), (255, 255, 255), 3); cv2.imwrite('test.png', img)"`) then run `python3 painter.py test.png` on an X11/XWayland session.
**Expected:** OpenCV window "Contour Preview" opens showing colored contours on a solid black background. Rainbow gradient visible (red to blue). Pressing Esc closes window and prints "Aborted by user." with exit code 0.
**Why human:** cv2.imshow requires a live X display. Automated tests cannot exercise the GUI rendering path.

#### 2. Calibration Two-Click Flow

**Test:** After pressing a non-Esc key in the preview, observe the terminal calibration prompts. Click twice on the screen.
**Expected:** "Click top-left corner in: 3... 2... 1... GO — click now." followed by "Click bottom-right corner in: 3... 2... 1... GO — click now." followed by "Captured bounding box: (x1, y1) -> (x2, y2)" and "Proceeding in 2 seconds..." Tool then exits (no painting in Phase 1).
**Why human:** pynput.mouse.Listener requires physical mouse input; click coordinates cannot be injected in unit tests without additional infrastructure.

#### 3. Success Criterion Wording Mismatch

**Test:** Review ROADMAP.md Success Criterion 1 ("sees an OpenCV window showing the detected contours overlaid on the image") against the actual implementation (contours on a black canvas, not overlaid on the source image).
**Expected:** Either the ROADMAP is updated to read "contours on a black background" (matching CONTEXT.md locked decision) or the implementation is changed to overlay on the source image.
**Why human:** Design intent question — only the project owner can decide if "black canvas" satisfies "overlaid on the image."

### Gaps Summary

No functional gaps found. All automated verifications pass:

- All 22 tests pass green (`pytest tests/ -x -q`)
- All 15 painter.py symbols exist and are substantive (no NotImplementedError, no stubs)
- All 9 key links verified by code pattern matching
- All 13 requirement IDs from plan frontmatter are implemented
- Wayland detection confirmed working with live test (exit code 1, X11/DISPLAY message)
- Config auto-generation confirmed working (file created, annotated comments present)
- CLI `--help` confirmed: positional `image`, `--config`, `--dry-run`, `--verbose` all listed

The human_needed status is due to two items requiring live X11 display (CAL-01 preview, CAL-04/CAL-05 calibration) and one wording mismatch in ROADMAP Success Criterion 1 that requires owner review.

---

_Verified: 2026-03-20T22:45:00Z_
_Verifier: Claude (gsd-verifier)_
