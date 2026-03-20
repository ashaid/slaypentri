# Feature Research

**Domain:** Image-to-mouse-stroke automation / auto-drawing tool
**Researched:** 2026-03-19
**Confidence:** HIGH (core features), MEDIUM (differentiators), HIGH (anti-features — grounded in PROJECT.md constraints)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or unsafe to run.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| PNG image loading | Entry point of the entire tool — no image, no purpose | LOW | Grayscale conversion implicit; reject unsupported formats with clear error |
| Canny edge detection with configurable thresholds | Every auto-draw tool does this; it is the core vision step | LOW | `threshold1` (low), `threshold2` (high), Gaussian blur kernel size — all three must be tunable. Otsu auto-threshold is a useful default fallback |
| Contour extraction from edge map | Required to convert pixel edges into drawable polylines | LOW | OpenCV `findContours` with `RETR_LIST` or `RETR_EXTERNAL`; hierarchy ignored for flat line-art |
| Minimum contour length filter | Without it, noise dots create thousands of 1-2px contours that waste time and look terrible | LOW | Single threshold parameter (min pixel length); default ~10px |
| Point simplification (Douglas-Peucker) | Dense edge pixels produce redundant points that slow mouse replay dramatically without improving quality | LOW | Epsilon parameter controls aggressiveness; default ~1.5–2.0px produces clean results |
| OpenCV preview window before painting | Without a pre-paint preview, users commit blind to potentially wrong edge params | MEDIUM | Show detected contours overlaid on image; keypress to proceed, Esc to abort |
| Two-point screen calibration (bounding box capture) | Canvas mapping requires knowing where the drawable area is on screen | MEDIUM | Click top-left, click bottom-right in terminal-guided flow; show captured coordinates for confirmation before proceeding |
| Coordinate normalization and canvas mapping | Bridges image space to screen space; without this, contours land at wrong positions | LOW | Normalize contours to 0–1, then scale to screen bbox; aspect ratio handling matters |
| Mouse stroke replay (mouseDown + moveTo + mouseUp) | The core output action | LOW | PyAutoGUI `mouseDown`, `dragTo` or `moveTo` sequence, `mouseUp`; configurable inter-point delay |
| Configurable stroke speed / inter-point delay | Drawing too fast produces skipped strokes in apps with input rate limits; too slow wastes time | LOW | Single `point_delay_ms` or `stroke_speed` parameter in config |
| Esc hotkey abort during painting | Safety — user must be able to stop a runaway stroke session without killing the terminal | MEDIUM | Keyboard listener in separate thread; PyAutoGUI's built-in corner FAILSAFE is a backup, not a replacement |
| YAML/JSON config file for all parameters | Many parameters need tuning per image; CLI args become unwieldy beyond 3–4 flags | LOW | YAML preferred for human readability; all tunable parameters must have sensible defaults in a sample config |
| Sample config file with annotated defaults | Users cannot guess reasonable Canny thresholds or epsilon values from scratch | LOW | Comments explaining what each parameter does and what range makes sense |
| Clear error messages for bad inputs | Image not found, no contours detected, calibration timeout — all need actionable messages | LOW | "No contours detected — try lowering `canny_threshold1`" is more useful than a stack trace |

### Differentiators (Competitive Advantage)

Features that set this tool apart from basic auto-draw bots. Not all are needed at launch.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Contour ordering by spatial proximity (nearest-neighbor) | Without ordering, the mouse teleports across the canvas between strokes, causing visible artifacts and wasted time. Nearest-neighbor reduces total travel distance significantly | MEDIUM | Sort contours greedily: after finishing contour N, pick the undrawn contour whose start point is closest to current mouse position. O(n^2) but fine for typical contour counts (<5000) |
| Contour start-point optimization | Each contour can be traversed starting from either end; choosing the end nearest to current cursor position halves average inter-stroke travel | LOW | For each candidate contour, compare distance to both endpoints; pick the closer one as the entry point |
| Configurable countdown delay before painting begins | Gives user time to click focus into the target application window after calibration | LOW | 3–5 second countdown in terminal with per-second output; configurable |
| Progress reporting during paint | Long sessions (hundreds of contours) feel frozen without feedback; progress lets users estimate completion | LOW | Print "Stroke N/M (X%)" to terminal at each contour start; negligible performance cost |
| Contour count and estimated time preview | Shown in the preview step before painting; helps user decide whether to tighten the minimum-length filter first | LOW | Compute from detected contours + configurable speed; display alongside preview window |
| Gaussian blur pre-processing parameter | Controls noise reduction before edge detection; critical for photos vs. clean line art | LOW | `blur_kernel_size` in config (must be odd integer); default 3 or 5 works for most line art |
| Aspect-ratio-preserving canvas mapping | Without this, images stretch to fill non-square bounding boxes, distorting the result | LOW | Compute scale factor from min(width_ratio, height_ratio); center the result within the bbox |
| Multiple named config profiles | Users paint different images with different edge settings; named profiles in config file avoid re-tuning each time | LOW | YAML supports multiple named sections; tool accepts `--profile` argument to select one |

### Anti-Features (Commonly Requested, Often Problematic)

Features to deliberately NOT build, with rationale.

| Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Real-time / interactive edge threshold tuning (slider UI) | "I want to see the edges update live as I drag a slider" | Requires a GUI framework (Qt, Tk) that violates the single-file constraint, adds significant complexity, and solves a problem that re-running with new config params already handles adequately | Expose Canny thresholds and blur kernel in YAML config; the preview window + re-run loop is fast enough |
| GUI/TUI configuration interface | Seems like better UX than editing YAML | Adds a full UI framework dependency, is harder to script/automate, and the parameter space is simple enough that YAML comments are sufficient | Provide a well-annotated sample config; document each parameter in README |
| Color or fill painting | "Can it also fill regions, not just draw outlines?" | Fill painting requires a fundamentally different image processing pipeline (flood-fill regions, color quantization), multiplying scope significantly. The core value is contour tracing | Out of scope per PROJECT.md; direct users to tools like AUTO-DRAW-BOT (dmcbx) if they need fill |
| Multi-monitor support | "I have two screens, let me pick which one" | Adds display enumeration complexity and coordinate-space translation across monitors; PyAutoGUI's multi-monitor support is inconsistent on Linux/Wayland | Document single-screen assumption; users can move target window to primary monitor |
| Game memory / API hooks | "Can it read the game state to position more accurately?" | Requires game-specific reverse engineering, breaks cross-app generality, and is out of scope per PROJECT.md | The mouse-based approach works across any app by design |
| Undo / replay control | "Let me pause or rewind mid-paint" | Requires tracking stroke history and implementing reverse mouse actions; the target apps (game canvases) typically don't expose an API that makes undo reliable | Esc abort + re-run from scratch is simpler and more reliable; preview reduces the need to undo |
| Automatic canvas detection (no calibration) | "Can it find the drawing area automatically?" | Screen region detection is brittle — it requires image recognition of the target app's UI, which breaks across app versions, themes, and resolutions | Two-point manual calibration is fast (two clicks), reliable, and explicit |
| Wacom/stylus pressure simulation | "Vary stroke width based on contour curvature" | PyAutoGUI has no pressure API; OS-level pressure injection requires platform-specific drivers and breaks the single-file constraint | Constant-width strokes are appropriate for line art tracing; this is a different product category |

## Feature Dependencies

```
[PNG loading + grayscale conversion]
    └──requires──> [Canny edge detection]
                       └──requires──> [Contour extraction]
                                          └──requires──> [Min-length filter]
                                                             └──requires──> [Point simplification]
                                                                                └──requires──> [Coordinate normalization]
                                                                                                   └──requires──> [Mouse stroke replay]

[OpenCV preview window]
    └──requires──> [Contour extraction] (must exist before preview)
    └──enables──>  [User proceed/abort decision] (gate before painting starts)

[Screen calibration (two-point bbox)]
    └──required by──> [Coordinate normalization] (cannot map without bbox)

[Esc abort hotkey]
    └──requires──> [Background keyboard listener thread] (must run concurrently with stroke replay)

[Contour ordering by proximity]
    └──enhances──> [Mouse stroke replay] (reduces inter-stroke travel; optional but high-value)

[Contour start-point optimization]
    └──requires──> [Contour ordering by proximity] (only useful when ordering is active)

[YAML config]
    └──required by──> all tunable parameters (Canny thresholds, blur kernel, epsilon, delays, filters)

[Countdown delay]
    └──requires──> [Screen calibration complete] (fires after calibration, before first stroke)

[Progress reporting]
    └──requires──> [Mouse stroke replay loop] (hooks into the loop iterator)
```

### Dependency Notes

- **Contour pipeline is strictly sequential:** Each stage consumes the output of the previous. The entire chain must be implemented before any painting can occur.
- **Preview window gates painting:** The OpenCV window is a hard gate — user must explicitly confirm (keypress) before the mouse replay loop starts. This prevents accidental painting.
- **Calibration gates normalization:** Without the two-point bbox, there is no coordinate mapping. Calibration must run before painting, not after.
- **Esc abort requires threading:** The keyboard listener must run on a separate thread; blocking on the paint loop makes abort impossible without OS signals.
- **Contour start-point optimization only useful with ordering:** If contours are drawn in arbitrary order, optimizing which end of each contour to start from provides marginal benefit. It compounds the proximity-ordering improvement.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept end-to-end.

- [ ] PNG loading + grayscale conversion — entry point
- [ ] Canny edge detection with configurable `threshold1`, `threshold2`, `blur_kernel_size` — core vision
- [ ] Contour extraction via OpenCV — converts edges to polylines
- [ ] Minimum contour length filter — removes noise contours
- [ ] Douglas-Peucker point simplification — reduces redundant points
- [ ] OpenCV preview window (proceed/abort gate) — user confirms quality before committing
- [ ] Two-point terminal-guided screen calibration with confirmation — defines canvas bbox
- [ ] Coordinate normalization + canvas mapping (with aspect-ratio preservation) — bridges image to screen
- [ ] Configurable countdown delay before first stroke — time to focus target window
- [ ] Mouse stroke replay loop (mouseDown + moveTo points + mouseUp) with configurable inter-point delay — core output
- [ ] Esc abort hotkey via background keyboard thread — safety
- [ ] YAML config file with all parameters + annotated sample config — usability
- [ ] Progress output (stroke N/M) during painting — feedback during long sessions

### Add After Validation (v1.x)

Features to add once core painting works correctly.

- [ ] Contour ordering by spatial proximity (nearest-neighbor) — add when inter-stroke travel is observed to cause visible artifacts or slow sessions; measurable improvement
- [ ] Contour start-point optimization — pairs with ordering; trivial to add alongside it
- [ ] Contour count + estimated time display in preview — add when users report uncertainty about session length
- [ ] Multiple named config profiles (`--profile`) — add when users accumulate multiple tested configs for different image types

### Future Consideration (v2+)

Features to defer until the tool is proven useful.

- [ ] Adaptive / auto Canny threshold (Otsu-based) — useful but adds complexity; users can tune manually first
- [ ] Contour hierarchy traversal (parent-child relationships for nested shapes) — only valuable for complex drawings with nested regions; line art rarely needs this
- [ ] Batch mode (process multiple images sequentially) — defer until single-image workflow is validated

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Canny edge detection (configurable) | HIGH | LOW | P1 |
| Contour extraction + min-length filter | HIGH | LOW | P1 |
| Douglas-Peucker point simplification | HIGH | LOW | P1 |
| OpenCV preview window (proceed/abort) | HIGH | MEDIUM | P1 |
| Two-point screen calibration | HIGH | MEDIUM | P1 |
| Mouse stroke replay with configurable delay | HIGH | LOW | P1 |
| Esc abort hotkey (threaded) | HIGH | MEDIUM | P1 |
| YAML config + sample file | HIGH | LOW | P1 |
| Aspect-ratio-preserving canvas mapping | MEDIUM | LOW | P1 |
| Countdown delay before painting | MEDIUM | LOW | P1 |
| Progress reporting (stroke N/M) | MEDIUM | LOW | P1 |
| Contour ordering by proximity | HIGH | MEDIUM | P2 |
| Contour start-point optimization | MEDIUM | LOW | P2 |
| Estimated time display in preview | LOW | LOW | P2 |
| Named config profiles (`--profile`) | LOW | LOW | P2 |
| Auto Canny threshold (Otsu) | MEDIUM | MEDIUM | P3 |
| Batch mode | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | dmcbx/AUTO-DRAW-BOT | PIPIKAI/auto-painter-win | auto-draw/autodraw | STS2 Map Painter (this project) |
|---------|---------------------|--------------------------|--------------------|---------------------------------|
| Drawing modes | Full, Contour, Color-aware | Pencil/Pen/Ink/Comic/Contour | Single cursor mode | Contour only (line art focus) |
| Abort mechanism | Esc key | Esc key (configurable hotkey) | Not documented | Esc key (background thread) |
| Canvas calibration | Canvas area selection | F7/F8 hotkeys for corners | Not documented | Two-point terminal-guided click |
| Preview before painting | Not documented | Original vs sketch comparison | Not documented | OpenCV contour preview window |
| Config format | Hardcoded constants in script | GUI sliders | Settings panel (GUI) | YAML file with annotated defaults |
| Point simplification | Not documented | Not documented | Not documented | Douglas-Peucker (explicit) |
| Contour ordering | Not documented | Not documented | Not documented | Proximity nearest-neighbor (v1.x) |
| Platform | Not documented | Windows (Win32 APIs) | Windows only | Linux-first (X11/Wayland) |
| Single-file | No (PyQt5 GUI) | No (PyQt5 GUI) | No (.NET) | Yes (explicit constraint) |
| Color/fill support | Yes | Yes | Yes | No (deliberate — line art only) |

**Key differentiator for this project:** The only tool in this comparison that is single-file, Linux-native, terminal-only, and focused purely on contour fidelity for line art. Competitors with GUI frameworks gain interactive parameter tuning at the cost of deployment complexity; this tool trades that for simplicity and scriptability.

## Sources

- [GitHub: auto-draw/autodraw](https://github.com/auto-draw/autodraw) — UI-based cursor drawing tool
- [GitHub: dmcbx/AUTO-DRAW-BOT](https://github.com/dmcbx/AUTO-DRAW-BOT) — contour + color mode drawing bot
- [GitHub: PIPIKAI/auto-painter-win](https://github.com/PIPIKAI/auto-painter-win) — multi-style auto painter with GUI
- [GitHub: FireyPixels/picatrix](https://github.com/FireyPixels/picatrix) — Drawasaurus bot with RDP simplification and nearest-neighbor path ordering
- [PyAutoGUI Safety Features (DeepWiki)](https://deepwiki.com/asweigart/pyautogui/4-safety-features) — FAILSAFE corner mechanism documentation
- [OpenCV Canny Edge Detector](https://docs.opencv.org/3.4/da/d5c/tutorial_canny_detector.html) — threshold parameter guidance
- [OpenCV Contour Sorting (cvexplained)](https://cvexplained.wordpress.com/2020/06/06/sorting-contours/) — contour ordering strategies
- [Ramer-Douglas-Peucker Algorithm (Wikipedia)](https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm) — point simplification algorithm
- [Optimal Path Planning for Pen Plotters (EngineerDog)](https://engineerdog.com/2021/08/18/optimal-path-planning-and-hatch-filling-for-pen-plotters/) — pen-lift minimization and nearest-neighbor TSP strategies

---
*Feature research for: image-to-mouse-stroke automation (STS2 Map Painter)*
*Researched: 2026-03-19*
