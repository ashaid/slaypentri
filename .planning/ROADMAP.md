# Roadmap: STS2 Map Painter

## Overview

Three phases deliver the tool from nothing to production-ready. Phase 1 builds the image processing pipeline and safety infrastructure — everything that can be built and tested without moving the mouse. Phase 2 adds coordinate mapping and the replay engine, making the tool actually paint. Phase 3 completes the UX and documentation, making the tool hand-offable to someone who has never used it.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Image Pipeline and Safety** - Load PNG, detect edges, extract contours, preview result, calibrate canvas, wire abort — no mouse movement yet (completed 2026-03-20)
- [ ] **Phase 2: Coordinate Mapping and Replay** - Map contours to screen space and drive pyautogui to paint every stroke
- [ ] **Phase 3: UX Polish and Docs** - Time estimates, progress output, annotated config, README, and example files

## Phase Details

### Phase 1: Image Pipeline and Safety
**Goal**: User can load a PNG, see detected contours in a preview window, capture a screen bounding box via two clicks, and abort at any time — with no mouse painting yet
**Depends on**: Nothing (first phase)
**Requirements**: IMG-01, IMG-02, IMG-03, IMG-04, IMG-05, IMG-06, CAL-01, CAL-02, CAL-04, CAL-05, CFG-01, CFG-05, CFG-06
**Success Criteria** (what must be TRUE):
  1. User runs the tool with a PNG path and sees an OpenCV window showing the detected contours on a black canvas with rainbow gradient coloring
  2. User can press Esc in the preview window to abort without any mouse movement occurring
  3. After proceeding from preview, user clicks two screen points in the terminal and sees the captured bounding box coordinates printed for confirmation
  4. On a pure Wayland session (no XWayland), the tool exits immediately with a clear error message explaining the X11 requirement
  5. All tunable parameters (Canny thresholds, blur, arc-length filter, epsilon) are read from a YAML config file; missing keys fall back to defaults
**Plans:** 4/4 plans complete

Plans:
- [x] 01-01-PLAN.md — Wave 0: Test scaffold (conftest, test_config, test_safety, test_image_pipeline, requirements.txt)
- [x] 01-02-PLAN.md — Wave 1: painter.py foundation (AppState, config loader, Wayland detection, CLI, main skeleton)
- [x] 01-03-PLAN.md — Wave 2: Image processing pipeline (load, grayscale, blur, Canny, contours, filter, simplify, normalize)
- [x] 01-04-PLAN.md — Wave 3: Preview window + calibration flow (OpenCV preview with rainbow gradient, pynput click capture)

### Phase 2: Coordinate Mapping and Replay
**Goal**: User can run the tool end-to-end and have contours painted onto the target screen region as mouse strokes
**Depends on**: Phase 1
**Requirements**: CAL-06, CAL-07, PAINT-01, PAINT-02, PAINT-03, PAINT-04, PAINT-05, PAINT-06, PAINT-07, PAINT-08
**Success Criteria** (what must be TRUE):
  1. After the countdown delay, contours are drawn onto the screen inside the captured bounding box with correct aspect ratio and no transposition artifacts
  2. Contours are painted in spatial order (nearest-neighbor), so the mouse does not visibly jump erratically between strokes
  3. Pressing Esc during painting stops all mouse movement within one stroke and releases the mouse button before exiting
  4. The terminal prints stroke progress (e.g., "Stroke 42/200 — 21%") during painting
  5. On all exit paths — normal completion, Esc abort, and unhandled exception — mouseUp is called before the process ends
**Plans**: TBD

### Phase 3: UX Polish and Docs
**Goal**: The tool is usable by someone who has never run it — preview gives enough information to decide whether to proceed, and the repo contains everything needed to get started
**Depends on**: Phase 2
**Requirements**: CAL-03, CFG-02, CFG-03, CFG-04
**Success Criteria** (what must be TRUE):
  1. The preview window displays contour count and estimated painting time so the user knows what they are committing to before pressing a key
  2. A sample YAML config file with annotated comments for every parameter is included in the repo
  3. The README explains how to install dependencies, configure the tool, run it, and interpret common errors
  4. At least one example PNG is included so a new user can verify the tool works without sourcing their own image
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Image Pipeline and Safety | 4/4 | Complete   | 2026-03-20 |
| 2. Coordinate Mapping and Replay | 0/? | Not started | - |
| 3. UX Polish and Docs | 0/? | Not started | - |
