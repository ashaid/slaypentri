# STS2 Map Painter

## What This Is

A single-file Python tool that takes a PNG image, detects its edges and contours, then replays those contours as mouse drag strokes over any screen region — designed for painting line art onto the Satisfactory (STS2) map canvas, but works anywhere a cursor can draw.

## Core Value

Accurately trace detected contours as smooth, ordered mouse strokes within a user-defined screen bounding box.

## Current State

Shipped v1.0 MVP. 752 LOC in `painter.py`, 821 LOC across 6 test files (45 tests). Single-file Python tool with full image pipeline, replay engine, and documentation.

Tech stack: Python 3.10+, opencv-python, scikit-image, pyautogui, pynput, numpy, pyyaml.

## Requirements

### Validated

- ✓ Load PNG, convert to grayscale, run Canny edge detection — v1.0
- ✓ Extract ordered contour polylines from edge map — v1.0
- ✓ Terminal-guided two-click calibration for canvas bounding box — v1.0
- ✓ Confirmation step showing captured bounding box coordinates — v1.0
- ✓ OpenCV preview window with detected contours — v1.0
- ✓ YAML config file for all tunable parameters — v1.0
- ✓ Point simplification (Douglas-Peucker) — v1.0
- ✓ Minimum contour length filter — v1.0
- ✓ Coordinate normalization and screen-space mapping with aspect ratio — v1.0
- ✓ Contour replay as mouseDown → moveTo → mouseUp with configurable delay — v1.0
- ✓ Esc hotkey abort mid-painting — v1.0
- ✓ Preview time estimate with contour count — v1.0
- ✓ Self-documenting config with value ranges — v1.0
- ✓ README with installation, usage, and config reference — v1.0
- ✓ Example PNG for new users — v1.0

### Active

(none — planning next milestone)

### Out of Scope

- Game memory integration or API hooks — purely mouse-based, works over any window
- GUI/TUI configuration interface — config file is sufficient
- Real-time edge detection tuning — preview is static, re-run with new params if needed
- Multi-monitor support — single screen assumed
- Color or fill painting — line contours only
- Undo / replay control — Esc abort + re-run is simpler and more reliable
- Wacom/stylus pressure simulation — no pressure API in pyautogui

## Context

- Target game is Satisfactory (STS2) map painter, but the tool is game-agnostic — it just moves the mouse
- Input images are ideally clean line art or high-contrast outlines (logos, borders, simple drawings)
- PyAutoGUI handles all mouse control; no OS-specific APIs needed
- Dependencies: opencv-python, scikit-image, pyautogui, numpy, pyyaml, pynput
- Single Python script — no package structure needed

## Constraints

- **Single file**: One `.py` script — no modules, no package
- **Dependencies**: opencv-python, scikit-image, pyautogui, numpy, pyyaml, pynput only
- **Platform**: Needs to work on Linux (X11/XWayland) — pure Wayland not supported
- **Python**: 3.10+ assumed

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Terminal prompts for calibration (not overlay) | Simpler, works cross-platform, runs in background cleanly | ✓ Good |
| YAML config file (not CLI args) | Cleaner UX for many parameters, easy to share/version configs | ✓ Good |
| OpenCV preview window before painting | Lets user verify contour detection quality before committing to paint | ✓ Good |
| Esc hotkey for abort (not mouse-corner failsafe) | More intentional, less accidental triggers | ✓ Good |
| Black canvas preview (not image overlay) | Cleaner contrast for contour visibility | ✓ Good |
| Lazy pyautogui/pynput imports | Module-level import crashes when DISPLAY is unset; lazy import allows safety check first | ✓ Good |
| RETR_LIST over RETR_EXTERNAL for contours | Preserves inner contours for line art (letter holes, enclosed regions) | ✓ Good |
| Nearest-neighbor contour sorting | Minimizes mouse travel distance between strokes | ✓ Good |
| try/finally for guaranteed mouseUp | Covers normal, abort, and exception exit paths | ✓ Good |
| Bbox min/max normalization | Click-corner order never matters — any two points define the box | ✓ Good |

---
*Last updated: 2026-03-20 after v1.0 milestone*
