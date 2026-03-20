# Project Research Summary

**Project:** STS2 Map Painter (slaypentri)
**Domain:** Image-to-mouse-stroke automation / contour replay CLI tool
**Researched:** 2026-03-19
**Confidence:** HIGH

## Executive Summary

STS2 Map Painter is a single-file Python CLI tool that converts a PNG image into a sequence of mouse strokes replayed on screen, effectively "painting" the image in any drawing application. The canonical expert approach follows a linear pipeline: load image, detect edges (Canny), extract contours (OpenCV findContours), simplify points (Douglas-Peucker), normalize coordinates, calibrate screen bounding box via two-point click, preview the result, then replay contours as pyautogui mouse strokes. This pipeline is well-established, the required libraries are mature and stable, and the scope is intentionally narrow — no GUI, no fill modes, no multi-monitor support. All four research streams agree on this approach.

The recommended stack is Python 3.11+, opencv-python 4.13, pyautogui 0.9.54, pynput 1.8.1, numpy 2.4.3, and pyyaml 6.0.3 — all verifiable on PyPI as of 2026-03-19. The project's single-file constraint is a hard boundary: no GUI frameworks, no external RDP libraries. The architecture should use an AppState dataclass passed through sequential phase functions, with a daemon thread for the Esc abort listener using threading.Event — a proven pattern that avoids the main thread-blocking problem inherent to pyautogui's synchronous mouse API.

The primary risks are platform-related (pyautogui and pynput both require X11, not native Wayland) and algorithmic (contour ordering must be implemented from the start to prevent visible jump artifacts; pyautogui's default 0.1s PAUSE will make the tool unusably slow if not disabled). Both risks are well-understood and have clear mitigations that must be baked in from Phase 1, not added later.

## Key Findings

### Recommended Stack

The project should use opencv-python as the sole computer vision library — it provides Canny edge detection, findContours, and approxPolyDP (Douglas-Peucker) in a single package with no additional dependencies. The built-in `cv2.approxPolyDP()` is strictly preferred over third-party RDP packages (`rdp`, `simplification`) because it operates natively on OpenCV contour arrays and this project will never process the GIS-scale point counts those packages optimize for. pyautogui 0.9.54 is mandated by PROJECT.md and remains the only viable single-library option for X11/XWayland on Linux without root access. pynput 1.8.1 provides the background keyboard listener needed for mid-paint Esc abort.

**Core technologies:**
- opencv-python 4.13: edge detection, contour extraction, point simplification, preview window — all in one package
- pyautogui 0.9.54: mouse stroke replay (mouseDown/moveTo/mouseUp) — PROJECT.md mandated; X11/XWayland only
- pynput 1.8.1: background keyboard listener for Esc abort — daemon thread pattern; X11/XWayland only
- numpy 2.4.3 (Python 3.11+) or 2.1.x (Python 3.10): array operations for coordinate math
- pyyaml 6.0.3: YAML config file loading via `yaml.safe_load()` only
- scikit-image 0.26.0: optional — only if OpenCV Canny is insufficient for noisy inputs

### Expected Features

The entire MVP feature set is P1 — every item in the must-have list is a dependency of something else or a direct user safety requirement. There are no nice-to-have tradeoffs in the core pipeline: remove any stage and the tool either doesn't work or is unsafe to run.

**Must have (table stakes):**
- PNG loading + grayscale conversion — entry point
- Canny edge detection with configurable `threshold1`, `threshold2`, `blur_kernel_size` — core vision step
- Contour extraction + minimum arc-length filter — converts edges to drawable polylines, removes noise
- Douglas-Peucker simplification with configurable epsilon — reduces redundant points without degrading quality
- OpenCV preview window showing detected contours before painting — hard gate; user must confirm before any mouse movement
- Two-point terminal-guided screen calibration with coordinate confirmation — defines the canvas bounding box
- Aspect-ratio-preserving coordinate normalization and canvas mapping — bridges image space to screen space
- Configurable countdown delay before first stroke — time for user to focus target application window
- Mouse stroke replay (mouseDown + moveTo loop + mouseUp) with pyautogui PAUSE=0 and configurable inter-stroke delay
- Esc abort hotkey via pynput daemon thread with threading.Event — must also release mouse on abort
- YAML config file with annotated defaults for all parameters
- Progress reporting (stroke N/M) during replay

**Should have (competitive):**
- Contour ordering by spatial proximity (nearest-neighbor greedy sort) — eliminates visible jump artifacts; this is actually required for quality output and should be included in v1
- Contour start-point optimization (choose closer endpoint per contour) — trivial addition alongside ordering
- Contour count and estimated time shown in preview window — prevents user from committing to multi-hour runs unknowingly
- Named config profiles via `--profile` argument — useful once users accumulate per-image tuning

**Defer (v2+):**
- Auto Canny threshold selection (Otsu-based) — useful but users can tune manually first
- Contour hierarchy traversal for nested shapes — only valuable for complex nested line art
- Batch mode (multiple images sequentially) — defer until single-image workflow is validated

### Architecture Approach

The tool uses a linear phase pipeline with a shared AppState dataclass as the single source of truth. `main()` instantiates AppState once and calls each phase function in sequence: load_config → run_image_pipeline → run_calibration → run_preview → start_hotkey_listener → run_replay. The image pipeline is purely functional (no side effects, individually testable). The only cross-thread boundary is the abort_flag (threading.Event) written by the pynput listener and read by the replay loop. All code lives in a single file (`slaypentri.py`) organized by section-header comments that match execution order.

**Major components:**
1. Config Loader — reads YAML, applies defaults, validates ranges; only component that reads YAML directly
2. Image Pipeline — grayscale → Canny → findContours → simplify → filter → normalize; purely functional, returns normalized polylines in 0.0–1.0 coords
3. Calibration / Capture — terminal-guided two-point bbox capture; owns screen interaction before painting
4. Preview (OpenCV) — draws contours on image copy, blocks on waitKey; outputs proceed/abort decision; must run on main thread
5. Coordinate Transformer — stateless math function; maps 0.0–1.0 normalized coords to screen pixels within bbox
6. Hotkey Listener — pynput daemon thread; sets abort_flag on Esc; never touches mouse or contours
7. Replay Engine — drives pyautogui stroke-by-stroke; polls abort_flag; owns all mouse control
8. AppState — dataclass shared across all phases; single source of truth

### Critical Pitfalls

1. **pyautogui silently does nothing on native Wayland** — detect `XDG_SESSION_TYPE` at startup; fail fast with an actionable error message pointing to X11/XWayland requirement. A no-op run that paints nothing and exits cleanly is worse than a crash. Address in Phase 1.

2. **pyautogui PAUSE=0.1 default makes the tool 10x–100x too slow** — set `pyautogui.PAUSE = 0` at script startup before any moveTo calls; add explicit `time.sleep()` only between strokes via configurable `inter_stroke_delay`. A 200-point contour takes 20 seconds at default PAUSE vs under 1 second at PAUSE=0. Address in Phase 2 during initial replay implementation.

3. **Contour ordering: findContours returns scan-line order, not spatial order** — without nearest-neighbor sorting, the mouse jumps erratically across canvas between strokes, producing visible drag artifacts and wasted time. The greedy O(n²) sort is ~20 lines of code and must be included from the start, not added as polish. Address in Phase 2.

4. **Coordinate mapping transposition: numpy [row,col] vs OpenCV [x,y]** — OpenCV contour points are [x,y] (column,row); numpy array indexing is [row,col]. Mixing these conventions transposes the entire drawing. Normalize explicitly using named variables; validate with a diagonal test image before any real artwork. Address in Phase 2.

5. **Thread safety and mouse release on abort** — use threading.Event (not a plain bool) for the abort flag; check abort inside the per-contour moveTo loop, not just between contours; always call pyautogui.mouseUp() in the abort handler and in a try/except FailSafeException block around the entire replay loop. Address in Phase 1 before the replay loop exists.

## Implications for Roadmap

Based on combined research, the natural phase structure follows the hard dependency chain in the feature set: you cannot paint without contours, cannot position contours without calibration, and cannot safely paint without the abort mechanism. The architecture's suggested build order (from ARCHITECTURE.md) maps directly to a two-phase roadmap.

### Phase 1: Foundation and Safety Infrastructure

**Rationale:** The config loader, image pipeline, preview, calibration, and abort infrastructure are all prerequisites for any mouse activity. They can be built and tested without touching the screen. Building safety infrastructure (abort, Wayland detection, FAILSAFE handling) before the replay loop ensures it is never an afterthought.

**Delivers:** A fully working image processing pipeline with visual preview, screen calibration, and a wired abort mechanism. The tool can show contours and capture a canvas bbox but not yet paint.

**Addresses:** PNG loading, Canny edge detection, contour extraction, minimum length filter, Douglas-Peucker simplification, OpenCV preview window, two-point calibration, YAML config with annotated defaults, Esc abort infrastructure (threading.Event + pynput daemon), Wayland detection and early exit.

**Avoids:** Wayland silent failure (Pitfall 1), undetected thread safety issues (Pitfall 8), pynput listener failure mode (Pitfall 2), edge detection producing unusable contour counts without filtering (Pitfall 6).

### Phase 2: Coordinate Mapping and Replay Engine

**Rationale:** With the pipeline and safety infrastructure in place, the coordinate transformer and replay engine can be built against real calibration data. pyautogui PAUSE must be set to 0 from the first line of the replay implementation. Contour ordering and start-point optimization must be included in this phase — retrofitting them later after users report jump artifacts is unnecessary.

**Delivers:** A fully functional end-to-end painting tool. Image in, mouse strokes out.

**Uses:** pyautogui 0.9.54 (moveTo/mouseDown/mouseUp), pynput abort integration, coordinate transformer (normalization math), contour nearest-neighbor ordering, start-point optimization per contour.

**Implements:** Coordinate Transformer component, Replay Engine component, aspect-ratio-preserving canvas mapping.

**Avoids:** pyautogui PAUSE performance trap (Pitfall 5), contour ordering jump artifacts (Pitfall 3), coordinate transposition (Pitfall 4), FAILSAFE corner crash without mouse release (Pitfall 9).

### Phase 3: UX Polish and Configuration Completeness

**Rationale:** Once painting works correctly, the remaining high-value items are low-complexity UX improvements that make the tool production-ready: countdown timer, progress reporting, contour count and time estimate in preview, named config profiles, and clear error messages for common failure modes.

**Delivers:** A tool users can hand to someone else without a tutorial. Includes all annotated config defaults, per-session progress feedback, and actionable error messages.

**Addresses:** Countdown delay before painting, progress output (stroke N/M), contour count + estimated time in preview, named config profiles (`--profile`), config key validation with warnings on unknown keys, clear error messages for no-contours-detected, image-not-found, calibration timeout.

**Avoids:** UX pitfalls (no count shown before painting, no progress during replay, bbox capture without confirmation, abort with no mouse release confirmation).

### Phase Ordering Rationale

- **Safety before painting:** The abort mechanism and Wayland detection must exist before any mouse control code runs. Building them first prevents the "abort as afterthought" failure mode documented in multiple pitfalls.
- **Pipeline before calibration:** The image pipeline is purely functional and fully testable without screen access. Verifying edge detection and contour quality visually in the preview window before attempting any screen interaction removes a confounding variable.
- **Threading introduced late in Phase 1, before replay:** The pynput daemon thread is integrated at the end of Phase 1, after the preview gate but before any mouse movement. This ensures thread correctness is validated with a short integration test before the full replay loop exists.
- **Contour ordering in Phase 2, not Phase 3:** Research (PITFALLS.md, FEATURES.md) is unambiguous that ordering is a core algorithmic requirement, not polish. It belongs with the replay implementation.

### Research Flags

Phases with standard, well-documented patterns (skip research-phase during planning):
- **Phase 1:** All components follow documented OpenCV and Python standard library patterns. Canny, findContours, approxPolyDP, threading.Event, pynput.keyboard.Listener, yaml.safe_load — all have official documentation and multiple tutorials.
- **Phase 2:** Coordinate transformation is pure linear math. pyautogui mouse API is minimal. Nearest-neighbor sort is a standard greedy algorithm. No novel integration required.
- **Phase 3:** Pure UX and config — no new libraries or algorithms.

No phases require `/gsd:research-phase` during planning. All needed research has been completed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified against PyPI on 2026-03-19; numpy/Python version matrix explicitly checked; no version conflicts identified |
| Features | HIGH (core), MEDIUM (differentiators) | Core pipeline features are unambiguous dependencies; differentiator features (named profiles, auto-threshold) are reasonable but not validated against user demand |
| Architecture | HIGH | Linear pipeline with AppState dataclass is a standard Python CLI pattern; threading.Event abort pattern is documented in pynput's own guidance; Wayland caveat is MEDIUM (compositor-specific behavior varies) |
| Pitfalls | HIGH | 9 specific pitfalls identified with verified sources; most confirmed against official GitHub issues and library documentation; pyautogui Wayland failure confirmed unfixed as of 2025 |

**Overall confidence:** HIGH

### Gaps to Address

- **Pure Wayland handling:** pyautogui's Wayland incompatibility is documented and unfixed. The tool's stated platform is "Linux (X11/Wayland)" but it can only reliably support X11/XWayland. The mitigation (detect at startup, fail with actionable message) is clear, but the user experience on pure Wayland sessions remains poor. If the target user runs a pure Wayland session without XWayland, the tool will not function. This is an accepted limitation per PROJECT.md scope but should be prominently documented.

- **Optimal epsilon default:** The research recommends starting at epsilon=1.5 pixels for Douglas-Peucker simplification, but the ideal default is image-resolution-dependent. The YAML config should also support `epsilon_pct` (as a fraction of image diagonal) as an alternative to pixel-absolute epsilon. This needs validation against real STS2 map images during implementation.

- **Application-specific inter-stroke delay:** The optimal `inter_stroke_delay` value depends on how fast the target drawing application processes mouseDown/mouseUp events. The documented safe default range is 0.05–0.1s, but this should be validated against the specific game canvas (STS2) during Phase 2 testing.

## Sources

### Primary (HIGH confidence)
- PyPI: opencv-python 4.13.0.92 — https://pypi.org/project/opencv-python/
- PyPI: pyautogui 0.9.54 — https://pypi.org/project/PyAutoGUI/
- PyPI: pynput 1.8.1 — https://pypi.org/project/pynput/
- PyPI: numpy 2.4.3 — https://pypi.org/project/numpy/
- PyPI: pyyaml 6.0.3 — https://pypi.org/project/pyyaml/
- OpenCV approxPolyDP docs — https://docs.opencv.org/4.x/d3/dc0/group__imgproc__shape.html
- OpenCV Canny tutorial — https://docs.opencv.org/3.4/da/d22/tutorial_py_canny.html
- OpenCV findContours tutorial — https://docs.opencv.org/3.4/d4/d73/tutorial_py_contours_begin.html
- pynput keyboard listener docs — https://pynput.readthedocs.io/en/latest/keyboard.html
- pyautogui mouse control docs — https://pyautogui.readthedocs.io/en/latest/mouse.html
- pyautogui FAILSAFE documentation — https://pyautogui.readthedocs.io/en/latest/index.html

### Secondary (MEDIUM confidence)
- pynput Wayland listener issues #628, #331 — https://github.com/moses-palmer/pynput/issues/628 (open as of 2025)
- pyautogui Wayland issues #695, #881, #909 — confirmed unfixed as of 2025
- wayland-automation v0.2.7 — https://github.com/OTAKUWeBer/Wayland-automation (small project, wlroots-only)
- GitHub: dmcbx/AUTO-DRAW-BOT — competitor feature analysis
- GitHub: PIPIKAI/auto-painter-win — competitor feature analysis
- GitHub: FireyPixels/picatrix — nearest-neighbor path ordering reference
- Optimal Path Planning for Pen Plotters (EngineerDog) — nearest-neighbor TSP strategies
- PyImageSearch: OpenCV Contour Approximation — https://pyimagesearch.com/2021/10/06/opencv-contour-approximation/

### Tertiary (LOW confidence)
- PyPI: simplification 0.7.14 — search-verified only; irrelevant to this project's scale
- PyPI: keyboard 0.13.5 — confirmed abandoned (2020); explicitly excluded from stack

---
*Research completed: 2026-03-19*
*Ready for roadmap: yes*
