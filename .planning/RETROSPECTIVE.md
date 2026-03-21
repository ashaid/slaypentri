# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-20
**Phases:** 3 | **Plans:** 8 | **Sessions:** ~4

### What Was Built
- Full image pipeline: PNG → grayscale → Canny → contours → Douglas-Peucker simplification → normalized coordinates
- Two-click calibration with aspect-ratio-preserving letterbox/pillarbox mapping
- pyautogui replay engine with nearest-neighbor contour sorting, Esc abort, progress bar, guaranteed mouseUp
- Time estimate in preview, self-documenting config, README, example PNG

### What Worked
- TDD-first approach (Wave 0 test scaffold before any implementation) caught import issues early and kept coverage high
- Phase ordering (no-mouse-movement first, replay second, polish third) meant each phase could be tested independently
- Lazy imports for pyautogui/pynput solved the Wayland/headless detection problem cleanly
- Parallel plan execution in Phase 3 (both plans in Wave 1) saved time with no conflicts

### What Was Inefficient
- Phase 1 had 4 plans for what was effectively one module — could have been 2-3 plans
- Some test stubs in Wave 0 were overly specific and needed adjustment when implementation details shifted

### Patterns Established
- Lazy import pattern for display-dependent libraries (check environment before importing)
- try/finally for guaranteed resource cleanup (mouseUp) on all exit paths
- Bbox min/max normalization so click order doesn't matter
- approxPolyDP in pixel space before normalization (epsilon stays intuitive in px units)

### Key Lessons
1. Test scaffolds before implementation (Wave 0) work well for single-file projects — they define the API contract early
2. Nearest-neighbor contour sorting is a core quality requirement, not polish — should be in Phase 1 scope next time
3. pyautogui.PAUSE=0 is mandatory at startup — the 0.1s default makes the tool unusable at scale

### Cost Observations
- Model mix: ~30% opus (planning/orchestration), ~70% sonnet (execution/verification)
- Sessions: ~4 sessions across 1 day
- Notable: Phase 3 executed both plans in parallel with no merge conflicts — good wave grouping

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~4 | 3 | Initial project — established TDD-first, lazy-import patterns |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 45 | High (all paths) | 0 |

### Top Lessons (Verified Across Milestones)

1. TDD-first with test scaffolds defines clean API contracts before implementation
2. Lazy imports solve environment detection for display-dependent libraries
