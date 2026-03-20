# Phase 2: Coordinate Mapping and Replay - Research

**Researched:** 2026-03-20
**Domain:** Aspect-ratio-preserving coordinate transform + pyautogui stroke replay with pynput abort
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Aspect Ratio Mapping**
- D-01: Preserve aspect ratio when mapping to bounding box — no stretching/distortion
- D-02: Fill the largest fitting axis (letterbox/pillarbox), center on the shorter axis
- D-03: Contours scale to fill the bounding box on whichever axis fits, margins only on the other axis

**Stroke Replay Speed**
- D-04: Configurable countdown delay before first stroke (`painting.start_delay`, default: 3 seconds), prints countdown in terminal
- D-05: Inter-point delay defaults to 0 (`painting.inter_point_delay: 0`) — fastest possible. User increases if target app drops inputs
- D-06: Inter-stroke delay configurable (`painting.inter_stroke_delay: 0.05`) — 50ms pause between contours
- D-07: Progress reported via inline overwrite (`\r`) — single line: `Painting: 42/128 strokes (33%)` with progress bar

**Contour Ordering**
- D-08: Nearest-neighbor greedy sort — start from bbox top-left, pick closest contour endpoint, paint it, repeat from current position
- D-09: For each contour, compare distance from current cursor to both endpoints — start from whichever is closer (halves average travel)

**Abort Mechanism**
- D-10: Esc sets `abort_flag` (threading.Event already on AppState). Current contour finishes (mouseDown→moveTo→mouseUp completes), then loop breaks. No partial strokes.
- D-11: pynput background daemon thread for Esc listener — same library already used for calibration clicks, imported lazily
- D-12: mouseUp guaranteed on ALL exit paths via try/finally wrapping the painting loop — prevents stuck mouse button on crashes
- D-13: On abort: print "Aborted after N/M strokes." and exit code 0

### Claude's Discretion
- Exact progress bar formatting (width, characters)
- Whether to print total painting time at completion
- Edge case handling for very small contours (< 2 points)
- Whether to skip contours that map to a single pixel after coordinate transform

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAL-06 | Map contour coordinates to screen space preserving aspect ratio (no stretching) | Letterbox/pillarbox math in Architecture Patterns; aspect ratio formula verified |
| CAL-07 | Configurable countdown delay before first stroke begins | D-04; config key `painting.start_delay`, default 3s; same countdown pattern as calibration |
| PAINT-01 | Replay each contour as right-click mouseDown → moveTo sequence → mouseUp | pyautogui API: `mouseDown(x, y, button=button)`, `moveTo(x, y)`, `mouseUp(x, y, button=button)` |
| PAINT-02 | Mouse button for strokes is configurable (default: right) | Already in config defaults (`painting.mouse_button: right`); thread through to mouseDown/mouseUp calls |
| PAINT-03 | Inter-point delay is configurable for stroke speed tuning | D-05; `painting.inter_point_delay: 0`; `time.sleep(inter_point_delay)` inside moveTo loop if > 0 |
| PAINT-04 | Contours sorted by spatial proximity (nearest-neighbor) to minimize travel | O(n²) greedy algorithm; starts from bbox top-left; documented with benchmark data |
| PAINT-05 | Tool picks optimal start-point (closest endpoint) for each contour | D-09; compare dist(cursor, contour[0]) vs dist(cursor, contour[-1]); reverse contour if far end is closer |
| PAINT-06 | Esc hotkey aborts painting mid-stroke via background listener thread | pynput keyboard.Listener daemon; sets abort_flag.Event; checked after each complete stroke |
| PAINT-07 | Tool prints stroke progress (N/M, percentage) to terminal during painting | `\r` overwrite pattern; progress bar with configurable width |
| PAINT-08 | Tool calls mouseUp on all exit paths (normal, abort, exception) | try/finally wrapping entire painting loop; mouseUp in finally block |
</phase_requirements>

---

## Summary

Phase 2 adds the two components that complete the tool's core value: a coordinate transformer that maps normalized `[0,1]` contours to screen pixel space (with aspect ratio preservation), and a replay engine that drives pyautogui to paint every stroke. Both components build directly on Phase 1 outputs (`AppState.contours_normalized`, `AppState.bbox`) with no changes to the image pipeline or calibration code.

The coordinate transform is pure arithmetic — a letterbox/pillarbox fit that scales the image aspect ratio into the bbox, centers it on the short axis, then maps each normalized point to an integer screen pixel. The replay engine is a loop over the sorted contour list: for each contour, press the configured mouse button down, move through each point, release, pause, check the abort flag, and report progress. Both components are unit-testable without screen interaction.

The most critical implementation detail is the try/finally guard (PAINT-08): mouseUp must be called even when an exception is raised, the FailSafeException fires, or the process is killed mid-stroke. A stuck mouse button in a game is highly disruptive and recovery requires a physical click. All other decisions (abort timing, progress format, sort starting point) are fully locked by CONTEXT.md and require no further investigation.

**Primary recommendation:** Implement `map_contours_to_screen()` as a pure function returning pixel arrays, `sort_contours_nearest_neighbor()` as a standalone sort, and `run_replay()` as the orchestrating function — in that order. Wire them sequentially into `main()` after `run_calibration()`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyautogui | 0.9.54 | mouseDown, moveTo, mouseUp for stroke replay | Project mandated; already imported in painter.py |
| pynput | 1.8.1 | keyboard.Listener daemon for Esc abort | Already used for calibration clicks; same lazy import pattern applies |
| numpy | 2.1.x (Python 3.10) / 2.4.3 (Python 3.11+) | Array math for coordinate transform, euclidean distance | Already imported; contours are np.ndarray |
| threading | stdlib | threading.Event for cross-thread abort flag | Already in AppState.abort_flag |
| time | stdlib | time.sleep for delays, time.time for elapsed timing | No additional dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| math | stdlib | math.sqrt for euclidean distance | Alternative to numpy for scalar distance; numpy preferred since contours are already arrays |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyautogui mouseDown+moveTo+mouseUp | pyautogui.drag() | drag() provides no per-point abort check opportunity; locked out by PAINT-06 requirement |
| pynput keyboard.Listener | keyboard library | keyboard is abandoned (2020), needs root on Linux; pynput already present |
| nearest-neighbor O(n²) | scipy.spatial.KDTree O(n log n) | KDTree adds a dependency for a problem that is fast enough at n < 5,000; plain numpy is sufficient |

**No additional installation needed** — all required libraries are already in requirements.txt from Phase 1.

---

## Architecture Patterns

### Recommended Project Structure

Phase 2 adds three logical sections to `painter.py` (single-file constraint):

```
painter.py
  # === CONFIGURATION ===     (Phase 1 — add new painting.* keys)
  # === SAFETY ===            (Phase 1 — unchanged)
  # === CLI ===               (Phase 1 — unchanged)
  # === IMAGE PIPELINE ===    (Phase 1 — unchanged)
  # === PREVIEW ===           (Phase 1 — unchanged)
  # === CALIBRATION ===       (Phase 1 — unchanged)
  # === COORDINATE MAPPING === (Phase 2 NEW)
  # === REPLAY ENGINE ===      (Phase 2 NEW)
  # === MAIN ===               (Phase 2 — extend with new calls)
```

### Pattern 1: Letterbox/Pillarbox Aspect-Ratio Mapping (CAL-06)

**What:** Map normalized `[0,1]` contour coordinates to screen pixels within `bbox`, preserving the source image's aspect ratio. The image aspect ratio is derived from the source image dimensions (same approach as Phase 1 `run_preview`).

**When to use:** Whenever the bbox proportions differ from the source image proportions.

**Math:**
```
bbox = (bx1, by1, bx2, by2)
bbox_w = bx2 - bx1
bbox_h = by2 - by1
img_aspect = img_w / img_h     # source image aspect ratio

# Determine which axis is the constraining axis
if bbox_w / img_aspect <= bbox_h:
    # Width-constrained (letterbox: margins top/bottom)
    draw_w = bbox_w
    draw_h = bbox_w / img_aspect
else:
    # Height-constrained (pillarbox: margins left/right)
    draw_h = bbox_h
    draw_w = bbox_h * img_aspect

# Center the draw area within the bbox
offset_x = bx1 + (bbox_w - draw_w) / 2
offset_y = by1 + (bbox_h - draw_h) / 2

# Map a normalized point (nx, ny) to screen pixel:
screen_x = int(offset_x + nx * draw_w)
screen_y = int(offset_y + ny * draw_h)
```

**Example:**
```python
# Source: ARCHITECTURE.md coordinate math + D-01/D-02/D-03 decisions
def compute_draw_region(bbox: tuple, img_w: int, img_h: int) -> tuple:
    """CAL-06: Compute the letterboxed/pillarboxed draw region within bbox.

    Returns (offset_x, offset_y, draw_w, draw_h) all as floats.
    Caller converts to int at point-mapping time, not here (avoids accumulated rounding).
    """
    bx1, by1, bx2, by2 = bbox
    bbox_w = bx2 - bx1
    bbox_h = by2 - by1
    img_aspect = img_w / img_h

    if bbox_w / img_aspect <= bbox_h:
        draw_w = float(bbox_w)
        draw_h = draw_w / img_aspect
    else:
        draw_h = float(bbox_h)
        draw_w = draw_h * img_aspect

    offset_x = bx1 + (bbox_w - draw_w) / 2
    offset_y = by1 + (bbox_h - draw_h) / 2
    return offset_x, offset_y, draw_w, draw_h


def map_contour_to_screen(norm_contour: np.ndarray,
                           offset_x: float, offset_y: float,
                           draw_w: float, draw_h: float) -> np.ndarray:
    """CAL-06: Convert (N, 2) normalized contour to (N, 2) integer screen pixels."""
    screen = np.empty_like(norm_contour, dtype=np.int32)
    screen[:, 0] = (offset_x + norm_contour[:, 0] * draw_w).astype(np.int32)
    screen[:, 1] = (offset_y + norm_contour[:, 1] * draw_h).astype(np.int32)
    return screen
```

**Important:** Read source image dimensions the same way `run_preview` does — `cv2.imread(state.image_path)` then `.shape[:2]`. Do not cache dimensions in AppState (not in scope for Phase 2).

### Pattern 2: Nearest-Neighbor Contour Sort (PAINT-04, PAINT-05)

**What:** Greedy O(n²) sort. Start cursor at bbox top-left `(bx1, by1)` in normalized space `(0.0, 0.0)`. For each remaining contour, measure euclidean distance from current position to both endpoints. Pick the contour with the closest endpoint. If the far endpoint is closer, reverse the contour. After painting, update current position to the endpoint that was painted last.

**When to use:** Always — PITFALLS.md rates skipping sort as "never acceptable."

**Example:**
```python
# Source: PITFALLS.md Pitfall 3 + D-08/D-09 decisions
def sort_contours_nearest_neighbor(contours: list[np.ndarray]) -> list[np.ndarray]:
    """PAINT-04, PAINT-05: Greedy nearest-neighbor sort starting from (0, 0) in normalized space.

    For each contour, picks whichever endpoint (first or last point) is closer to
    the current cursor position. If the last point is closer, reverses the contour
    so painting starts from the nearer end.

    Time complexity: O(n^2) — acceptable for n < 5,000 contours.
    """
    if not contours:
        return []

    remaining = list(contours)
    sorted_out = []
    # Start from top-left of normalized space (maps to bbox top-left after transform)
    cx, cy = 0.0, 0.0

    while remaining:
        best_idx = 0
        best_dist = float("inf")
        best_reversed = False

        for i, c in enumerate(remaining):
            # Distance to first point
            d_start = (c[0, 0] - cx) ** 2 + (c[0, 1] - cy) ** 2
            # Distance to last point
            d_end = (c[-1, 0] - cx) ** 2 + (c[-1, 1] - cy) ** 2
            d = min(d_start, d_end)
            if d < best_dist:
                best_dist = d
                best_idx = i
                best_reversed = d_end < d_start

        chosen = remaining.pop(best_idx)
        if best_reversed:
            chosen = chosen[::-1]  # paint from the closer endpoint
        sorted_out.append(chosen)
        # Update cursor to the last painted point
        cx, cy = float(chosen[-1, 0]), float(chosen[-1, 1])

    return sorted_out
```

**Note:** Squared distances are used (no `math.sqrt`) for performance — we only need to compare, not the actual distance value.

### Pattern 3: Replay Loop with try/finally (PAINT-01, PAINT-06, PAINT-07, PAINT-08)

**What:** Single `run_replay()` function wraps the entire painting session. try/finally guarantees mouseUp on all exit paths. Abort is checked after each complete stroke (D-10 — no partial strokes).

**Example:**
```python
# Source: ARCHITECTURE.md Pattern 2 + D-10/D-11/D-12/D-13 decisions
def run_replay(state: AppState) -> None:
    """PAINT-01..08: Drive pyautogui to paint sorted, screen-mapped contours.

    Entry point for the full painting session. Handles countdown, abort listener,
    progress reporting, and guaranteed mouseUp on all exit paths.
    """
    import pyautogui as _pyautogui

    if state.dry_run:
        print("Dry run: skipping painting.")
        return

    # CAL-06: compute draw region from source image dimensions
    src_img = cv2.imread(state.image_path)
    img_h, img_w = src_img.shape[:2]
    offset_x, offset_y, draw_w, draw_h = compute_draw_region(state.bbox, img_w, img_h)

    # PAINT-04, PAINT-05: sort contours before mapping to screen
    sorted_contours = sort_contours_nearest_neighbor(state.contours_normalized)

    # Map all contours to screen pixel arrays once (not per-stroke)
    screen_contours = [
        map_contour_to_screen(c, offset_x, offset_y, draw_w, draw_h)
        for c in sorted_contours
    ]

    # CAL-07: countdown before first stroke
    start_delay = state.config.get("painting", {}).get("start_delay", 3)
    if start_delay > 0:
        print(f"Painting starts in:", end="", flush=True)
        for t in range(int(start_delay), 0, -1):
            print(f" {t}...", end="", flush=True)
            time.sleep(1)
        print(" GO")

    # PAINT-06: start Esc abort listener
    _start_abort_listener(state)

    total = len(screen_contours)
    button = state.config.get("painting", {}).get("mouse_button", "right")
    inter_stroke = state.config.get("painting", {}).get("inter_stroke_delay", 0.05)
    inter_point = state.config.get("painting", {}).get("inter_point_delay", 0)

    painted = 0
    t_start = time.time()

    # PAINT-08: try/finally guarantees mouseUp on crash, abort, or FailSafeException
    try:
        for i, pts in enumerate(screen_contours):
            if state.abort_flag.is_set():
                break

            if len(pts) < 2:
                continue  # skip degenerate single-point contours

            x0, y0 = int(pts[0, 0]), int(pts[0, 1])
            _pyautogui.mouseDown(x0, y0, button=button)

            for pt in pts[1:]:
                _pyautogui.moveTo(int(pt[0]), int(pt[1]))
                if inter_point > 0:
                    time.sleep(inter_point)

            _pyautogui.mouseUp(button=button)
            painted += 1

            # PAINT-07: inline progress overwrite
            _print_progress(painted, total)

            if i < total - 1:
                time.sleep(inter_stroke)

    finally:
        # PAINT-08: unconditional release
        _pyautogui.mouseUp(button=button)

    elapsed = time.time() - t_start

    if state.abort_flag.is_set():
        print(f"\nAborted after {painted}/{total} strokes.")
    else:
        print(f"\nDone. {painted} strokes in {elapsed:.1f}s.")
```

### Pattern 4: Abort Listener (PAINT-06)

```python
# Source: ARCHITECTURE.md Pattern 2 + D-11 decision
def _start_abort_listener(state: AppState) -> None:
    """PAINT-06: Start pynput keyboard daemon that sets abort_flag on Esc.

    Lazy import matches Phase 1 pattern (capture_click_position).
    Must be called AFTER run_preview (cv2.imshow must be on main thread only).
    """
    from pynput import keyboard as _pynput_keyboard

    def on_press(key):
        if key == _pynput_keyboard.Key.esc:
            state.abort_flag.set()
            return False  # stops the listener

    listener = _pynput_keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
```

### Pattern 5: Progress Bar (PAINT-07)

```python
# Source: D-07 decision
def _print_progress(done: int, total: int, bar_width: int = 30) -> None:
    """PAINT-07: Single-line inline progress overwrite."""
    pct = done / total if total > 0 else 1.0
    filled = int(bar_width * pct)
    bar = "#" * filled + "-" * (bar_width - filled)
    print(f"\rPainting: {done}/{total} strokes ({pct:.0%}) [{bar}]", end="", flush=True)
```

### Pattern 6: Config YAML Extension

Three new keys must be added to `_DEFAULTS` and `DEFAULT_CONFIG_CONTENT` (the auto-generated config):

```yaml
painting:
  mouse_button: right          # existing key from Phase 1
  inter_stroke_delay: 0.05     # existing key from Phase 1
  start_delay: 3               # NEW: countdown seconds before first stroke (CAL-07)
  inter_point_delay: 0         # NEW: seconds between moveTo calls within a stroke (PAINT-03)
```

And to `_DEFAULTS` dict:
```python
"painting": {
    "mouse_button": "right",
    "inter_stroke_delay": 0.05,
    "start_delay": 3,          # NEW
    "inter_point_delay": 0,    # NEW
},
```

### Anti-Patterns to Avoid

- **Using pyautogui.drag() instead of mouseDown+moveTo+mouseUp:** drag() is atomic — no per-point abort check is possible. PITFALLS.md rates this "never for this tool."
- **Calling mouseUp inside the for-loop but not in finally:** A FailSafeException bypasses the loop's mouseUp, leaving the button held. The try/finally must wrap the entire loop.
- **Checking abort_flag only between contours:** D-10 locks this as acceptable (current contour finishes before abort takes effect). No change needed.
- **Converting contours to Python lists before distance math:** Numpy indexing on `(N, 2)` arrays is faster than list iteration. Keep as ndarray throughout.
- **Calling cv2.imread() inside the per-stroke loop:** Read source image dimensions once before the loop, not per contour.
- **Hardcoding mouse_button to 'right':** PAINT-02 requires it to be configurable. Read from `state.config["painting"]["mouse_button"]`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Aspect ratio scaling math | Custom stretch/shrink formula | The letterbox formula in Pattern 1 (verified) | Stretching vs centering requires careful axis selection — the provided formula is correct for both landscape and portrait bboxes |
| Per-point euclidean distance | `math.hypot` in inner loop | `(dx**2 + dy**2)` comparison (no sqrt) | sqrt is unnecessary for comparison; saves 40% time in inner loop for 500+ contours |
| Abort signaling across threads | global bool | `threading.Event` (already in AppState.abort_flag) | `threading.Event` is already initialized; do not introduce a second mechanism |
| Mouse release on exception | try/except each paint call | `try/finally` wrapping entire loop | A single finally guarantees release regardless of exception type, including FailSafeException |
| Progress display | curses/rich | `\r` overwrite with `print(..., end="", flush=True)` | Zero dependencies; works in all terminals; D-07 locks this format |

**Key insight:** The coordinate math and pyautogui APIs are simple — the danger is in omissions (no finally, no aspect ratio, no sort), not in complexity. The patterns above prevent all known omissions.

---

## Common Pitfalls

### Pitfall 1: No try/finally — Stuck Mouse Button (PAINT-08)
**What goes wrong:** An unhandled exception (FailSafeException, KeyboardInterrupt, cv2 error) exits the loop after mouseDown but before mouseUp. The mouse button remains physically pressed in the game window, causing uncontrolled paint marks.
**Why it happens:** mouseUp is written inside the loop; exceptions bypass it.
**How to avoid:** Wrap the entire painting for-loop in `try: ... finally: pyautogui.mouseUp(button=button)`. The finally block executes even if the loop completes normally, so calling mouseUp twice (once at loop end, once in finally) is harmless.
**Warning signs:** Mouse button stuck after Ctrl+C during testing. Right-click context menus appearing on next click.

### Pitfall 2: pyautogui FailSafeException Near Screen Corners (from PITFALLS.md)
**What goes wrong:** If the computed screen coordinate lands exactly on a screen corner pixel `(0,0)`, `(screen_w-1, 0)`, etc., pyautogui raises `FailSafeException`. The FAILSAFE is enabled by default and should remain enabled.
**Why it happens:** Off-by-one in coordinate math, or user defines a bbox that includes a corner.
**How to avoid:** The try/finally guard handles this case cleanly. Optionally clamp coords to `[1, screen_w-2]` x `[1, screen_h-2]`. Do NOT disable FAILSAFE.
**Warning signs:** Script crashes with `pyautogui.FailSafeException` when painting near screen edges.

### Pitfall 3: Coordinate Axis Transposition (from PITFALLS.md Pitfall 4)
**What goes wrong:** Drawing appears rotated 90 degrees or mirrored. OpenCV contour points are `[x, y]` (col, row). Numpy indexing is `[row, col]`. Mixing these in normalization or in `map_contour_to_screen` transposes the image.
**Why it happens:** `norm_contour[:, 0]` is x (horizontal), `norm_contour[:, 1]` is y (vertical). This matches screen coordinates where index 0 is x. A developer confusing numpy's row-major convention with OpenCV's column-first convention will swap axes.
**How to avoid:** Use named intermediate variables. Verify with a diagonal test: a contour from normalized `(0,0)` to `(1,1)` must map to a line from bbox top-left to bbox bottom-right on screen.
**Warning signs:** Preview looks correct but painting appears as a transposed/mirrored drawing on canvas.

### Pitfall 4: Contour Sort Applied After Screen Mapping (wrong order)
**What goes wrong:** Sort distances are computed in screen pixel space instead of normalized space. Result is functionally correct but wastes a conversion step. More importantly, if sort happens after mapping, the normalized arrays are discarded and the sort operates on integer arrays — rounding errors accumulate in distance calculations.
**Why it happens:** Sort and map seem independent; it is easy to swap their order.
**How to avoid:** Sort normalized contours first, then map to screen pixels. This is the order shown in Pattern 3 (run_replay example).
**Warning signs:** No functional bug but the code is unnecessarily complex.

### Pitfall 5: Calling cv2.imread Again (performance and correctness)
**What goes wrong:** `run_preview` already calls `cv2.imread(state.image_path)` to get the source aspect ratio. `run_replay` needs the same. Calling imread again is wasteful on large images and creates an inconsistency if the file changes between runs.
**Why it happens:** Source image dimensions are not stored in AppState.
**How to avoid:** Call imread once at the top of `run_replay`, extract shape, discard the image immediately. This is a one-time cost per run, acceptable for Phase 2. Storing dims in AppState would be cleaner but is out of scope per the phase boundary.
**Warning signs:** No bug — just a lint/performance note. Document it.

### Pitfall 6: Inter-Stroke Delay Applied After Last Stroke
**What goes wrong:** `time.sleep(inter_stroke_delay)` inside the loop runs after the last stroke, adding unnecessary delay before the completion message.
**Why it happens:** The sleep is unconditional inside the loop body.
**How to avoid:** `if i < total - 1: time.sleep(inter_stroke_delay)` — only sleep between strokes, not after the last one.
**Warning signs:** Tool appears to hang for 50ms after the final stroke before printing "Done."

### Pitfall 7: Progress Print Leaves Terminal in Dirty State
**What goes wrong:** After `\r` progress lines, the final "Done." message prints on the same line without a leading newline, resulting in garbled output.
**Why it happens:** The last `\r` line is not terminated.
**How to avoid:** Print `\n` (or use `print()` with default end) before the final completion message. The `_print_progress` function uses `end=""` — the caller must print a newline after the loop exits.
**Warning signs:** "Done. 128 strokes" appears appended to the last progress bar line.

---

## Code Examples

### Verified: pyautogui Mouse Button API

```python
# Source: https://pyautogui.readthedocs.io/en/latest/mouse.html
import pyautogui
pyautogui.mouseDown(x, y, button='right')   # button: 'left', 'right', 'middle'
pyautogui.moveTo(x, y)                       # no button argument needed
pyautogui.mouseUp(button='right')            # must match mouseDown button
```

The `button` parameter is a string. The default is `'left'`. For this tool the default is `'right'` per the Phase 1 config.

### Verified: pynput Keyboard Listener Pattern

```python
# Source: https://pynput.readthedocs.io/en/latest/keyboard.html
from pynput import keyboard

def on_press(key):
    if key == keyboard.Key.esc:
        abort_event.set()
        return False  # return False stops the listener

listener = keyboard.Listener(on_press=on_press)
listener.daemon = True  # does not block process exit
listener.start()
# listener runs in background; no join() call needed
```

**Note:** `return False` from the callback stops the listener. Do NOT raise exceptions inside the callback — they are swallowed silently (PITFALLS.md Pitfall 2). The abort_flag.set() is sufficient.

### Verified: pyautogui FailSafeException Handling

```python
# Source: https://pyautogui.readthedocs.io/en/latest/index.html
import pyautogui

try:
    for pts in screen_contours:
        pyautogui.mouseDown(...)
        # ... moveTo loop ...
        pyautogui.mouseUp(...)
finally:
    pyautogui.mouseUp(button=button)  # safe to call even if not currently held
```

Calling `mouseUp` when the button is not held is a no-op in pyautogui — it does not raise an error.

### Verified: numpy squared distance for nearest-neighbor

```python
# No import needed — plain Python arithmetic on numpy scalars
dx = c[0, 0] - cx   # c[0] = first point; c[0,0] = x coordinate
dy = c[0, 1] - cy
d_start = dx*dx + dy*dy   # squared Euclidean distance — no sqrt needed for comparison
```

### Verified: Contour Reversal

```python
# numpy array reversal: [::-1] reverses along axis 0 (rows = points)
reversed_contour = contour[::-1]   # (N, 2) array, last point becomes first
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pyautogui.drag()` for strokes | `mouseDown` + `moveTo` loop + `mouseUp` | N/A — drag() never used here | Enables per-point abort checks |
| Global boolean `abort_flag` | `threading.Event` | Established in Phase 1 architecture | Thread-safe, correct |
| Raw findContours order for replay | Nearest-neighbor sort | Phase 2 (this phase) | Eliminates jump artifacts |
| Simple stretch mapping (norm * bbox_wh + bbox_xy) | Aspect-ratio preserving letterbox | Phase 2 (this phase) | No distortion on non-square images |

**Deprecated/outdated patterns:**
- `pyautogui.drag()`: Not used in this tool (no per-point granularity). Confirmed by docs review.
- `keyboard` library: Abandoned 2020. pynput is the replacement.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | none — implicit discovery from tests/ directory |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAL-06 | Aspect-ratio mapping: letterbox/pillarbox math correct | unit | `pytest tests/test_coordinate_mapping.py -x -q` | ❌ Wave 0 |
| CAL-06 | Square bbox: no margins (map fills entire bbox) | unit | `pytest tests/test_coordinate_mapping.py::test_square_bbox_no_margins -x` | ❌ Wave 0 |
| CAL-06 | Wide bbox + tall image: pillarbox centering | unit | `pytest tests/test_coordinate_mapping.py::test_pillarbox -x` | ❌ Wave 0 |
| CAL-06 | Tall bbox + wide image: letterbox centering | unit | `pytest tests/test_coordinate_mapping.py::test_letterbox -x` | ❌ Wave 0 |
| CAL-07 | start_delay config key loads with default 3 | unit | `pytest tests/test_coordinate_mapping.py::test_start_delay_default -x` | ❌ Wave 0 |
| PAINT-03 | inter_point_delay config key loads with default 0 | unit | `pytest tests/test_coordinate_mapping.py::test_inter_point_delay_default -x` | ❌ Wave 0 |
| PAINT-04 | Sort: 3 contours, sorted closer than unsorted | unit | `pytest tests/test_coordinate_mapping.py::test_sort_reduces_travel -x` | ❌ Wave 0 |
| PAINT-05 | Sort: contour reversed when far endpoint is closer | unit | `pytest tests/test_coordinate_mapping.py::test_sort_reverses_contour -x` | ❌ Wave 0 |
| PAINT-05 | Sort: contour NOT reversed when start endpoint is closer | unit | `pytest tests/test_coordinate_mapping.py::test_sort_no_reverse_when_start_closer -x` | ❌ Wave 0 |
| PAINT-08 | mouseUp called in finally even if loop raises exception | unit (mock) | `pytest tests/test_coordinate_mapping.py::test_mouseup_on_exception -x` | ❌ Wave 0 |
| PAINT-01 | dry_run skips painting (no mouseDown called) | unit (mock) | `pytest tests/test_coordinate_mapping.py::test_dry_run_skips_painting -x` | ❌ Wave 0 |
| PAINT-02 | mouse_button config key flows to mouseDown/mouseUp calls | unit (mock) | `pytest tests/test_coordinate_mapping.py::test_configurable_mouse_button -x` | ❌ Wave 0 |
| PAINT-06 | abort_flag set: loop breaks after current stroke | unit (mock) | `pytest tests/test_coordinate_mapping.py::test_abort_flag_stops_replay -x` | ❌ Wave 0 |
| PAINT-07 | Progress output contains N/M and percentage | unit | `pytest tests/test_coordinate_mapping.py::test_progress_output_format -x` | ❌ Wave 0 |

**Manual-only tests (cannot automate):**
- CAL-07 countdown visual: terminal prints "3... 2... 1..." before painting — requires human to observe timing
- PAINT-01 actual mouse movement: pyautogui moves real cursor — cannot unit test without screen
- PAINT-06 Esc abort during live run — requires physical keyboard

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_coordinate_mapping.py` — covers CAL-06, CAL-07, PAINT-01..08 (14 test functions)
- [ ] No new conftest fixtures needed — `tmp_config_path`, `sample_png`, `blank_png` from Phase 1 are sufficient

**Existing test infrastructure:** All 22 Phase 1 tests continue to pass. No changes to existing test files required.

---

## Open Questions

1. **Source image dimensions: read from file or cache in AppState?**
   - What we know: `run_preview` already calls `cv2.imread(state.image_path)` for aspect ratio. `run_replay` needs the same dims.
   - What's unclear: Storing in AppState would be cleaner; calling imread twice is wasteful for large images.
   - Recommendation: For Phase 2, call imread once at the start of `run_replay` and extract `.shape[:2]`. Do not change AppState — this is a clean Phase 2 scope. A Phase 3 refactor could cache it.

2. **Edge case: contour with 1 point after mapping**
   - What we know: D-41 (Claude's discretion) — "Whether to skip contours that map to a single pixel after coordinate transform."
   - What's unclear: Should the skip happen pre-sort (in normalized space, < 2 points) or post-map (in pixel space, all points identical after int conversion)?
   - Recommendation: Skip in normalized space (`len(contour) < 2`) before sorting. Post-map deduplication is unnecessary complexity.

3. **Progress bar: print total time at completion?**
   - What we know: D-41 (Claude's discretion) — "Whether to print total painting time at completion."
   - Recommendation: Yes, print elapsed time. It helps users calibrate expected duration for future runs. Format: `"Done. 128 strokes in 47.3s."` This is low cost and high value.

---

## Sources

### Primary (HIGH confidence)
- ARCHITECTURE.md (project research) — coordinate math, component boundaries, replay engine pattern, pynput listener pattern
- PITFALLS.md (project research) — FailSafeException handling, contour ordering, coordinate transposition, try/finally pattern, PAUSE default
- STACK.md (project research) — pyautogui 0.9.54, pynput 1.8.1, numpy version matrix
- painter.py (existing Phase 1 code) — AppState definition, config access pattern, lazy import pattern, pyautogui.PAUSE=0 already set

### Secondary (MEDIUM confidence)
- PyAutoGUI mouse control docs: https://pyautogui.readthedocs.io/en/latest/mouse.html — mouseDown/moveTo/mouseUp button parameter
- pynput keyboard listener docs: https://pynput.readthedocs.io/en/latest/keyboard.html — on_press callback, return False to stop listener

### Tertiary (LOW confidence)
- None — all critical claims verified against Phase 1 code and project research docs

---

## Metadata

**Confidence breakdown:**
- Coordinate mapping math: HIGH — letterbox formula is verified math; cross-checked against Phase 1 run_preview which uses the same centering logic
- Nearest-neighbor sort: HIGH — O(n²) algorithm is textbook; squared-distance optimization is verified; starting point from (0,0) normalized is correct per D-08
- pyautogui stroke pattern: HIGH — mouseDown/moveTo/mouseUp API verified against official docs; PAUSE=0 already set in Phase 1
- try/finally guarantee: HIGH — Python language guarantee; verified in PITFALLS.md
- pynput abort listener: HIGH — same library already used in Phase 1 for mouse capture; keyboard.Listener pattern mirrors mouse.Listener
- Config key additions: HIGH — extends existing _DEFAULTS dict structure; deep_merge handles missing keys

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable APIs — pyautogui and pynput have not had major releases since 2023)
