# Pitfalls Research

**Domain:** Image-to-mouse-stroke automation (auto-drawing / contour replay tools)
**Researched:** 2026-03-19
**Confidence:** HIGH (most pitfalls verified against official documentation and multiple sources)

---

## Critical Pitfalls

### Pitfall 1: Wayland Breaks pyautogui Entirely

**What goes wrong:**
pyautogui uses Xlib under the hood on Linux. On a native Wayland session, `moveTo()`, `mouseDown()`, and `mouseUp()` silently fail or do nothing. The cursor does not move. The tool appears to run with no error but paints nothing.

**Why it happens:**
pyautogui has no native Wayland backend. It relies on the X11 RECORD and XTEST extensions, which are only available to the X server. On Wayland, XWayland provides partial compatibility but only for X11 windows — native Wayland apps (including many modern game launchers) receive no synthetic input events.

**How to avoid:**
- At startup, detect the session type via `os.environ.get("XDG_SESSION_TYPE")` and `os.environ.get("WAYLAND_DISPLAY")`.
- If Wayland is detected, print an explicit, actionable error: "pyautogui requires an X11 session. Run with `DISPLAY=:0` or switch your session to X11 at login."
- Document the requirement prominently in the README. The user's stated platform is Linux (X11/Wayland) — this must be tested on their actual session.
- Do not silently continue; a no-op run that paints nothing and exits cleanly is worse than a crash.

**Warning signs:**
- Mouse position reported by `pyautogui.position()` never changes after `moveTo()` calls.
- `WAYLAND_DISPLAY` is set in the environment and `XDG_SESSION_TYPE` is `wayland`.
- No errors raised but the drawing canvas remains blank.

**Phase to address:** Phase 1 (core infrastructure / environment setup). Must be the first thing validated before any other work.

---

### Pitfall 2: pynput Hotkey Listener Fails Silently on Wayland / Captures Only XWayland Events

**What goes wrong:**
The Esc hotkey abort listener (implemented via pynput) stops working the moment focus shifts to a native Wayland window. The listener only captures keypresses routed through XWayland. If the target application (e.g., Satisfactory running under Steam/Proton with a native Wayland surface) has focus, Esc keypresses bypass X11 entirely. The abort mechanism becomes inert mid-paint.

**Why it happens:**
pynput's keyboard listener uses the X11 RECORD extension to intercept events. The RECORD extension only sees input destined for X11 clients. Native Wayland clients receive input through a separate protocol path that bypasses X11 completely.

**How to avoid:**
- Run pynput listener in a daemon thread so it does not block the main loop.
- Add a secondary abort mechanism that does not depend on pynput: check `pyautogui.position()` against a user-defined "abort corner" coordinate, or poll a `threading.Event` flag set by pyautogui's built-in FAILSAFE corner detection.
- Keep `pyautogui.FAILSAFE = True` (the default) as a last-resort abort. Document that moving the mouse to the top-left screen corner will halt the script via `FailSafeException`.
- Never raise exceptions inside pynput callbacks — callback exceptions silently stop the listener thread without propagating to the main thread.

**Warning signs:**
- Esc key pressed during painting does not abort — script continues to completion.
- Listener thread dies without error log when focus shifts to game window.

**Phase to address:** Phase 1 (core infrastructure). Must be wired up before the painting loop, not as an afterthought.

---

### Pitfall 3: Contour Ordering Causes Excessive Pen-Up Travel (Jump Artifacts)

**What goes wrong:**
`cv2.findContours()` returns contours in no guaranteed spatial order — typically in a scan-line detection order based on pixel position in the binary image. Replaying contours in raw detection order causes the "pen" to jump erratically across the canvas between strokes, producing long visible drag lines if mouseUp/mouseDown sequencing is wrong, and wasting significant time on empty travel.

**Why it happens:**
findContours is an image-processing algorithm, not a path planner. It has no awareness of minimizing travel distance between contours. Developers assume the returned list is spatially coherent when it is not.

**How to avoid:**
- After extracting all contours, sort them using a nearest-neighbor greedy traversal: for each contour, track its start and end point, and pick the next contour whose endpoint (or startpoint) is closest to the current cursor position. This is a simple O(n²) pass and is fast enough for typical contour counts (< 5,000).
- Alternatively, sort contours by the centroid of their bounding rect as a cheaper approximation that avoids the O(n²) cost.
- Move between contours with `pyautogui.moveTo()` (no button held), not `dragTo()`, to avoid accidental paint marks during travel.
- Verify: in the OpenCV preview window, draw contours in the order they will be replayed using color gradient (blue → red) so jump severity is visually apparent before committing.

**Warning signs:**
- Preview window shows contours distributed across the image but they render in a seemingly random walk.
- Long straight drag lines appear on the drawing canvas connecting unrelated regions.
- Painting time is dominated by travel rather than actual strokes.

**Phase to address:** Phase 2 (contour extraction and ordering). This is a core algorithmic concern, not a polish item.

---

### Pitfall 4: Coordinate Mapping Introduces Systematic Offset Due to Y-Axis Flip

**What goes wrong:**
Image coordinates have (0,0) at the top-left with Y increasing downward. Screen coordinates also have (0,0) at top-left with Y increasing downward. These match — but the bounding box capture step introduces a subtle error: if the user clicks the reference points imprecisely, or if the normalization formula has an off-by-one, all strokes are shifted uniformly by a fixed pixel offset. The drawing appears structurally correct but misregistered by several pixels.

A worse variant: if the developer accidentally maps image rows to Y and image columns to X but transposes them at any point (e.g., using `contour[i][0]` as `[x, y]` when OpenCV returns `[col, row]` which is `[x, y]` — this is correct, but confusion with numpy's `[row, col]` indexing causes transposition bugs).

**Why it happens:**
- OpenCV contour points are stored as `[x, y]` (column, row) — consistent with screen coordinates.
- numpy array indexing is `[row, col]` — the opposite convention.
- Mixing these two conventions when normalizing (`point[0] / img_width` vs `point[1] / img_width`) transposes the entire drawing.

**How to avoid:**
- Normalize explicitly: `norm_x = point[0][0] / img_width`, `norm_y = point[0][1] / img_height`. Always use named variables, never index-chained expressions.
- Verify mapping with a known test: use a single diagonal line from image top-left to image bottom-right. After mapping, it should appear as a diagonal from bounding box top-left to bottom-right on screen. If it is vertical, horizontal, or mirrored, the axes are swapped.
- For the bounding box capture, confirm coordinates are stored as `(top_left_x, top_left_y, bottom_right_x, bottom_right_y)` and that the screen mapping is `screen_x = top_left_x + norm_x * (bottom_right_x - top_left_x)`.

**Warning signs:**
- Drawing appears rotated 90 degrees on canvas.
- Drawing appears as a mirror image (horizontally or vertically flipped).
- Drawing is consistently shifted by a fixed pixel amount regardless of image content.

**Phase to address:** Phase 2 (coordinate mapping). Validate with a geometric test pattern before any real artwork.

---

### Pitfall 5: pyautogui Timing: PAUSE Default Is Too Slow for Smooth Strokes

**What goes wrong:**
`pyautogui.PAUSE` defaults to 0.1 seconds — inserted after every pyautogui call. For a contour with 200 points, this adds 20 seconds of dead time per contour, making a multi-contour drawing take hours instead of minutes. Developers do not realize PAUSE applies to every call including intermediate `moveTo()` calls inside a drag sequence.

**Why it happens:**
The PAUSE default exists for interactive scripts where human-readable pacing helps. It is inappropriate for tight drawing loops. Documentation mentions it but it is easy to miss.

**How to avoid:**
- Set `pyautogui.PAUSE = 0` at script startup. Use explicit `time.sleep()` only where intentional delay is needed (e.g., between contours, after mouseDown before first move).
- Between contours: a small inter-stroke delay (0.05–0.1s) lets the target application register the mouseUp event before the next mouseDown.
- Within a contour (moveTo calls): no delay is needed for most drawing applications — they process mouse events from the OS event queue regardless of speed.
- Make inter-stroke and intra-stroke delays configurable in the YAML config so users can tune for their application's responsiveness.

**Warning signs:**
- Script with 10 contours takes 10+ minutes when it should take 30 seconds.
- CPU is idle during painting (indicates sleep/pause dominates).
- Profiling shows most time inside `pyautogui._pause()`.

**Phase to address:** Phase 2 (painting loop implementation). Set PAUSE=0 from the start, not as a later optimization.

---

### Pitfall 6: Edge Detection Produces Unusable Contour Counts Without Filtering

**What goes wrong:**
Running `cv2.Canny()` on a real-world photograph (as opposed to clean line art) with default or aggressive low-threshold settings produces thousands of tiny contour fragments from texture, noise, JPEG compression artifacts, and gradients. Replaying 8,000 two-point contours produces a speckled mess and takes an unreasonable amount of time. Running with thresholds too conservative produces zero contours from a logo with thin strokes.

**Why it happens:**
Canny threshold selection is highly image-dependent. There is no universal "good" value. Developers set thresholds once on a test image and ship them as defaults that fail on other inputs.

**How to avoid:**
- Apply a Gaussian blur before Canny (`cv2.GaussianBlur(img, (5, 5), 0)`) — this is the standard preprocessing step documented in OpenCV tutorials and eliminates high-frequency noise.
- Expose both Canny thresholds as YAML config parameters (`canny_low`, `canny_high`).
- After findContours, apply a minimum arc length filter: discard any contour with `cv2.arcLength(c, False) < min_contour_px` where `min_contour_px` is configurable (default: 10 pixels in image space).
- In the preview window, display the contour count prominently so the user knows what they are about to replay.
- Document recommended threshold ranges for clean line art vs. photographs.

**Warning signs:**
- Preview shows thousands of tiny dots scattered across the image.
- Contour count exceeds 1,000 for a simple logo image.
- Painting produces a stippled noise texture rather than recognizable line art.

**Phase to address:** Phase 1 (image processing pipeline). Filtering must be in place before the preview step.

---

### Pitfall 7: Douglas-Peucker Epsilon Destroys Stroke Quality at High Values

**What goes wrong:**
Point simplification with an epsilon that is too large removes the points that define corners and direction changes. Straight lines appear where curves should be. Circular arcs become pentagons. The drawing looks like a crude vector approximation. At epsilon = 0 (disabled simplification), dense raw contours with 1-pixel step intervals create unreasonably slow painting and may cause application-side event queue overflow.

**Why it happens:**
Developers treat epsilon as a performance knob only ("higher = faster") without understanding it also degrades visual quality. The optimal value is image-resolution-dependent and must be proportional to the image's feature scale.

**How to avoid:**
- Default epsilon to `1.5` (in image pixels) — this removes sub-pixel jitter while preserving corners.
- Express epsilon as a percentage of the image diagonal (e.g., `epsilon_pct = 0.001`) so it scales with image resolution rather than requiring manual tuning per image.
- Always preview after simplification — the OpenCV preview window should show the simplified contours, not the raw Canny output, so the user sees exactly what will be painted.
- Cap maximum simplification: do not allow epsilon values that reduce a contour to fewer than 3 points (a triangle), as this typically indicates severe over-simplification.

**Warning signs:**
- Circles rendered as obvious polygons with 4–8 sides.
- Text contours lose legibility.
- Contour point counts collapse to near-zero for all shapes.

**Phase to address:** Phase 2 (contour simplification). Validate visually before finalizing defaults.

---

### Pitfall 8: Thread Safety — Esc Abort Flag Must Cross Thread Boundary Safely

**What goes wrong:**
The pynput listener runs in a daemon thread. The painting loop runs in the main thread. Naive implementations use a plain `global abort_flag = False` that the listener sets to `True`. This is technically a data race — Python's GIL makes it safe for simple boolean assignment in CPython, but the pattern is fragile if the code is ever extended (e.g., adding a queue or additional state). More commonly, developers check `abort_flag` only between contours, not within a contour's moveTo loop, causing a 30-second wait before the abort takes effect.

**Why it happens:**
Abort logic is added as an afterthought. The `time.sleep()` or PAUSE within the contour loop is not interrupted by flag checks.

**How to avoid:**
- Use `threading.Event` instead of a plain bool: `abort_event = threading.Event()`. The listener calls `abort_event.set()`. The painting loop checks `abort_event.is_set()` between every `moveTo()` call inside a contour.
- On abort detection within a stroke, call `pyautogui.mouseUp()` immediately before exiting to avoid a stuck mouse button.
- After abort, print confirmation to terminal: "Aborted after N contours. Mouse released."
- The `threading.Event` approach is documented in pynput's own guidance for dispatching events from callback threads to a queue.

**Warning signs:**
- Pressing Esc does not stop painting until the current contour finishes (may be 10–30 seconds for complex shapes).
- Mouse button remains held down after script exits mid-stroke.
- KeyboardInterrupt from terminal (Ctrl+C) does not release the mouse button.

**Phase to address:** Phase 1 (abort/safety infrastructure). Wire this up before the painting loop exists.

---

### Pitfall 9: pyautogui FAILSAFE Triggers Unexpectedly at Corner Coordinates

**What goes wrong:**
`pyautogui.FAILSAFE = True` (the default) raises `FailSafeException` if the mouse reaches any corner of the primary monitor. If the bounding box the user defines includes a screen corner, or if the coordinate mapping has a small error that overshoots to `(0, 0)`, the entire script crashes mid-paint without releasing the mouse button, leaving it held down.

**Why it happens:**
The FAILSAFE corner detection is a hard-coded check in pyautogui against the four screen corners. Developers do not account for this when the drawing canvas is near a screen edge.

**How to avoid:**
- Wrap the entire painting loop in a `try/except pyautogui.FailSafeException` block that calls `pyautogui.mouseUp()` in the `except` clause before re-raising or exiting cleanly.
- Clamp all computed screen coordinates to `[1, screen_width - 1]` and `[1, screen_height - 1]` before passing to moveTo. This prevents any off-by-one from reaching the literal corner pixels.
- Keep FAILSAFE enabled — it is the user's manual emergency stop and should not be disabled.

**Warning signs:**
- Script crashes with `FailSafeException` when painting near screen edges.
- Mouse button remains held after crash.

**Phase to address:** Phase 2 (painting loop). Add the try/except guard during initial implementation.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode Canny thresholds (e.g., 100/200) | No config needed | Fails silently on different input images; user must edit source code | Never — expose as YAML config from the start |
| Skip contour ordering (replay in findContours order) | Simpler code | Obvious jump artifacts; users file bugs | Never — the nearest-neighbor sort is 20 lines |
| Use `pyautogui.drag()` instead of `mouseDown` + `moveTo` loop | Simpler API | No abort-checking opportunity mid-stroke; all-or-nothing per contour | Never for this tool — the moveTo loop is required for abort support |
| Set `pyautogui.FAILSAFE = False` | Eliminates spurious crashes near screen corners | No emergency stop; runaway automation is unrecoverable without physical intervention | Never |
| Plain `global abort_flag` bool instead of `threading.Event` | Less code | Race conditions if code grows; abort only checked between contours | Acceptable in MVP if abort is checked every moveTo call |
| Skip minimum contour length filter | Less config surface | Thousands of noise contours crash painting performance on photographs | Never — always filter, even with a generous default |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| pyautogui on Linux | Assume it works on any Linux desktop | Detect `XDG_SESSION_TYPE` at startup; fail fast with actionable error on Wayland |
| pyautogui + pynput | Import both without checking for X11 RECORD extension availability | Both require X11; if X11 is unavailable both will fail — check once at startup |
| OpenCV preview window | Call `cv2.waitKey(0)` in a thread other than main | OpenCV GUI functions must be called from the main thread on Linux; do preview before spawning any threads |
| pynput listener + pyautogui | Call `pyautogui.moveTo()` from within a pynput callback | pynput callbacks are on a listener thread; pyautogui is not thread-safe for input simulation; use an Event to signal the main thread instead |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `pyautogui.PAUSE = 0.1` (default) inside moveTo loop | 200-point contour takes 20 seconds instead of 1 second | Set `PAUSE = 0` at startup; use explicit sleeps only between contours | Breaks immediately — even a 10-contour image takes 10+ minutes |
| No point simplification — raw Canny points (1px steps) | 50,000 moveTo calls for a single contour; application event queue backs up | Apply Douglas-Peucker before replay; default epsilon ~1.5px | Breaks on any contour longer than ~200 pixels in image space |
| Contours stored as Python lists of lists | Slow iteration for large contour sets; extra memory pressure | Contours from findContours are already numpy arrays; do not convert to pure Python lists | Noticeable at > 500 contours with > 100 points each |
| Re-running findContours every time config changes | Slow feedback loop during tuning | Cache the contour result; only re-detect when image path or Canny params change | Breaks iteration speed during config tuning |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No contour count shown before painting | User commits to a 2-hour run with 5,000 noise contours from a photo | Preview window title or terminal output: "Found 847 contours. Press any key to paint, Q to abort." |
| No elapsed time / progress during painting | User cannot estimate completion; no feedback for 30 minutes | Print `Contour N/total` to terminal every N contours during replay |
| Bounding box capture with no confirmation | Misclicked reference point causes entire drawing to be wrong region | Show captured coordinates and ask "Correct? [y/N]" before proceeding |
| Esc abort with no mouse release confirmation | User unsure if mouse button is held after abort | Always print "Painting aborted. Mouse released." after abort handling |
| Config file errors (YAML typo) silently using defaults | User changes `canny_low` to `cany_low`; tool ignores it and uses hardcoded default | Validate all config keys against a known schema at startup; warn on unknown keys |

---

## "Looks Done But Isn't" Checklist

- [ ] **Wayland detection:** Tool starts without error on Wayland but `pyautogui.moveTo()` does nothing — verify `XDG_SESSION_TYPE` check is present and aborts early.
- [ ] **Mouse release on abort:** Press Esc mid-stroke. Verify left mouse button is not held down after script exits (check with `xdotool getactivewindow` or observe cursor).
- [ ] **Contour ordering:** Run on a multi-contour test image and watch for long travel strokes between unrelated regions — not visible in the preview, only during replay.
- [ ] **Coordinate mapping:** Paint a simple diagonal test image. Verify diagonal appears on canvas with correct orientation (not rotated/mirrored).
- [ ] **PAUSE=0 set:** Verify painting a 100-point contour completes in under 1 second, not 10 seconds.
- [ ] **Minimum contour filter active:** Feed a JPEG photograph. Verify contour count in preview is < 500 with default config, not 10,000+.
- [ ] **FailSafeException handled:** Move mouse to top-left corner during painting. Verify script exits cleanly with mouse released, not stuck.
- [ ] **OpenCV preview on main thread:** Preview window renders and responds to keypresses — not frozen or black (indicates it was created on a non-main thread).

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Wayland + pyautogui incompatibility discovered after build | LOW | Add session-type check at startup; document X11 requirement; user logs out and selects X11 session at login screen |
| Contour ordering causing jump artifacts | LOW | Add nearest-neighbor sort after findContours; re-test with preview |
| Coordinate mapping producing mirrored drawing | LOW | Add a diagonal test case; fix axis transposition in normalization formula |
| PAUSE not set to 0 — tool is too slow | LOW | Add `pyautogui.PAUSE = 0` at top of main; immediate fix |
| pynput listener dying silently on focus switch | MEDIUM | Add FAILSAFE corner as secondary abort; document limitation; test on actual game window |
| Mouse button stuck after crash mid-stroke | LOW | User presses physical mouse button once to toggle state; or run `xdotool mouseup 1` |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Wayland / pyautogui incompatibility | Phase 1 — environment bootstrap | Check `XDG_SESSION_TYPE`; run `pyautogui.position()` before and after `moveTo(1, 1)`; verify cursor moved |
| pynput listener Wayland failure | Phase 1 — abort infrastructure | Press Esc during a test painting loop; verify abort triggers within 1 moveTo cycle |
| Thread safety — abort flag | Phase 1 — abort infrastructure | Use `threading.Event`; verify abort checked inside per-contour moveTo loop |
| Mouse release on abort/crash | Phase 1 — abort infrastructure | Intentionally raise exception mid-stroke; verify mouse is up afterward |
| Contour ordering jumps | Phase 2 — contour extraction and ordering | Paint a 5-contour test image; verify no visible travel lines between strokes |
| Coordinate mapping transposition | Phase 2 — coordinate mapping | Paint a diagonal line image; verify correct orientation on canvas |
| pyautogui PAUSE too slow | Phase 2 — painting loop | Time a 100-point contour; must complete < 2 seconds |
| Edge detection too many/few contours | Phase 1 — image processing pipeline | Feed clean logo and a JPEG photo; verify contour counts are reasonable with defaults |
| Douglas-Peucker over-aggressive | Phase 2 — point simplification | Compare preview before/after simplification on a circular shape; verify no jagged artifacts |
| FAILSAFE corner trigger | Phase 2 — painting loop | Move to top-left corner mid-paint; verify clean exit with mouse released |

---

## Sources

- pyautogui Wayland issues (multiple open GitHub issues, confirmed unfixed as of 2025): https://github.com/asweigart/pyautogui/issues/695, https://github.com/asweigart/pyautogui/issues/881, https://github.com/asweigart/pyautogui/issues/909
- pynput Wayland keyboard listener failures: https://github.com/moses-palmer/pynput/issues/628, https://github.com/moses-palmer/pynput/issues/331
- pynput platform limitations (official docs): https://pynput.readthedocs.io/en/latest/limitations.html
- pynput thread safety and callback guidance: https://pynput.readthedocs.io/en/latest/keyboard.html
- pyautogui FAILSAFE documentation: https://pyautogui.readthedocs.io/en/latest/index.html
- pyautogui mouse control and PAUSE: https://pyautogui.readthedocs.io/en/latest/mouse.html
- OpenCV Canny edge detection and Gaussian preprocessing: https://docs.opencv.org/4.x/da/d22/tutorial_py_canny.html
- OpenCV findContours hierarchy and retrieval modes: https://docs.opencv.org/4.x/d9/d8b/tutorial_py_contours_hierarchy.html
- OpenCV contour ordering (unordered by default): https://answers.opencv.org/question/39113/contours-sorting/
- Douglas-Peucker visual quality degradation: https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm
- TSP-based drawing path optimization (nearest neighbor): https://arxiv.org/abs/2210.07592
- DrawingBot V3 path-finding module documentation: https://docs.drawingbotv3.com/en/latest/pfms.html
- Automatic Canny threshold selection: https://pyimagesearch.com/2015/04/06/zero-parameter-automatic-canny-edge-detection-with-python-and-opencv/

---
*Pitfalls research for: image-to-mouse-stroke automation (STS2 Map Painter)*
*Researched: 2026-03-19*
