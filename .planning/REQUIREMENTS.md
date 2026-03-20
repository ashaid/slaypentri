# Requirements: STS2 Map Painter

**Defined:** 2026-03-19
**Core Value:** Accurately trace detected contours as smooth, ordered mouse strokes within a user-defined screen bounding box

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Image Processing

- [x] **IMG-01**: User can load any PNG and have it converted to grayscale automatically
- [x] **IMG-02**: Tool runs Canny edge detection with configurable low/high thresholds and blur kernel size
- [x] **IMG-03**: Tool provides Otsu-based auto-threshold as a fallback when thresholds set to "auto"
- [x] **IMG-04**: Tool extracts ordered contour polylines from the edge map
- [x] **IMG-05**: Tool filters out contours below a configurable minimum arc-length
- [x] **IMG-06**: Tool simplifies contour points using Douglas-Peucker with configurable epsilon

### Preview & Calibration

- [x] **CAL-01**: Tool displays detected contours in an OpenCV preview window before painting
- [x] **CAL-02**: User can abort from preview (Esc) or proceed (any other key)
- [ ] **CAL-03**: Preview shows contour count and estimated painting time
- [x] **CAL-04**: Terminal-guided capture mode: user clicks top-left then bottom-right to define canvas bounding box
- [x] **CAL-05**: Tool displays captured bounding box coordinates for confirmation before proceeding
- [x] **CAL-06**: Tool maps contour coordinates to screen space preserving aspect ratio (no stretching)
- [ ] **CAL-07**: Configurable countdown delay before first stroke begins

### Painting & Control

- [ ] **PAINT-01**: Tool replays each contour as right-click mouseDown → moveTo sequence → mouseUp
- [ ] **PAINT-02**: Mouse button for strokes is configurable (default: right)
- [ ] **PAINT-03**: Inter-point delay is configurable for stroke speed tuning
- [x] **PAINT-04**: Contours are sorted by spatial proximity (nearest-neighbor) to minimize travel
- [x] **PAINT-05**: Tool picks optimal start-point (closest endpoint) for each contour
- [ ] **PAINT-06**: Esc hotkey aborts painting mid-stroke via background listener thread
- [ ] **PAINT-07**: Tool prints stroke progress (N/M, percentage) to terminal during painting
- [ ] **PAINT-08**: Tool calls mouseUp on all exit paths (normal, abort, exception)

### Configuration & Docs

- [x] **CFG-01**: All parameters stored in a YAML config file with sensible defaults
- [ ] **CFG-02**: Sample config file with annotated comments explaining each parameter
- [ ] **CFG-03**: README with usage instructions, parameter documentation, and example workflow
- [ ] **CFG-04**: Example PNG(s) included for testing
- [x] **CFG-05**: Tool detects Wayland-only sessions and fails with an actionable error message
- [x] **CFG-06**: pyautogui.PAUSE set to 0 at startup to avoid 0.1s default penalty

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Configuration

- **CFG-V2-01**: Multiple named config profiles selectable via --profile flag

### Image Processing

- **IMG-V2-01**: Contour hierarchy traversal for nested shapes (parent-child relationships)
- **IMG-V2-02**: Batch mode to process multiple images sequentially

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time / interactive edge threshold tuning (slider UI) | Requires GUI framework, violates single-file constraint |
| GUI/TUI configuration interface | YAML config is sufficient for the parameter space |
| Color or fill painting | Fundamentally different pipeline, not core value |
| Multi-monitor support | Single screen assumed; move target window to primary |
| Game memory / API hooks | Tool is game-agnostic, purely mouse-based |
| Undo / replay control | Esc abort + re-run is simpler and more reliable |
| Automatic canvas detection | Screen region detection is brittle; two-click calibration is fast and reliable |
| Wacom/stylus pressure simulation | No pressure API in pyautogui; different product category |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| IMG-01 | Phase 1 | Complete |
| IMG-02 | Phase 1 | Complete |
| IMG-03 | Phase 1 | Complete |
| IMG-04 | Phase 1 | Complete |
| IMG-05 | Phase 1 | Complete |
| IMG-06 | Phase 1 | Complete |
| CAL-01 | Phase 1 | Complete |
| CAL-02 | Phase 1 | Complete |
| CAL-03 | Phase 3 | Pending |
| CAL-04 | Phase 1 | Complete |
| CAL-05 | Phase 1 | Complete |
| CAL-06 | Phase 2 | Complete |
| CAL-07 | Phase 2 | Pending |
| PAINT-01 | Phase 2 | Pending |
| PAINT-02 | Phase 2 | Pending |
| PAINT-03 | Phase 2 | Pending |
| PAINT-04 | Phase 2 | Complete |
| PAINT-05 | Phase 2 | Complete |
| PAINT-06 | Phase 2 | Pending |
| PAINT-07 | Phase 2 | Pending |
| PAINT-08 | Phase 2 | Pending |
| CFG-01 | Phase 1 | Complete |
| CFG-02 | Phase 3 | Pending |
| CFG-03 | Phase 3 | Pending |
| CFG-04 | Phase 3 | Pending |
| CFG-05 | Phase 1 | Complete |
| CFG-06 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after roadmap creation*
