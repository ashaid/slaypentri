# Phase 2: Coordinate Mapping and Replay - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Map normalized [0,1] contours to screen pixel space within the calibrated bounding box, then replay each contour as pyautogui mouse drag strokes. Includes contour sorting, abort mechanism, and progress reporting. No changes to image processing or calibration — those are done in Phase 1.

</domain>

<decisions>
## Implementation Decisions

### Aspect Ratio Mapping
- **D-01:** Preserve aspect ratio when mapping to bounding box — no stretching/distortion
- **D-02:** Fill the largest fitting axis (letterbox/pillarbox), center on the shorter axis
- **D-03:** Contours scale to fill the bounding box on whichever axis fits, margins only on the other axis

### Stroke Replay Speed
- **D-04:** Configurable countdown delay before first stroke (`painting.start_delay`, default: 3 seconds), prints countdown in terminal
- **D-05:** Inter-point delay defaults to 0 (`painting.inter_point_delay: 0`) — fastest possible. User increases if target app drops inputs
- **D-06:** Inter-stroke delay configurable (`painting.inter_stroke_delay: 0.05`) — 50ms pause between contours
- **D-07:** Progress reported via inline overwrite (`\r`) — single line: `Painting: 42/128 strokes (33%)` with progress bar

### Contour Ordering
- **D-08:** Nearest-neighbor greedy sort — start from bbox top-left, pick closest contour endpoint, paint it, repeat from current position
- **D-09:** For each contour, compare distance from current cursor to both endpoints — start from whichever is closer (halves average travel)

### Abort Mechanism
- **D-10:** Esc sets `abort_flag` (threading.Event already on AppState). Current contour finishes (mouseDown→moveTo→mouseUp completes), then loop breaks. No partial strokes.
- **D-11:** pynput background daemon thread for Esc listener — same library already used for calibration clicks, imported lazily
- **D-12:** mouseUp guaranteed on ALL exit paths via try/finally wrapping the painting loop — prevents stuck mouse button on crashes
- **D-13:** On abort: print "Aborted after N/M strokes." and exit code 0

### Claude's Discretion
- Exact progress bar formatting (width, characters)
- Whether to print total painting time at completion
- Edge case handling for very small contours (< 2 points)
- Whether to skip contours that map to a single pixel after coordinate transform

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Context
- `.planning/PROJECT.md` — Core value, constraints (single file, specific dependencies, Linux/Python 3.10+)
- `.planning/REQUIREMENTS.md` — Phase 2 requirements: CAL-06, CAL-07, PAINT-01..08

### Phase 1 Context (prior decisions)
- `.planning/phases/01-image-pipeline-and-safety/01-CONTEXT.md` — Config structure, calibration flow, safety decisions
- `.planning/phases/01-image-pipeline-and-safety/01-VERIFICATION.md` — What was verified in Phase 1

### Research
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow, coordinate math
- `.planning/research/PITFALLS.md` — pyautogui.PAUSE default, contour ordering issues, thread safety

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppState.contours_normalized` — List of (N,2) float32 arrays in [0,1] range, ready for coordinate mapping
- `AppState.bbox` — `(x1, y1, x2, y2)` screen pixels from calibration
- `AppState.abort_flag` — `threading.Event` already wired on the dataclass
- `AppState.dry_run` — Skip painting when true (already handled in main flow)
- `capture_click_position()` — pynput lazy import pattern established here, reuse for Esc listener

### Established Patterns
- Lazy imports: pyautogui and pynput imported inside functions, not at module level (Wayland fix)
- Config access: `state.config.get("section", {}).get("key", default)`
- Verbose logging: `if state.verbose: print(f"[DEBUG] ...")`
- Requirement tracing: docstrings reference requirement IDs (e.g., `"""CAL-06: ...`)

### Integration Points
- `main()` calls pipeline → preview → calibration → [Phase 2 adds: coordinate mapping → painting]
- New functions slot in after `run_calibration(state)` in `main()`
- Config YAML gains new keys under `painting:` section (start_delay, inter_point_delay, inter_stroke_delay)

</code_context>

<specifics>
## Specific Ideas

- Nearest-neighbor sort starts from bbox top-left to create a natural left-to-right painting feel
- Progress bar overwrites in-place to keep terminal clean during potentially long painting sessions
- try/finally for mouseUp is critical — a stuck right-click button in a game would be very disruptive

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-coordinate-mapping-and-replay*
*Context gathered: 2026-03-20*
