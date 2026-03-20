# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** Accurately trace detected contours as smooth, ordered mouse strokes within a user-defined screen bounding box
**Current focus:** Phase 1 — Image Pipeline and Safety

## Current Position

Phase: 1 of 3 (Image Pipeline and Safety)
Plan: 0 of ? in current phase
Status: Ready to plan
Last activity: 2026-03-19 — Roadmap created

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Terminal prompts for calibration — simpler, cross-platform, runs in background cleanly
- [Init]: YAML config file over CLI args — cleaner UX for many parameters, easy to share
- [Init]: OpenCV preview window before painting — user confirms contour quality before any mouse movement
- [Init]: Esc hotkey for abort via pynput daemon thread — more intentional than mouse-corner failsafe
- [Research]: pyautogui.PAUSE must be set to 0 at startup — default 0.1s makes tool 10–100x too slow
- [Research]: Contour ordering (nearest-neighbor) required in Phase 2 — not polish, core quality requirement

### Pending Todos

None yet.

### Blockers/Concerns

- Wayland: tool can only support X11/XWayland; pure Wayland sessions will fail fast with an error (accepted limitation)
- Optimal epsilon default is image-resolution-dependent; starting value of 1.5px needs validation against real STS2 images
- Ideal inter_stroke_delay depends on target application responsiveness; safe default range is 0.05–0.1s

## Session Continuity

Last session: 2026-03-19
Stopped at: Roadmap created, STATE.md initialized — ready to plan Phase 1
Resume file: None
