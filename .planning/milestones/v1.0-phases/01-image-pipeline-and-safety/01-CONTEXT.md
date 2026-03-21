# Phase 1: Image Pipeline and Safety - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the full image processing pipeline (load PNG → grayscale → Canny edge detection → contour extraction → min-length filter → Douglas-Peucker simplification), OpenCV preview window, terminal-guided screen calibration, YAML config loading, and Wayland detection. No mouse painting in this phase — everything is testable without moving the cursor.

</domain>

<decisions>
## Implementation Decisions

### Preview Window
- Black background with contour lines drawn on top (no original image overlay)
- Contours color-coded with rainbow gradient by drawing order (first contour red → last contour blue)
- Any key proceeds to calibration, Esc aborts the tool
- Terminal prints: "Preview ready. Press any key to continue, Esc to abort."

### Calibration Flow
- 3-second countdown in terminal before capturing each corner click position
- Flow: "Click top-left corner in 3...2...1..." → capture click → "Click bottom-right corner in 3...2...1..." → capture click
- After both clicks: print captured bounding box coordinates, pause 2 seconds for review, then auto-proceed
- No redo mechanism — misclick = Ctrl+C and re-run the tool

### Config File Structure
- YAML format, grouped by concern (sections like `edge_detection:`, `painting:`, `calibration:`, etc.)
- Config file lives next to the script (same directory as `painter.py`)
- If no config file exists on first run, auto-generate `config.yaml` with annotated defaults
- Canny auto-threshold uses special string value `"auto"` in YAML (e.g., `canny_low: auto`) rather than a separate boolean flag

### Script Invocation
- Script named `painter.py`
- Basic usage: `python painter.py image.png` (image path as positional argument)
- CLI flags:
  - `--config path/to/config.yaml` — override default config location
  - `--dry-run` — run pipeline + preview + calibration but skip painting entirely
  - `--verbose` — enable debug output for troubleshooting
- Everything else configured via YAML

### Safety Infrastructure
- Wayland detection at startup: check for `WAYLAND_DISPLAY` without `DISPLAY`, fail with actionable error
- `pyautogui.PAUSE = 0` set at startup
- Right-click (`button='right'`) as default mouse button for strokes (configurable in YAML)

### Claude's Discretion
- Preview window sizing (scale to fit screen vs match source dimensions)
- Exact YAML section names and parameter naming conventions
- Log format for --verbose output
- How click position is captured (pyautogui.position() after pynput click event, or other approach)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research Findings
- `.planning/research/STACK.md` — Library versions, pyautogui Wayland limitation, numpy Python version constraint
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow, coordinate math, build order
- `.planning/research/PITFALLS.md` — Wayland blockers, pyautogui.PAUSE default, contour ordering issues, thread safety
- `.planning/research/FEATURES.md` — Feature dependency chain, MVP definition, competitor analysis

### Project Context
- `.planning/PROJECT.md` — Core value, constraints (single file, specific dependencies, Linux/Python 3.10+)
- `.planning/REQUIREMENTS.md` — Phase 1 requirements: IMG-01..06, CAL-01/02/04/05, CFG-01/05/06

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
None — greenfield project, no existing code.

### Established Patterns
None — first phase establishes all patterns.

### Integration Points
- `painter.py` is the single entry point — all code lives in this one file
- Config file (`config.yaml`) is the external integration point for user customization
- Preview window (OpenCV `imshow`/`waitKey`) is the visual output before Phase 2 adds mouse control

</code_context>

<specifics>
## Specific Ideas

- Auto-generate config with annotated comments on first run — makes the tool self-documenting
- Rainbow gradient contour preview helps user understand drawing order before committing to paint
- 3-second countdown gives time to position cursor at corner without feeling slow

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-image-pipeline-and-safety*
*Context gathered: 2026-03-20*
