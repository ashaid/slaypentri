# STS2 Map Painter

## What This Is

A single-file Python tool that takes a PNG image, detects its edges and contours, then replays those contours as mouse drag strokes over any screen region — designed for painting line art onto the Satisfactory (STS2) map canvas, but works anywhere a cursor can draw.

## Core Value

Accurately trace detected contours as smooth, ordered mouse strokes within a user-defined screen bounding box.

## Requirements

### Validated

- [x] Load PNG, convert to grayscale, run Canny edge detection — Validated in Phase 1
- [x] Extract ordered contour polylines from edge map — Validated in Phase 1
- [x] Capture mode: terminal-guided flow to click two reference points (top-left, bottom-right) defining the drawing canvas bounding box — Validated in Phase 1
- [x] Confirmation step showing captured bounding box coordinates before proceeding — Validated in Phase 1
- [x] OpenCV preview window showing detected contours before painting (press key to proceed or abort) — Validated in Phase 1
- [x] YAML/JSON config file for all tunable parameters — Validated in Phase 1
- [x] Point simplification (Douglas-Peucker or similar) to reduce dense redundant points — Validated in Phase 1
- [x] Minimum contour length filter to discard noise — Validated in Phase 1

### Active

- [ ] Normalize contour coordinates to 0–1 range and map to screen pixel space via reference bounding box
- [ ] Replay each contour as mouseDown → moveTo sequence → mouseUp with configurable delay
- [ ] Esc hotkey listener to abort mid-painting
- [ ] README with usage docs and example images
- [ ] Sample config file(s) with sensible defaults
- [ ] Example PNG(s) for testing

### Out of Scope

- Game memory integration or API hooks — purely mouse-based, works over any window
- GUI/TUI configuration interface — config file is sufficient
- Real-time edge detection tuning — preview is static, re-run with new params if needed
- Multi-monitor support — single screen assumed
- Color or fill painting — line contours only

## Context

- Target game is Satisfactory (STS2) map painter, but the tool is game-agnostic — it just moves the mouse
- Input images are ideally clean line art or high-contrast outlines (logos, borders, simple drawings)
- PyAutoGUI handles all mouse control; no OS-specific APIs needed
- Dependencies: opencv-python, scikit-image, pyautogui, numpy, pyyaml
- Single Python script — no package structure needed

## Constraints

- **Single file**: One `.py` script — no modules, no package
- **Dependencies**: opencv-python, scikit-image, pyautogui, numpy, pyyaml only
- **Platform**: Needs to work on Linux (X11/Wayland) — user's environment
- **Python**: 3.10+ assumed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Terminal prompts for calibration (not overlay) | Simpler, works cross-platform, runs in background cleanly | Implemented Phase 1 |
| YAML config file (not CLI args) | Cleaner UX for many parameters, easy to share/version configs | Implemented Phase 1 |
| OpenCV preview window before painting | Lets user verify contour detection quality before committing to paint | Implemented Phase 1 |
| Esc hotkey for abort (not mouse-corner failsafe) | More intentional, less accidental triggers | — Pending |
| Black canvas preview (not image overlay) | Cleaner contrast for contour visibility, deliberate design choice | Implemented Phase 1 |
| Lazy pyautogui/pynput imports | Module-level import crashes when DISPLAY is unset; lazy import allows safety check first | Implemented Phase 1 |

---
*Last updated: 2026-03-20 after Phase 1 completion*
