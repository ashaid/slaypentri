# Milestones

## v1.0 MVP (Shipped: 2026-03-21)

**Phases completed:** 3 phases, 8 plans, 15 tasks

**Key accomplishments:**

- pytest test scaffold with 22 stub tests across 4 files covering CFG-01/05/06 and IMG-01..06 — all skip cleanly before painter.py exists
- One-liner:
- OpenCV 8-step image pipeline (load -> grayscale -> blur -> Canny -> findContours -> approxPolyDP -> arcLength filter -> normalize) with Otsu auto-threshold, producing resolution-independent (N,2) float32 contour arrays in [0,1]
- OpenCV rainbow-contour preview window and pynput two-click calibration with lazy X11 library imports to enable clean Wayland detection before display connection
- Three pure functions in painter.py — letterbox/pillarbox bbox mapping and nearest-neighbor contour sort — with 11-test suite using numpy array math and no screen interaction
- pyautogui replay engine with countdown, Esc abort via pynput daemon, inline progress bar, guaranteed mouseUp via try/finally — verified end-to-end on real screen; bbox normalization bug fixed for any click-corner order
- Painting time estimate printed to terminal before preview window using actual config values, plus value-range annotations for all 9 config parameters in DEFAULT_CONFIG_CONTENT
- README.md with installation, quick-start, full 10-parameter config reference, and troubleshooting; plus a programmatically generated 400x400 star PNG producing 13 contours

---
